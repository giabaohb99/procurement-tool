import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  reportClientError,
  reportLoggedError,
  resetClientErrorState,
  sanitizeErrorMessage,
} from './install-global-error-capture'
import { telemetry } from './telemetry-queue'

beforeEach(() => resetClientErrorState())
afterEach(() => vi.restoreAllMocks())

describe('client error capture', () => {
  it('sends at most 20 distinct errors per page load', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    for (let i = 0; i < 25; i++) reportClientError('Error', `boom ${i}`)
    expect(spy).toHaveBeenCalledTimes(20)
  })

  it('drops repeated messages', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    reportClientError('Error', 'same')
    reportClientError('Error', 'same')
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('masks long digit runs such as phone numbers and truncates to 200', () => {
    expect(sanitizeErrorMessage('lỗi 0912345678 và 12345')).toBe('lỗi # và 12345')
    expect(sanitizeErrorMessage('x'.repeat(500)).length).toBe(200)
    const spy = vi.spyOn(telemetry, 'enqueue')
    reportClientError('Error', 'sdt 0912345678')
    expect(JSON.stringify(spy.mock.calls)).not.toContain('0912345678')
  })

  it('does not recurse when enqueue itself reports an error', () => {
    vi.spyOn(telemetry, 'enqueue').mockImplementation(() => {
      reportClientError('Error', 'inner')
    })
    expect(() => reportClientError('Error', 'outer')).not.toThrow()
  })

  it('maps logger.error arguments, ignoring calls with nothing usable', () => {
    const spy = vi.spyOn(telemetry, 'enqueue')
    reportLoggedError([42, { a: 1 }])
    expect(spy).not.toHaveBeenCalled()
    reportLoggedError(['msg', new TypeError('bad')])
    expect(spy).toHaveBeenCalledTimes(1)
    expect(spy.mock.calls[0][0]).toMatchObject({ error: { name: 'TypeError', message: 'bad' } })
  })
})
