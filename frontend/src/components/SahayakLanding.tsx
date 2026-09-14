import { ArrowRight, FileText, Landmark, Leaf, LockKeyhole, Mic, Scale, ShieldAlert, WalletCards } from 'lucide-react'

type SahayakLandingProps = {
  onOpenAuth: () => void
  onTalk: () => void
  onViewServices: () => void
}

const TOPICS = [
  { icon: Landmark, title: 'Cooperative guidance', text: 'Understand member services, meetings, by-laws and everyday cooperative questions.' },
  { icon: Leaf, title: 'PACS & farm support', text: 'Find a simple place to begin your PACS and agriculture support questions.' },
  { icon: ShieldAlert, title: 'Crop insurance', text: 'Ask clear questions about PMFBY and the documents you may need.' },
  { icon: WalletCards, title: 'Financial literacy', text: 'Build confidence around savings, credit and digital payments.' },
  { icon: Scale, title: 'Grievance support', text: 'Prepare a clear, respectful request for help and its supporting documents.' },
]

export function SahayakLanding({ onOpenAuth, onTalk, onViewServices }: SahayakLandingProps) {
  return (
    <main className="discover-page">
      <section className="discover-hero">
        <div className="discover-hero__content">
          <p className="section-kicker">Multilingual cooperative assistance</p>
          <h1>Your guide to cooperative services, schemes and support.</h1>
          <p>Ask in the language you are most comfortable with. Sahayak AI brings voice-first guidance closer to cooperative members, farmers and rural communities.</p>
          <div className="hero-actions">
            <button className="primary-action" onClick={onTalk} type="button"><Mic size={18} /> Talk to Sahayak</button>
            <button className="secondary-action" onClick={onOpenAuth} type="button">Sign in</button>
          </div>
          <p className="hero-disclaimer">Educational guidance only. Always verify important legal, scheme and insurance details with official sources.</p>
        </div>
        <aside className="voice-preview" aria-label="Voice assistant preview">
          <div className="voice-preview__orbit voice-preview__orbit--outer" />
          <div className="voice-preview__orbit voice-preview__orbit--inner" />
          <div className="voice-preview__core"><Mic size={30} /></div>
          <div className="voice-preview__caption"><span className="status-dot" /> Ready to listen</div>
          <button onClick={onTalk} type="button">Ask a question <ArrowRight size={16} /></button>
        </aside>
      </section>

      <section className="trust-strip" aria-label="Sahayak AI benefits">
        <span>Voice & text support</span><i /><span>10 Indian languages</span><i /><span>Simple, private and accessible</span>
      </section>

      <section className="topic-section" aria-labelledby="topics-heading">
        <div className="section-heading">
          <div><p className="section-kicker">Explore support</p><h2 id="topics-heading">Start with what matters today.</h2></div>
          <button className="link-action" onClick={onTalk} type="button">Ask Sahayak <ArrowRight size={16} /></button>
        </div>
        <div className="topic-grid">
          {TOPICS.map(({ icon: Icon, title, text }) => (
            <button className="topic-card" key={title} onClick={onTalk} type="button">
              <span className="topic-card__icon"><Icon size={22} /></span><h3>{title}</h3><p>{text}</p><span>Ask Sahayak <ArrowRight size={15} /></span>
            </button>
          ))}
        </div>
      </section>

      <section className="account-prompt">
        <div><p className="section-kicker">Your private space</p><h2>Keep your important support in one place.</h2><p>Sign in to access your documents, notifications, personalised service space and profile.</p></div>
        <div className="locked-service-list">
          <span><LockKeyhole size={15} /> Documents</span><span><LockKeyhole size={15} /> Notifications</span><span><LockKeyhole size={15} /> My profile</span>
        </div>
        <button className="secondary-action" onClick={onViewServices} type="button"><FileText size={17} /> Explore services</button>
      </section>
    </main>
  )
}
