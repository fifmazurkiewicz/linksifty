import { createContext } from 'react'
import type { Session, SupabaseClient } from '@supabase/supabase-js'

export type AuthValue = {
  client: SupabaseClient | null
  session: Session | null
  loading: boolean
  error: string | null
  signInWithGoogle: () => Promise<void>
  signOut: () => Promise<void>
}

export const AuthContext = createContext<AuthValue | null>(null)
