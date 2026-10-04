"""Bounded, in-memory context for anonymous browser sessions.

This module deliberately has no database, filesystem, or cache dependency.
Guest data disappears when a session is deleted, expires, or the backend
process stops.
"""

from __future__ import annotations

from collections import OrderedDict, deque
from dataclasses import dataclass, field
from secrets import compare_digest, token_urlsafe
from threading import RLock
from time import monotonic
from uuid import uuid4

from app.services.document_text import ExtractedDocument

GUEST_SESSION_TTL_SECONDS = 30 * 60
MAX_GUEST_SESSIONS = 16
MAX_TURNS = 32
MAX_TURN_CHARACTERS = 2_000
MAX_HISTORY_CHARACTERS = 24_000
MAX_DOCUMENT_REFERENCES = 3
MAX_AGENT_CONTEXT_CHARACTERS = 18_000


@dataclass(frozen=True)
class MemberProfile:
    """The minimum account data useful for personalized assistance.

    This intentionally omits street address and any authentication data.
    The values are stored only in the same short-lived, capability-protected
    session as the conversation.
    """

    full_name: str | None = None
    phone_number: str | None = None
    state: str | None = None
    district: str | None = None
    village_or_town: str | None = None
    address: str | None = None
    pincode: str | None = None
    caste_category: str | None = None
    user_type: str | None = None
    cooperative_role: str | None = None

    @classmethod
    def create(
        cls,
        *,
        full_name: object = None,
        phone_number: object = None,
        state: object = None,
        district: object = None,
        village_or_town: object = None,
        address: object = None,
        pincode: object = None,
        caste_category: object = None,
        user_type: object = None,
        cooperative_role: object = None,
    ) -> "MemberProfile":
        """Normalize profile strings before they enter model context."""

        return cls(
            full_name=_clean_profile_value(full_name, 120),
            phone_number=_clean_profile_value(phone_number, 20),
            state=_clean_profile_value(state, 100),
            district=_clean_profile_value(district, 120),
            village_or_town=_clean_profile_value(village_or_town, 120),
            address=_clean_profile_value(address, 500),
            pincode=_clean_profile_value(pincode, 10),
            caste_category=_clean_profile_value(caste_category, 32),
            user_type=_clean_profile_value(user_type, 48),
            cooperative_role=_clean_profile_value(cooperative_role, 120),
        )

    def render_context(self) -> str:
        """Render account fields as data, never as model instructions."""

        fields = (
            ("Name", self.full_name),
            ("Phone", self.phone_number),
            ("State", self.state),
            ("District", self.district),
            ("Village or town", self.village_or_town),
            ("Address", self.address),
            ("Pincode", self.pincode),
            ("Caste category", self.caste_category),
            ("Member type", self.user_type),
            ("Cooperative role", self.cooperative_role),
        )
        lines = [f"{label}: {value}" for label, value in fields if value]
        if not lines:
            return ""
        return "ACCOUNT PROFILE DATA START\n" + "\n".join(lines) + "\nACCOUNT PROFILE DATA END"


def _clean_profile_value(value: object, maximum: int) -> str | None:
    """Remove control characters and bound user-controlled profile data."""

    if not isinstance(value, str):
        return None
    normalized = " ".join(value.replace("\x00", " ").split()).strip()
    return normalized[:maximum] or None


class GuestSessionError(ValueError):
    """Raised when an anonymous session capability is invalid or expired."""


@dataclass(frozen=True)
class GuestTurn:
    """A small, finalized chat turn belonging to one guest session."""

    role: str
    text: str
    source: str


@dataclass(frozen=True)
class GuestSessionSnapshot:
    """A read-only copy used to create a model request outside the store lock."""

    session_id: str
    history: tuple[GuestTurn, ...]
    documents: tuple[ExtractedDocument, ...]
    member_profile: MemberProfile | None = None
    # This is never rendered into model context or returned to a browser. It
    # crosses only the capability-protected local worker boundary, where voice
    # tools apply the same account ownership checks as the HTTP APIs.
    account_id: int | None = None

    def render_context(self, *, max_characters: int) -> str:
        """Render recent history and useful document excerpts within a hard bound.

        Sending every extracted document on every speech turn would hurt voice
        latency.  Instead retain recent conversational turns and a balanced
        beginning/end excerpt from the newest references.  The full source is
        never written to disk and remains available to direct text chat only
        while the in-memory session is alive.
        """

        if max_characters <= 0:
            return ""

        sections: list[str] = []
        if self.member_profile is not None:
            profile_context = self.member_profile.render_context()
            if profile_context:
                sections.append(profile_context)
        history_budget = min(6_000, max_characters // 3)
        history_lines: deque[str] = deque()
        used_history = 0
        for turn in reversed(self.history):
            line = f"{turn.role.upper()} ({turn.source}): {turn.text}"
            if used_history and used_history + len(line) + 1 > history_budget:
                break
            if not history_lines and len(line) > history_budget:
                line = line[-history_budget:]
            history_lines.appendleft(line)
            used_history += len(line) + 1
        if history_lines:
            sections.append(
                "CONVERSATION HISTORY START\n"
                + "\n".join(history_lines)
                + "\nCONVERSATION HISTORY END"
            )

        used = len("\n\n".join(sections))
        remaining = max_characters - used
        document_parts: deque[str] = deque()
        for document in reversed(self.documents):
            # Leave enough room for labels and older documents; newest
            # references are more likely to answer the current question.
            allowance = min(7_000, max(0, remaining - 128))
            if allowance < 256:
                break
            text = self._document_excerpt(document.text, allowance)
            suffix = "\n[Document text was truncated.]" if document.truncated else ""
            part = f"DOCUMENT: {document.filename}\n{text}{suffix}"
            if len(part) > remaining:
                part = part[:remaining]
            document_parts.appendleft(part)
            remaining -= len(part) + 2
        if document_parts:
            sections.append(
                "REFERENCE DOCUMENTS START\n"
                + "\n\n".join(document_parts)
                + "\nREFERENCE DOCUMENTS END"
            )

        return "\n\n".join(sections)[:max_characters].strip()

    @staticmethod
    def _document_excerpt(text: str, limit: int) -> str:
        """Preserve both document introductions and conclusions when needed."""

        if len(text) <= limit:
            return text
        head_size = max(1, int(limit * 0.7))
        tail_size = max(1, limit - head_size)
        return f"{text[:head_size].rstrip()}\n[...excerpt shortened...]\n{text[-tail_size:].lstrip()}"


@dataclass
class _GuestSession:
    secret: str
    expires_at: float
    turns: deque[GuestTurn] = field(default_factory=deque)
    documents: deque[ExtractedDocument] = field(default_factory=deque)
    member_profile: MemberProfile | None = None
    account_id: int | None = None


class GuestSessionStore:
    """Thread-safe, non-persistent session capability store."""

    def __init__(self) -> None:
        self._sessions: OrderedDict[str, _GuestSession] = OrderedDict()
        self._lock = RLock()

    def create(self) -> tuple[str, str]:
        """Create a new random session identifier and unguessable capability."""

        with self._lock:
            self._purge_expired_locked()
            while len(self._sessions) >= MAX_GUEST_SESSIONS:
                self._sessions.popitem(last=False)
            session_id = str(uuid4())
            secret = token_urlsafe(32)
            self._sessions[session_id] = _GuestSession(
                secret=secret,
                expires_at=monotonic() + GUEST_SESSION_TTL_SECONDS,
            )
            return session_id, secret

    def snapshot(self, session_id: str, secret: str) -> GuestSessionSnapshot:
        """Return a safe copy of active context and extend its idle lifetime."""

        with self._lock:
            session = self._authorize_locked(session_id, secret)
            return GuestSessionSnapshot(
                session_id=session_id,
                history=tuple(session.turns),
                documents=tuple(session.documents),
                member_profile=session.member_profile,
                account_id=session.account_id,
            )

    def set_member_profile(
        self,
        session_id: str,
        secret: str,
        *,
        full_name: object = None,
        phone_number: object = None,
        state: object = None,
        district: object = None,
        village_or_town: object = None,
        address: object = None,
        pincode: object = None,
        caste_category: object = None,
        user_type: object = None,
        cooperative_role: object = None,
        account_id: object = None,
    ) -> None:
        """Attach server-verified account context to this ephemeral session.

        Callers must already have authenticated the account on the backend;
        the browser never supplies these values through LiveKit attributes.
        """

        profile = MemberProfile.create(
            full_name=full_name,
            phone_number=phone_number,
            state=state,
            district=district,
            village_or_town=village_or_town,
            address=address,
            pincode=pincode,
            caste_category=caste_category,
            user_type=user_type,
            cooperative_role=cooperative_role,
        )
        with self._lock:
            session = self._authorize_locked(session_id, secret)
            session.member_profile = profile
            # This comes only from a backend account lookup. Invalid values
            # are ignored instead of becoming a usable voice identity.
            session.account_id = account_id if isinstance(account_id, int) and account_id > 0 else None

    def append_turn(self, session_id: str, secret: str, *, role: str, text: str, source: str) -> None:
        """Store one bounded final turn, deduplicating immediate repeats."""

        cleaned = text.replace("\x00", "").strip()
        if not cleaned or role not in {"user", "assistant"} or source not in {"text", "voice"}:
            return
        cleaned = cleaned[:MAX_TURN_CHARACTERS]

        with self._lock:
            session = self._authorize_locked(session_id, secret)
            turn = GuestTurn(role=role, text=cleaned, source=source)
            if session.turns and session.turns[-1] == turn:
                return
            session.turns.append(turn)
            while len(session.turns) > MAX_TURNS or self._turn_characters(session.turns) > MAX_HISTORY_CHARACTERS:
                session.turns.popleft()

    def add_document(self, session_id: str, secret: str, document: ExtractedDocument) -> None:
        """Keep only a few extracted documents in current guest-session memory."""

        with self._lock:
            session = self._authorize_locked(session_id, secret)
            session.documents.append(document)
            while len(session.documents) > MAX_DOCUMENT_REFERENCES:
                session.documents.popleft()

    def delete(self, session_id: str, secret: str) -> None:
        """Immediately forget the authenticated session and its references."""

        with self._lock:
            self._authorize_locked(session_id, secret)
            self._sessions.pop(session_id, None)

    def _authorize_locked(self, session_id: str, secret: str) -> _GuestSession:
        self._purge_expired_locked()
        session = self._sessions.get(session_id)
        if session is None or not secret or not compare_digest(session.secret, secret):
            raise GuestSessionError("Guest session is invalid or has expired.")
        session.expires_at = monotonic() + GUEST_SESSION_TTL_SECONDS
        self._sessions.move_to_end(session_id)
        return session

    def _purge_expired_locked(self) -> None:
        now = monotonic()
        for session_id in [
            candidate_id
            for candidate_id, candidate in self._sessions.items()
            if candidate.expires_at <= now
        ]:
            self._sessions.pop(session_id, None)

    @staticmethod
    def _turn_characters(turns: deque[GuestTurn]) -> int:
        return sum(len(turn.text) for turn in turns)


guest_sessions = GuestSessionStore()
