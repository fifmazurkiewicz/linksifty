import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import type { Session, SupabaseClient } from '@supabase/supabase-js'
import { supabase as configuredClient } from './supabase'
import { AuthContext } from './context'
import type { AuthValue } from './context'
import { AUTH_EXPIRED_EVENT } from '../lib/api'

export function AuthProvider({
  children,
  client = configuredClient,
}: {
  children: ReactNode
  client?: SupabaseClient | null
}) {
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(Boolean(client))
  const [error, setError] = useState<string | null>(null)
  const signingOut = useRef(false)

  const signInWithGoogle = useCallback(async () => {
    if (!client) {
      setError('Google sign-in is not configured yet.')
      return
    }
    try {
      const { error: authError } = await client.auth.signInWithOAuth({
        provider: 'google',
        options: { scopes: 'openid email profile', redirectTo: `${window.location.origin}/` },
      })
      if (authError) setError(authError.message)
    } catch {
      setError('Google sign-in could not be started. Please try again.')
    }
  }, [client])

  const signOut = useCallback(async () => {
    if (signingOut.current) return
    signingOut.current = true
    setSession(null)
    if (!client) return
    try {
      const { error: authError } = await client.auth.signOut()
      if (authError) setError(authError.message)
    } catch {
      setError('Sign out could not be completed. Please try again.')
    }
  }, [client])

  useEffect(() => {
    const expired = (event: Event) => {
      if ((event as CustomEvent<string>).detail === session?.user.id) void signOut()
    }
    window.addEventListener(AUTH_EXPIRED_EVENT, expired)
    return () => window.removeEventListener(AUTH_EXPIRED_EVENT, expired)
  }, [session, signOut])

  useEffect(() => {
    if (!client) return
    let active = true
    void client.auth.getSession().then(({ data, error: authError }) => {
      if (!active) return
      setSession(data.session)
      setError(authError?.message ?? null)
      setLoading(false)
    }).catch(() => {
      if (!active) return
      setError('Could not restore your sign-in session.')
      setLoading(false)
    })
    const { data } = client.auth.onAuthStateChange((_event, nextSession) => {
      if (nextSession) signingOut.current = false
      setSession(nextSession)
      setError(null)
      setLoading(false)
    })
    return () => {
      active = false
      data.subscription.unsubscribe()
    }
  }, [client])

  const value = useMemo<AuthValue>(() => ({
    client,
    session,
    loading,
    error,
    signInWithGoogle,
    signOut,
  }), [client, session, loading, error, signInWithGoogle, signOut])

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
