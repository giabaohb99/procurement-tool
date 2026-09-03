import { act, renderHook } from '@testing-library/react'
import { afterEach, describe, expect, it } from 'vitest'

import { useGanttPaneWidth } from './use-gantt-pane-width'
import { GRID_MIN_WIDTH } from '../utils/gantt-layout'

/**
 * Bề rộng lưới trái của Gantt.
 *
 * Lỗi khách báo 03/09/2026: trên màn rộng 2400px, lưới đứng im ở 600px trong khi
 * biểu đồ ôm 1500px gần như trống — mà bộ cột cần ~1350px nên lưới lại mọc thanh
 * cuộn ngang. Tức là phần chứa thông tin thì chật, phần trống thì rộng. Nay bề
 * rộng mặc định là một TỶ LỆ của khung; con số người dùng tự kéo thì vẫn thắng.
 */

const LIST = 77
const CONTENT = 1400

afterEach(() => localStorage.clear())

function dung(frameWidth: number, contentWidth = CONTENT) {
  return renderHook(() => useGanttPaneWidth(LIST, contentWidth, frameWidth))
}

describe('useGanttPaneWidth', () => {
  it('lấy tỷ lệ của khung nên màn càng rộng thì lưới càng rộng theo', () => {
    //  Đây là lỗi gốc: hai bề rộng khung khác hẳn nhau mà lưới ra cùng một số.
    const hep = dung(1200).result.current.width
    const rong = dung(2400).result.current.width
    expect(rong).toBeGreaterThan(hep)
  })

  it('chừa PHẦN LỚN hơn cho biểu đồ — đó là thứ người ta mở Gantt để xem', () => {
    const { result } = dung(2000)
    expect(result.current.width).toBeLessThan(2000 / 2)
  })

  it('không nong rộng hơn bộ cột — quá đó chỉ là chừa thêm khoảng trắng', () => {
    //  Khung siêu rộng nhưng dự án chỉ khai vài cột.
    const { result } = dung(6000, 500)
    expect(result.current.width).toBe(500)
  })

  it('không bao giờ hẹp hơn ngưỡng tối thiểu, kể cả khung tí hon', () => {
    //  Mở trên cửa sổ hẹp hoặc lúc panel chi tiết chiếm mất chỗ.
    expect(dung(200).result.current.width).toBe(GRID_MIN_WIDTH)
    expect(dung(0).result.current.width).toBeGreaterThanOrEqual(GRID_MIN_WIDTH)
  })

  it('chưa đo được khung (nhịp vẽ đầu) thì vẫn ra một bề rộng dùng được', () => {
    //  `frameWidth = 0` là trạng thái thật ở nhịp render đầu tiên, trước khi
    //  `ResizeObserver` kịp báo số. Ra 0 thì lưới biến mất một nhịp.
    const { result } = dung(0)
    expect(result.current.width).toBeGreaterThan(0)
  })

  it('người dùng đã tự kéo thì con số của họ THẮNG tỷ lệ', () => {
    //  Kéo xong mà phóng to cửa sổ lại tự nong lưới ra là giật mất quyền của họ.
    const { result, rerender } = dung(2400)
    act(() => result.current.resize(700))
    rerender()
    expect(result.current.width).toBe(700)
  })

  it('bề rộng đã kéo vẫn bị kẹp lại khi bộ cột co lại', () => {
    //  Tắt bớt cột ở «Tùy chỉnh»: giữ nguyên số cũ là thừa một mảng trắng ngay
    //  giữa lưới và biểu đồ.
    localStorage.setItem('erp.work.ganttpane.77', '1200')
    const { result } = dung(2400, 800)
    expect(result.current.width).toBe(800)
  })

  it('bản lưu hỏng thì rơi về tỷ lệ chứ không ra NaN', () => {
    //  `localStorage` là chuỗi người dùng sửa được.
    localStorage.setItem('erp.work.ganttpane.77', 'khong-phai-so')
    const { result } = dung(2000)
    expect(Number.isFinite(result.current.width)).toBe(true)
    expect(result.current.width).toBeGreaterThanOrEqual(GRID_MIN_WIDTH)
  })
})
