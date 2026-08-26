import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it } from 'vitest'

import { useResizablePanel } from './use-resizable-panel'

const KHOA = 'erp.thu-be-rong'
const CAU_HINH = { storageKey: KHOA, min: 200, max: 420, macDinh: 256 }

/** Giả lập một cú kéo: nhấn ở `x=0` rồi rê tới `x=delta` và thả tay. */
function keo(batDauKeo: (e: never) => void, delta: number) {
  act(() => {
    batDauKeo({ preventDefault: () => {}, clientX: 0 } as never)
  })
  act(() => {
    window.dispatchEvent(new PointerEvent('pointermove', { clientX: delta }))
  })
  act(() => {
    window.dispatchEvent(new PointerEvent('pointerup', { clientX: delta }))
  })
}

beforeEach(() => localStorage.clear())
afterEach(() => localStorage.clear())

describe('useResizablePanel', () => {
  it('chưa kéo lần nào thì lấy bề rộng mặc định', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    expect(result.current.width).toBe(256)
  })

  it('kéo sang phải thì rộng ra đúng khoảng đã kéo', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    keo(result.current.batDauKeo, 100)
    expect(result.current.width).toBe(356)
  })

  it('kéo quá tay bị chặn ở TRẦN, không nuốt hết chỗ phần chính', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    keo(result.current.batDauKeo, 9999)
    expect(result.current.width).toBe(420)
  })

  it('kéo hẹp bị chặn ở SÀN, không bóp thành một vạch', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    keo(result.current.batDauKeo, -9999)
    expect(result.current.width).toBe(200)
  })

  it('thả tay mới ghi xuống localStorage, không ghi mỗi nhịp kéo', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))

    act(() => {
      result.current.batDauKeo({ preventDefault: () => {}, clientX: 0 } as never)
    })
    act(() => {
      window.dispatchEvent(new PointerEvent('pointermove', { clientX: 80 }))
    })
    //  Đang kéo dở: bề rộng đã đổi trên màn nhưng CHƯA ghi đĩa.
    expect(result.current.width).toBe(336)
    expect(localStorage.getItem(KHOA)).toBeNull()

    act(() => {
      window.dispatchEvent(new PointerEvent('pointerup', { clientX: 80 }))
    })
    expect(localStorage.getItem(KHOA)).toBe('336')
  })

  it('mở lại thì lấy đúng bề rộng đã lưu', () => {
    localStorage.setItem(KHOA, '390')
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    expect(result.current.width).toBe(390)
  })

  it('giá trị lưu bị hỏng / ngoài khoảng thì không làm vỡ cột', () => {
    //  Người dùng sửa tay localStorage, hoặc bản cũ lưu khoảng khác.
    localStorage.setItem(KHOA, 'không-phải-số')
    const { result: a } = renderHook(() => useResizablePanel(CAU_HINH))
    expect(a.current.width).toBe(256)

    localStorage.setItem(KHOA, '99999')
    const { result: b } = renderHook(() => useResizablePanel(CAU_HINH))
    expect(b.current.width).toBe(420)
  })

  it('phím mũi tên chỉnh được và ghi luôn xuống localStorage', () => {
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    act(() => result.current.chinhBangPhim(16))
    expect(result.current.width).toBe(272)
    expect(localStorage.getItem(KHOA)).toBe('272')
  })

  it('không khai `storageKey` thì không đụng tới localStorage', () => {
    const { result } = renderHook(() =>
      useResizablePanel({ min: 200, max: 420, macDinh: 256 }),
    )
    keo(result.current.batDauKeo, 50)
    expect(result.current.width).toBe(306)
    expect(localStorage.length).toBe(0)
  })

  it('thả tay xong thì gỡ listener, rê chuột tiếp không đổi bề rộng nữa', () => {
    //  Quên gỡ thì mọi cú rê chuột sau đó đều kéo cột — lỗi kinh điển của
    //  listener gắn trên `window`.
    const { result } = renderHook(() => useResizablePanel(CAU_HINH))
    keo(result.current.batDauKeo, 60)
    const sauKhiTha = result.current.width

    act(() => {
      window.dispatchEvent(new PointerEvent('pointermove', { clientX: 400 }))
    })
    expect(result.current.width).toBe(sauKhiTha)
  })
})
