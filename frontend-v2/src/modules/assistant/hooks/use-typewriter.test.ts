import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useTypewriter } from './use-typewriter'

const SENTENCE = 'Một hai ba bốn năm sáu bảy tám chín mười'

/** Giả lập `matchMedia` — jsdom không có sẵn. */
function setReducedMotion(bat: boolean) {
  vi.stubGlobal('matchMedia', (q: string) => ({
    matches: bat,
    media: q,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }))
}

beforeEach(() => {
  vi.useFakeTimers()
  setReducedMotion(false)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useTypewriter', () => {
  it('bật thì chữ hiện DẦN, không đập ra cả khối', () => {
    const { result } = renderHook(() => useTypewriter(SENTENCE, true))

    expect(result.current.display).toBe('')
    expect(result.current.isRunning).toBe(true)

    act(() => void vi.advanceTimersByTime(100))
    const middle = result.current.display
    expect(middle.length).toBeGreaterThan(0)
    expect(middle.length).toBeLessThan(SENTENCE.length)
    expect(SENTENCE.startsWith(middle)).toBe(true) //  luôn là phần ĐẦU của câu
  })

  it('chạy xong thì ra ĐÚNG nguyên văn, không thiếu không thừa', () => {
    const { result } = renderHook(() => useTypewriter(SENTENCE, true))
    act(() => void vi.advanceTimersByTime(3000))

    expect(result.current.display).toBe(SENTENCE)
    expect(result.current.isRunning).toBe(false)
  })

  it('TẮT thì hiện thẳng trọn nội dung ngay từ nhịp đầu', () => {
    //  Tin cũ trong lịch sử: mở lại hội thoại mà gõ lại từ đầu thì vừa chậm vừa
    //  vô nghĩa.
    const { result } = renderHook(() => useTypewriter(SENTENCE, false))
    expect(result.current.display).toBe(SENTENCE)
    expect(result.current.isRunning).toBe(false)
  })

  it('người dùng tắt hiệu ứng chuyển động ở hệ điều hành thì bỏ qua hiệu ứng', () => {
    setReducedMotion(true)
    const { result } = renderHook(() => useTypewriter(SENTENCE, true))
    act(() => void vi.advanceTimersByTime(20))

    expect(result.current.display).toBe(SENTENCE)
    expect(result.current.isRunning).toBe(false)
  })

  it('đổi nội dung giữa chừng thì gõ LẠI TỪ ĐẦU, không nối tiếp số từ cũ', () => {
    //  Đổi hội thoại trong lúc đang gõ: nếu giữ nguyên số từ đã hiện thì câu mới
    //  bị cắt mất đoạn đầu đúng bằng số từ của câu cũ.
    const { result, rerender } = renderHook(({ t }) => useTypewriter(t, true), {
      initialProps: { t: SENTENCE },
    })
    act(() => void vi.advanceTimersByTime(200))

    rerender({ t: 'Câu hoàn toàn khác' })
    act(() => void vi.advanceTimersByTime(20))
    expect('Câu hoàn toàn khác'.startsWith(result.current.display)).toBe(true)

    act(() => void vi.advanceTimersByTime(3000))
    expect(result.current.display).toBe('Câu hoàn toàn khác')
  })

  it('nội dung rỗng thì không kẹt ở trạng thái đang chạy', () => {
    const { result } = renderHook(() => useTypewriter('', true))
    act(() => void vi.advanceTimersByTime(50))
    expect(result.current.display).toBe('')
    expect(result.current.isRunning).toBe(false)
  })

  it('câu RẤT DÀI vẫn gõ xong trong tầm 1,2 giây, không bắt ngồi xem cả chục giây', () => {
    const dai = Array.from({ length: 600 }, (_, i) => `từ${i}`).join(' ')
    const { result } = renderHook(() => useTypewriter(dai, true))

    act(() => void vi.advanceTimersByTime(1400))
    expect(result.current.display).toBe(dai)
  })
})
