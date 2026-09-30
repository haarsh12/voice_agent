/** Browser-side WebAuthn conversion only; biometric data never enters this app. */

export type ServerWebAuthnOptions = Record<string, unknown>

export type WebAuthnCredentialJSON = {
  id: string
  rawId: string
  type: 'public-key'
  response: Record<string, unknown>
  clientExtensionResults: Record<string, unknown>
  authenticatorAttachment: 'platform' | 'cross-platform' | null
}

function fromBase64Url(value: string): Uint8Array<ArrayBuffer> {
  const padded = value.replace(/-/g, '+').replace(/_/g, '/') + '='.repeat((4 - value.length % 4) % 4)
  const binary = window.atob(padded)
  return Uint8Array.from(binary, (character) => character.charCodeAt(0))
}

function toBase64Url(value: ArrayBuffer): string {
  const bytes = new Uint8Array(value)
  let binary = ''
  for (const byte of bytes) binary += String.fromCharCode(byte)
  return window.btoa(binary).replace(/\+/g, '-').replace(/\//g, '_').replace(/=+$/g, '')
}

function creationOptions(options: ServerWebAuthnOptions): PublicKeyCredentialCreationOptions {
  const source = options as {
    challenge: string
    user: { id: string; name: string; displayName: string }
    excludeCredentials?: Array<{ id: string; [key: string]: unknown }>
  }
  const converted = {
    ...options,
    challenge: fromBase64Url(source.challenge),
    user: { ...source.user, id: fromBase64Url(source.user.id) },
    excludeCredentials: source.excludeCredentials?.map((credential) => ({
      ...credential,
      id: fromBase64Url(credential.id),
    })),
  }
  // The server validates and creates this WebAuthn dictionary. At this browser
  // boundary its JSON fields are intentionally decoded into Web API buffers.
  return converted as unknown as PublicKeyCredentialCreationOptions
}

function requestOptions(options: ServerWebAuthnOptions): PublicKeyCredentialRequestOptions {
  const source = options as {
    challenge: string
    allowCredentials?: Array<{ id: string; [key: string]: unknown }>
  }
  return {
    ...options,
    challenge: fromBase64Url(source.challenge),
    allowCredentials: source.allowCredentials?.map((credential) => ({
      ...credential,
      id: fromBase64Url(credential.id),
    })),
  } as PublicKeyCredentialRequestOptions
}

function serializeCredential(credential: PublicKeyCredential): WebAuthnCredentialJSON {
  const response = credential.response
  const common = {
    id: credential.id,
    rawId: toBase64Url(credential.rawId),
    type: 'public-key' as const,
    clientExtensionResults: {},
    authenticatorAttachment: supportedAuthenticatorAttachment(credential.authenticatorAttachment),
  }
  if (response instanceof AuthenticatorAttestationResponse) {
    return {
      ...common,
      response: {
        clientDataJSON: toBase64Url(response.clientDataJSON),
        attestationObject: toBase64Url(response.attestationObject),
        transports: response.getTransports?.() ?? [],
      },
    }
  }
  if (response instanceof AuthenticatorAssertionResponse) {
    return {
      ...common,
      response: {
        clientDataJSON: toBase64Url(response.clientDataJSON),
        authenticatorData: toBase64Url(response.authenticatorData),
        signature: toBase64Url(response.signature),
        userHandle: response.userHandle ? toBase64Url(response.userHandle) : null,
      },
    }
  }
  throw new Error('This browser returned an unsupported device credential.')
}

function supportedAuthenticatorAttachment(value: string | null): WebAuthnCredentialJSON['authenticatorAttachment'] {
  return value === 'platform' || value === 'cross-platform' ? value : null
}

export function supportsDeviceBiometrics(): boolean {
  return window.isSecureContext && typeof window.PublicKeyCredential !== 'undefined'
}

export async function createDeviceCredential(options: ServerWebAuthnOptions): Promise<WebAuthnCredentialJSON> {
  if (!supportsDeviceBiometrics()) {
    throw new Error('Face ID needs a current browser on a secure connection (HTTPS).')
  }
  const credential = await navigator.credentials.create({ publicKey: creationOptions(options) })
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Face ID setup was not completed.')
  return serializeCredential(credential)
}

export async function requestDeviceCredential(options: ServerWebAuthnOptions): Promise<WebAuthnCredentialJSON> {
  if (!supportsDeviceBiometrics()) {
    throw new Error('Face ID needs a current browser on a secure connection (HTTPS).')
  }
  const credential = await navigator.credentials.get({ publicKey: requestOptions(options) })
  if (!(credential instanceof PublicKeyCredential)) throw new Error('Face ID sign-in was not completed.')
  return serializeCredential(credential)
}

export function biometricErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof DOMException && error.name === 'NotAllowedError') {
    return 'Face ID was cancelled or not approved. You can try again or use mobile OTP.'
  }
  if (error instanceof DOMException && error.name === 'NotSupportedError') {
    return 'This device does not support Face ID or device biometrics. Use mobile OTP instead.'
  }
  return error instanceof Error ? error.message : fallback
}
