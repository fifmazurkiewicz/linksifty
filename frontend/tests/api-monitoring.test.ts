import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Session } from '@supabase/supabase-js'
import * as Sentry from '@sentry/react'
import { api, ApiError, watchActivity } from '../src/lib/api'
import { monitoringOptions } from '../src/lib/monitoring-options'

type Envelope = [unknown, Array<[{ type: string }, unknown]>]
const PRIVATE = 'SYNTHETIC-PRIVATE: article text auth-token email@example.test'
const session = { access_token: PRIVATE, user: { id: 'synthetic-user' } } as Session
let envelopes: Envelope[]

beforeEach(() => {
  envelopes = []
  Sentry.init({ ...monitoringOptions('linksifty-web', {
    enabled: 'true', dsn: 'https://0123456789abcdef0123456789abcdef@o1.ingest.de.sentry.io/123', environment: 'test',
  }), transport: () => ({
    send: envelope => { envelopes.push(envelope); return Promise.resolve({ statusCode: 200 }) },
    flush: () => Promise.resolve(true),
  }) })
  Sentry.setUser({ email: PRIVATE })
  Sentry.setExtra('private', PRIVATE)
})
afterEach(async () => { await Sentry.close(100); vi.restoreAllMocks() })

const request = () => api('/v1/items', session)
const activity = () => watchActivity(session, new AbortController().signal, () => {})

describe.each([['request', request], ['activity', activity]] as const)('%s delivery', (_name, run) => {
  it('reports a caught server failure once without transmitting private data', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: PRIVATE }), { status: 503 }))
    await expect(run()).rejects.toMatchObject({ status: 503 })
    await Sentry.flush(100)
    expect(envelopes).toHaveLength(1)
    expect(envelopes[0][1].map(([header]) => header.type)).toEqual(['event'])
    expect(JSON.stringify(envelopes)).not.toContain(PRIVATE)
  })

  it.each([401, 403, 409, 422])('keeps expected HTTP%s outcomes silent', async status => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ detail: PRIVATE }), { status }))
    await expect(run()).rejects.toBeInstanceOf(ApiError)
    await Sentry.flush(100)
    expect(envelopes).toEqual([])
  })

  it('reports a network failure while preserving the original error', async () => {
    const original = new TypeError(PRIVATE)
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(original)
    await expect(run()).rejects.toBe(original)
    await Sentry.flush(100)
    expect(envelopes).toHaveLength(1)
    expect(JSON.stringify(envelopes)).not.toContain(PRIVATE)
  })

  it('does not report normal cancellation', async () => {
    const original = new DOMException(PRIVATE, 'AbortError')
    vi.spyOn(globalThis, 'fetch').mockRejectedValue(original)
    await expect(run()).rejects.toBe(original)
    await Sentry.flush(100)
    expect(envelopes).toEqual([])
  })
})

it('reports malformed progress data while preserving stream cleanup', async () => {
  const cancelled = vi.fn()
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(new ReadableStream({
    start(controller) { controller.enqueue(new TextEncoder().encode('event: snapshot\ndata: invalid-json\n\n')) },
    cancel: cancelled,
  }), { headers: { 'Content-Type': 'text/event-stream' } }))
  await expect(activity()).rejects.toBeInstanceOf(SyntaxError)
  await Sentry.flush(100)
  expect(envelopes).toHaveLength(1)
  expect(cancelled).toHaveBeenCalledOnce()
})

it('keeps a stream access-denial event silent', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('event: denied\ndata: {}\n\n', {
    headers: { 'Content-Type': 'text/event-stream' },
  }))
  await expect(activity()).rejects.toMatchObject({ status: 403 })
  await Sentry.flush(100)
  expect(envelopes).toEqual([])
})

it('keeps successful results unchanged and silent', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({ items: [] })))
  await expect(request()).resolves.toEqual({ items: [] })
  await Sentry.flush(100)
  expect(envelopes).toEqual([])
})

it('keeps the original failure even when monitoring itself throws', async () => {
  const original = new TypeError(PRIVATE)
  vi.spyOn(globalThis, 'fetch').mockRejectedValue(original)
  vi.spyOn(Sentry.getClient()!, 'captureException').mockImplementation(() => { throw new Error('monitoring unavailable') })
  await expect(request()).rejects.toBe(original)
})

it('reports malformed API JSON instead of losing its asynchronous parsing failure', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('invalid-json'))
  await expect(request()).rejects.toBeInstanceOf(SyntaxError)
  await Sentry.flush(100)
  expect(envelopes).toHaveLength(1)
})
