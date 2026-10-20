import { renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { telemetry } from './telemetry-queue'
import { UI_EVENT, UI_FORM_CODE } from './ui-event-codes'
import { useFormTelemetry } from './use-form-telemetry'
import { useSearchTelemetry } from './use-search-telemetry'

afterEach(() => vi.restoreAllMocks())

const typesOf = (spy: ReturnType<typeof vi.spyOn>) =>
  spy.mock.calls.map((c: unknown[]) => (c[0] as { type: number }).type)

describe('useFormTelemetry', () => {
  it('open then submit emits no ABANDON afterwards', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { result, unmount } = renderHook(() => useFormTelemetry(UI_FORM_CODE.PURCHASE_ORDER, true))
    result.current.markSubmitted()
    unmount()
    expect(typesOf(spy)).toEqual([UI_EVENT.FORM_OPEN, UI_EVENT.FORM_SUBMIT])
  })

  it('open then unmount emits ABANDON with a duration', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { unmount } = renderHook(() => useFormTelemetry(UI_FORM_CODE.LEAVE_REQUEST, true))
    unmount()
    expect(typesOf(spy)).toEqual([UI_EVENT.FORM_OPEN, UI_EVENT.FORM_ABANDON])
    const abandon = spy.mock.calls[1][0] as { duration_ms: number; form: number }
    expect(abandon.duration_ms).toBeGreaterThanOrEqual(0)
    expect(abandon.form).toBe(UI_FORM_CODE.LEAVE_REQUEST)
  })

  it('stays silent when inactive, even if markSubmitted is called', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { result, unmount } = renderHook(() => useFormTelemetry(UI_FORM_CODE.EMPLOYEE_PROFILE, false))
    result.current.markSubmitted()
    unmount()
    expect(spy).not.toHaveBeenCalled()
  })

  it('a dialog reopened after a submit starts a fresh cycle', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { result, rerender, unmount } = renderHook(({ on }) => useFormTelemetry(UI_FORM_CODE.EMPLOYEE_PROFILE, on), {
      initialProps: { on: true },
    })
    result.current.markSubmitted()
    rerender({ on: false })
    rerender({ on: true })
    unmount()
    expect(typesOf(spy)).toEqual([
      UI_EVENT.FORM_OPEN,
      UI_EVENT.FORM_SUBMIT,
      UI_EVENT.FORM_OPEN,
      UI_EVENT.FORM_ABANDON,
    ])
  })
})

describe('useSearchTelemetry', () => {
  const run = (q: string, total: number | undefined, fetching = false) =>
    renderHook((p) => useSearchTelemetry(p.q, p.total, p.fetching), { initialProps: { q, total, fetching } })

  it('stays silent for an empty query', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    run('', 5)
    run('   ', 5)
    expect(spy).not.toHaveBeenCalled()
  })

  it('reports once per query with only the result count, and 0 is kept', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { rerender } = run('nguyen van a', 0)
    rerender({ q: 'nguyen van a', total: 0, fetching: false })
    rerender({ q: 'nguyen van a', total: 0, fetching: false })
    expect(spy).toHaveBeenCalledTimes(1)
    const event = spy.mock.calls[0][0]
    expect(event).toMatchObject({ type: UI_EVENT.SEARCH, result_count: 0 })
    // Từ khóa không bao giờ rời hook: không nằm ở bất cứ trường nào của sự kiện.
    expect(JSON.stringify(spy.mock.calls)).not.toContain('nguyen')
  })

  it('waits for the new result while fetching and ignores undefined totals', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { rerender } = run('abc', undefined)
    rerender({ q: 'abc', total: 3, fetching: true })
    expect(spy).not.toHaveBeenCalled()
    rerender({ q: 'abc', total: 3, fetching: false })
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('reports again when the query changes', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { rerender } = run('abc', 3)
    rerender({ q: 'abcd', total: 1, fetching: false })
    expect(spy).toHaveBeenCalledTimes(2)
  })
})

describe('useFormTelemetry — 7 biểu mẫu thêm (duoc-CR-654)', () => {
  const forms = [
    ['PAYMENT_REQUEST', UI_FORM_CODE.PAYMENT_REQUEST],
    ['GOODS_RECEIPT', UI_FORM_CODE.GOODS_RECEIPT],
    ['DOCUMENT', UI_FORM_CODE.DOCUMENT],
    ['VEHICLE_BOOKING', UI_FORM_CODE.VEHICLE_BOOKING],
    ['SEAL_REQUEST', UI_FORM_CODE.SEAL_REQUEST],
    ['ROOM_BOOKING', UI_FORM_CODE.ROOM_BOOKING],
    ['WORK_TASK', UI_FORM_CODE.WORK_TASK],
  ] as const

  it.each(forms)('%s: mở rồi lưu = OPEN+SUBMIT mang đúng mã form', (_name, code) => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    const { result, unmount } = renderHook(() => useFormTelemetry(code, true))
    result.current.markSubmitted()
    unmount()
    expect(typesOf(spy)).toEqual([UI_EVENT.FORM_OPEN, UI_EVENT.FORM_SUBMIT])
    expect(spy.mock.calls.every((c: unknown[]) => (c[0] as { form: number }).form === code)).toBe(true)
  })

  it.each(forms)('%s: đóng không lưu = OPEN+ABANDON; chưa active thì im', (_name, code) => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    renderHook(() => useFormTelemetry(code, false)).unmount()
    expect(spy).not.toHaveBeenCalled()
    renderHook(() => useFormTelemetry(code, true)).unmount()
    expect(typesOf(spy)).toEqual([UI_EVENT.FORM_OPEN, UI_EVENT.FORM_ABANDON])
  })

  it('13 mã form đủ và duy nhất', () => {
    expect(new Set(Object.values(UI_FORM_CODE)).size).toBe(13)
  })
})
