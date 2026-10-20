import { describe, expect, it } from 'vitest'

import {
  MAX_ACTIONS_PER_MINUTE,
  createUiActionTracker,
} from './track-ui-action'
import { UI_ACTION_CODE } from './ui-event-codes'
import { createTelemetryQueue } from './telemetry-queue'

function setup() {
  let t = 1_000_000
  let route = '/a'
  const out: Array<[number, string]> = []
  const track = createUiActionTracker({
    now: () => t,
    getRoute: () => route,
    enqueue: (a, r) => out.push([a, r]),
  })
  return { track, out, advance: (ms: number) => (t += ms), setRoute: (r: string) => (route = r) }
}

describe('trackUiAction (duoc-CR-654)', () => {
  it('bỏ trùng cùng mã+route trong 2 giây, cho qua sau đó', () => {
    const { track, out, advance } = setup()
    track(UI_ACTION_CODE.REFRESH)
    advance(1_000)
    track(UI_ACTION_CODE.REFRESH)
    expect(out).toHaveLength(1)
    advance(1_500)
    track(UI_ACTION_CODE.REFRESH)
    expect(out).toHaveLength(2)
  })

  it('mã khác hoặc route khác không bị coi là trùng', () => {
    const { track, out, setRoute } = setup()
    track(UI_ACTION_CODE.REFRESH)
    track(UI_ACTION_CODE.PRINT)
    setRoute('/b')
    track(UI_ACTION_CODE.REFRESH)
    expect(out.map(([a, r]) => `${a}${r}`)).toEqual([`${UI_ACTION_CODE.REFRESH}/a`, `${UI_ACTION_CODE.PRINT}/a`, `${UI_ACTION_CODE.REFRESH}/b`])
  })

  it('mã lắm lời gộp cửa sổ 10 giây', () => {
    const { track, out, advance } = setup()
    track(UI_ACTION_CODE.SORT_CHANGE)
    advance(5_000)
    track(UI_ACTION_CODE.SORT_CHANGE)
    expect(out).toHaveLength(1)
    advance(5_500)
    track(UI_ACTION_CODE.SORT_CHANGE)
    expect(out).toHaveLength(2)
  })

  it('trần 30/phút cắt đúng và mở lại sau 1 phút', () => {
    let t = 0
    let n = 0
    const out: number[] = []
    const track = createUiActionTracker({ now: () => t, getRoute: () => `/r${n++}`, enqueue: (a) => out.push(a) })
    for (let i = 0; i < 50; i++) track(UI_ACTION_CODE.REFRESH)
    expect(out).toHaveLength(MAX_ACTIONS_PER_MINUTE)
    t += 61_000
    track(UI_ACTION_CODE.REFRESH)
    expect(out).toHaveLength(MAX_ACTIONS_PER_MINUTE + 1)
  })
})

describe('UI_ACTION wire', () => {
  it('thân gửi chỉ có khóa số/route cố định, không chuỗi tự do', async () => {
    const bodies: string[] = []
    const q = createTelemetryQueue({
      fetchImpl: (async (_u: unknown, init: RequestInit) => {
        bodies.push(String(init.body))
        return new Response('{"data":{"accepted":1}}', { status: 200 })
      }) as typeof fetch,
      now: () => 10,
      getToken: () => 'x',
      url: '/u',
      tabKey: 1,
    })
    q.setEnabled(true)
    q.enqueue({ type: 8 as never, route: '/a', action: UI_ACTION_CODE.PRINT })
    await q.flush()
    const ev = JSON.parse(bodies[0]).events[0]
    expect(ev.action).toBe(UI_ACTION_CODE.PRINT)
    expect(Object.keys(ev).sort()).toEqual(
      ['action', 'age_ms', 'duration_ms', 'error', 'form', 'result_count', 'route', 'tab_key', 'type'],
    )
    expect(ev.error).toBeNull()
    q.setEnabled(false)
  })
})
