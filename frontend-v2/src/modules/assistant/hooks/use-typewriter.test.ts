import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useTypewriter } from './use-typewriter'

const CAU = 'Một hai ba bốn năm sáu bảy tám chín mười'

/** Giả lập `matchMedia` — jsdom không có sẵn. */
function datGiamChuyenDong(bat: boolean) {
  vi.stubGlobal('matchMedia', (q: string) => ({
    matches: bat,
    media: q,
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
  }))
}

beforeEach(() => {
  vi.useFakeTimers()
  datGiamChuyenDong(false)
})

afterEach(() => {
  vi.useRealTimers()
  vi.unstubAllGlobals()
})

describe('useTypewriter', () => {
  it('bật thì chữ hiện DẦN, không đập ra cả khối', () => {
    const { result } = renderHook(() => useTypewriter(CAU, true))

    expect(result.current.hienThi).toBe('')
    expect(result.current.dangChay).toBe(true)

    act(() => void vi.advanceTimersByTime(100))
    const giua = result.current.hienThi
    expect(giua.length).toBeGreaterThan(0)
    expect(giua.length).toBeLessThan(CAU.length)
    expect(CAU.startsWith(giua)).toBe(true) //  luôn là phần ĐẦU của câu
  })

  it('chạy xong thì ra ĐÚNG nguyên văn, không thiếu không thừa', () => {
    const { result } = renderHook(() => useTypewriter(CAU, true))
    act(() => void vi.advanceTimersByTime(3000))

    expect(result.current.hienThi).toBe(CAU)
    expect(result.current.dangChay).toBe(false)
  })

  it('TẮT thì hiện thẳng trọn nội dung ngay từ nhịp đầu', () => {
    //  Tin cũ trong lịch sử: mở lại hội thoại mà gõ lại từ đầu thì vừa chậm vừa
    //  vô nghĩa.
    const { result } = renderHook(() => useTypewriter(CAU, false))
    expect(result.current.hienThi).toBe(CAU)
    expect(result.current.dangChay).toBe(false)
  })

  it('người dùng tắt hiệu ứng chuyển động ở hệ điều hành thì bỏ qua hiệu ứng', () => {
    datGiamChuyenDong(true)
    const { result } = renderHook(() => useTypewriter(CAU, true))
    act(() => void vi.advanceTimersByTime(20))

    expect(result.current.hienThi).toBe(CAU)
    expect(result.current.dangChay).toBe(false)
  })

  it('đổi nội dung giữa chừng thì gõ LẠI TỪ ĐẦU, không nối tiếp số từ cũ', () => {
    //  Đổi hội thoại trong lúc đang gõ: nếu giữ nguyên số từ đã hiện thì câu mới
    //  bị cắt mất đoạn đầu đúng bằng số từ của câu cũ.
    const { result, rerender } = renderHook(({ t }) => useTypewriter(t, true), {
      initialProps: { t: CAU },
    })
    act(() => void vi.advanceTimersByTime(200))

    rerender({ t: 'Câu hoàn toàn khác' })
    act(() => void vi.advanceTimersByTime(20))
    expect('Câu hoàn toàn khác'.startsWith(result.current.hienThi)).toBe(true)

    act(() => void vi.advanceTimersByTime(3000))
    expect(result.current.hienThi).toBe('Câu hoàn toàn khác')
  })

  it('nội dung rỗng thì không kẹt ở trạng thái đang chạy', () => {
    const { result } = renderHook(() => useTypewriter('', true))
    act(() => void vi.advanceTimersByTime(50))
    expect(result.current.hienThi).toBe('')
    expect(result.current.dangChay).toBe(false)
  })

  it('câu RẤT DÀI vẫn gõ xong trong tầm 1,2 giây, không bắt ngồi xem cả chục giây', () => {
    const dai = Array.from({ length: 600 }, (_, i) => `từ${i}`).join(' ')
    const { result } = renderHook(() => useTypewriter(dai, true))

    act(() => void vi.advanceTimersByTime(1400))
    expect(result.current.hienThi).toBe(dai)
  })
})
