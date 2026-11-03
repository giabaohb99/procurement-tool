import { renderHook } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'

import { useSingleFlight } from './use-single-flight'

describe('useSingleFlight', () => {
  it('lets only the first of two same-tick calls start, and reopens after release', () => {
    const { result } = renderHook(() => useSingleFlight())
    const start = vi.fn()
    expect(result.current(start)).toBe(true)
    expect(result.current(start)).toBe(false)
    expect(start).toHaveBeenCalledTimes(1)

    start.mock.calls[0][0]()
    expect(result.current(start)).toBe(true)
    expect(start).toHaveBeenCalledTimes(2)
  })

  it('releases the lock when start throws synchronously', () => {
    const { result } = renderHook(() => useSingleFlight())
    expect(() =>
      result.current(() => {
        throw new Error('boom')
      }),
    ).toThrow('boom')
    expect(result.current(() => undefined)).toBe(true)
  })
})
