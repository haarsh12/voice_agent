import { LockKeyhole, Mic } from 'lucide-react'

type AccessGateProps = { onOpenAuth: () => void; onTalk: () => void; title: string }

export function AccessGate({ onOpenAuth, onTalk, title }: AccessGateProps) {
  return (
    <main className="access-gate">
      <span className="access-gate__icon"><LockKeyhole size={28} /></span>
      <p className="section-kicker">Login to access</p>
      <h1>{title} is part of your private Sahayak space.</h1>
      <p>Sign in with your mobile number to continue. You can still ask Sahayak AI a public question as a guest.</p>
      <div><button className="primary-action" onClick={onOpenAuth} type="button">Sign in to access</button><button className="secondary-action" onClick={onTalk} type="button"><Mic size={17} /> Continue as guest</button></div>
    </main>
  )
}
