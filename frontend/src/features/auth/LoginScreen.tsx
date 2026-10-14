import { useAuth } from '../../auth/useAuth'

export function LoginScreen() {
  const { signInWithGoogle, loading, error, client } = useAuth()
  return <main className="auth-screen">
    <section className="auth-card" aria-labelledby="login-title">
      <p className="eyebrow">LINKSIFTY</p>
      <h1 id="login-title">Make room for what matters.</h1>
      <p>Sign in to save links and get evidence-backed assessments.</p>
      <button className="primary google-button" onClick={() => void signInWithGoogle()} disabled={loading || !client}>
        Continue with Google
      </button>
      {!client && <p className="hint">Sign-in is waiting for Supabase settings.</p>}
      {error && <p className="error" role="alert">{error}</p>}
    </section>
  </main>
}
