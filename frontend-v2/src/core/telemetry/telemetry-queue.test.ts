import { describe, expect, it, vi } from 'vitest'

import { createTelemetryQueue, MAX_KEEPALIVE_TOTAL_BYTES, MAX_QUEUE, type UiEventInput } from './telemetry-queue'
import { UI_EVENT } from './ui-event-codes'

const view = (route = '/a'): UiEventInput => ({ type: UI_EVENT.PAGE_VIEW, route })

function setup(status = 200, body: unknown = { data: { accepted: 1 } }) {
  let now = 1_000
  const fetchImpl = vi.fn(async () => ({
    status,
    ok: status >= 200 && status < 300,
    json: async () => body,
  })) as unknown as typeof fetch & ReturnType<typeof vi.fn>
  const token = { value: 'tok' as string | null }
  const queue = createTelemetryQueue({
    fetchImpl,
    now: () => now,
    getToken: () => token.value,
    url: '/api/telemetry/ui-events',
    tabKey: 7,
  })
  return { queue, fetchImpl: fetchImpl as unknown as ReturnType<typeof vi.fn>, token, advance: (ms: number) => (now += ms) }
}

const sentEvents = (fetchImpl: ReturnType<typeof vi.fn>) =>
  fetchImpl.mock.calls.map((c) => JSON.parse((c[1] as RequestInit).body as string).events as unknown[])

describe('telemetry queue', () => {
  it('does nothing while disabled', async () => {
    const { queue, fetchImpl } = setup()
    queue.enqueue(view())
    await queue.flush()
    expect(fetchImpl).not.toHaveBeenCalled()
    expect(queue.size()).toBe(0)
  })

  it('splits 250 events into batches of at most 100', async () => {
    const { queue, fetchImpl } = setup()
    queue.setEnabled(true)
    for (let i = 0; i < 250; i++) queue.enqueue(view())
    await queue.flush()
    expect(sentEvents(fetchImpl).map((b) => b.length)).toEqual([100, 100, 50])
    queue.setEnabled(false)
  })

  it('splits by payload size so no body exceeds 60 KB', async () => {
    const { queue, fetchImpl } = setup()
    queue.setEnabled(true)
    const big = 'x'.repeat(200)
    for (let i = 0; i < 99; i++) {
      queue.enqueue({ type: UI_EVENT.CLIENT_ERROR, route: '/a', error: { name: 'E', message: big.repeat(100) } })
    }
    await queue.flush()
    expect(fetchImpl.mock.calls.length).toBeGreaterThan(1)
    for (const call of fetchImpl.mock.calls) {
      expect(new TextEncoder().encode((call[1] as RequestInit).body as string).length).toBeLessThanOrEqual(60 * 1024)
    }
    queue.setEnabled(false)
  })

  it('on keepalive with two near-full batches sends the first only', async () => {
    const { queue, fetchImpl } = setup()
    queue.setEnabled(true)
    // 100 sự kiện lỗi mỗi cái ~330 byte JSON không đủ 60 KB; dùng trần số sự kiện để có 2 lô đầy theo SỐ LƯỢNG
    // rồi kiểm tổng byte: hai lô 100 sự kiện lỗi dài 200 ký tự ≈ 2 × 36 KB = 72 KB > 60 KB.
    const message = 'y'.repeat(200)
    for (let i = 0; i < 200; i++) {
      queue.enqueue({ type: UI_EVENT.CLIENT_ERROR, route: '/a', error: { name: 'E', message } })
    }
    await queue.flush(true)
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    const body = (fetchImpl.mock.calls[0][1] as RequestInit).body as string
    expect(new TextEncoder().encode(body).length).toBeLessThanOrEqual(MAX_KEEPALIVE_TOTAL_BYTES)
    // Lô thứ hai không vừa trần keepalive chung: còn nguyên trong bộ đệm, không bắn để khỏi bị trình duyệt từ chối.
    expect(queue.size()).toBeGreaterThan(0)
    queue.setEnabled(false)
  })

  it('keeps the batch on 401 and resends it on the next flush', async () => {
    const { queue, fetchImpl } = setup(401)
    queue.setEnabled(true)
    queue.enqueue(view('/keep'))
    await queue.flush()
    expect(queue.size()).toBe(1)
    fetchImpl.mockResolvedValueOnce({ status: 200, ok: true, json: async () => ({ data: { accepted: 1 } }) })
    await queue.flush()
    expect(queue.size()).toBe(0)
    queue.setEnabled(false)
  })

  it.each([500, 413, 422])('drops the batch silently on %i', async (status) => {
    const { queue } = setup(status)
    queue.setEnabled(true)
    queue.enqueue(view())
    await expect(queue.flush()).resolves.toBeUndefined()
    expect(queue.size()).toBe(0)
    queue.setEnabled(false)
  })

  it('drops the batch and never throws on a network error', async () => {
    const { queue, fetchImpl } = setup()
    fetchImpl.mockRejectedValue(new TypeError('Failed to fetch'))
    queue.setEnabled(true)
    queue.enqueue(view())
    await expect(queue.flush()).resolves.toBeUndefined()
    expect(queue.size()).toBe(0)
    queue.setEnabled(false)
  })

  it('stops sending after the server answers 204 (collection switched off)', async () => {
    const { queue, fetchImpl } = setup(204)
    queue.setEnabled(true)
    queue.enqueue(view())
    await queue.flush()
    queue.enqueue(view())
    await queue.flush()
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    expect(queue.size()).toBe(0)
    queue.setEnabled(false)
  })

  it('stops sending when the server accepts 0 events', async () => {
    const { queue, fetchImpl } = setup(200, { data: { accepted: 0 } })
    queue.setEnabled(true)
    queue.enqueue(view())
    await queue.flush()
    queue.enqueue(view())
    await queue.flush()
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    queue.setEnabled(false)
  })

  it('keeps only the newest 300 events when the buffer overflows', () => {
    const { queue } = setup()
    queue.setEnabled(true)
    for (let i = 0; i < 350; i++) queue.enqueue(view(`/r${i}`))
    expect(queue.size()).toBe(MAX_QUEUE)
    queue.setEnabled(false)
  })

  it('on pagehide runs hooks then flushes with keepalive and a Bearer header', async () => {
    const { queue, fetchImpl } = setup()
    queue.setEnabled(true)
    queue.onPageHide(() => queue.enqueue({ type: UI_EVENT.PAGE_LEAVE, route: '/a', duration_ms: 5 }))
    queue.handlePageHide()
    await Promise.resolve()
    expect(fetchImpl).toHaveBeenCalledTimes(1)
    const init = fetchImpl.mock.calls[0][1] as RequestInit
    expect(init.keepalive).toBe(true)
    expect((init.headers as Record<string, string>).Authorization).toBe('Bearer tok')
    expect(sentEvents(fetchImpl)[0]).toHaveLength(1)
    queue.setEnabled(false)
  })

  it('keeps events while logged out and never sends without a token', async () => {
    const { queue, fetchImpl, token } = setup()
    token.value = null
    queue.setEnabled(true)
    queue.enqueue(view())
    await queue.flush()
    expect(fetchImpl).not.toHaveBeenCalled()
    expect(queue.size()).toBe(1)
    queue.setEnabled(false)
  })

  it('sends age_ms (time since enqueue), never a client clock or user id', async () => {
    const { queue, fetchImpl, advance } = setup()
    queue.setEnabled(true)
    queue.enqueue(view())
    advance(1_200)
    await queue.flush()
    const [event] = sentEvents(fetchImpl)[0] as Record<string, unknown>[]
    expect(event.age_ms).toBe(1_200)
    expect(Object.keys(event).sort()).toEqual(
      ['age_ms', 'duration_ms', 'error', 'form', 'result_count', 'route', 'tab_key', 'type'].sort(),
    )
    queue.setEnabled(false)
  })

  it('keeps age_ms up to 24 hours so a batch held overnight lands on the right day', async () => {
    const { queue, fetchImpl, advance } = setup()
    queue.setEnabled(true)
    queue.enqueue(view())
    advance(8 * 3_600_000)
    await queue.flush()
    expect((sentEvents(fetchImpl)[0][0] as { age_ms: number }).age_ms).toBe(8 * 3_600_000)
    queue.enqueue(view())
    advance(3 * 86_400_000)
    await queue.flush()
    expect((sentEvents(fetchImpl)[1][0] as { age_ms: number }).age_ms).toBe(86_400_000)
    queue.setEnabled(false)
  })

  // Bug M5 (CR-641 review): flush keepalive xóa cờ inFlight của lần gửi thường đang bay → nhịp kế tiếp chạy chồng.
  it('a finished keepalive flush does not release the in-flight guard of a pending regular flush', async () => {
    let releaseFirst: () => void = () => {}
    const fetchImpl = vi
      .fn()
      .mockImplementationOnce(
        () => new Promise((resolve) => (releaseFirst = () => resolve({ status: 200, ok: true, json: async () => ({ data: { accepted: 1 } }) }))),
      )
      .mockResolvedValue({ status: 200, ok: true, json: async () => ({ data: { accepted: 1 } }) })
    const queue = createTelemetryQueue({
      fetchImpl: fetchImpl as unknown as typeof fetch,
      now: () => 1_000,
      getToken: () => 'tok',
      url: '/api/telemetry/ui-events',
      tabKey: 7,
    })
    queue.setEnabled(true)
    queue.enqueue(view())
    const regular = queue.flush() // đang bay, chưa trả lời
    queue.enqueue(view())
    await queue.flush(true) // keepalive xong trước
    expect(fetchImpl).toHaveBeenCalledTimes(2)

    queue.enqueue(view())
    await queue.flush() // vẫn phải bị chặn vì lần gửi thường đầu tiên chưa xong
    expect(fetchImpl).toHaveBeenCalledTimes(2)

    releaseFirst()
    await regular
    await queue.flush() // hết bay thì gửi được
    expect(fetchImpl).toHaveBeenCalledTimes(3)
    queue.setEnabled(false)
  })

  it('clears the buffer when switched off', () => {
    const { queue } = setup()
    queue.setEnabled(true)
    queue.enqueue(view())
    queue.setEnabled(false)
    expect(queue.size()).toBe(0)
  })
})
