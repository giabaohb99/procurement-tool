import { describe, expect, it } from 'vitest'

import { buildThemeCss } from './build-theme-css'
import { contrastRatio } from './color-hue'
import { themePresets } from './theme-presets'

/**
 * Mục menu ĐANG MỞ tô bằng cặp `--sidebar-active` / `--sidebar-active-foreground`
 * (xem `app/layouts/module-sidebar.tsx`).
 *
 * Lỗi 27/08/2026: trước đó mục đang mở viết cứng `bg-primary/10` + `text-primary`.
 * Đo cả 42 bảng màu × 2 chế độ nền thì vệt nền so với nền menu cao nhất mới
 * 1.31:1 — không bảng màu nhập từ ngoài nào cho ra một vệt nhìn thấy được.
 */

/** Đọc một biến màu ra khỏi đoạn CSS đã dựng, trong khối `light` hoặc `dark`. */
function readVar(css: string, mode: 'light' | 'dark', name: string): string {
  const block = css.split('html.dark:root')[mode === 'light' ? 0 : 1]
  return new RegExp(`--${name}:\\s*([^;]+);`).exec(block)?.[1].trim() ?? ''
}

const MODES = ['light', 'dark'] as const

/**
 * Bảng màu để TRỐNG `sidebar-active` — tức viên nền do `build-theme-css.ts` suy
 * ra. Chỉ nhóm này bị soi tương phản: bảng màu tự khai nghĩa là đã có người cân
 * nhắc (hiện chỉ mỗi DEGO, và nó cố tình chọn vệt nhạt).
 */
const suyRa = themePresets.flatMap((preset) =>
  MODES.filter((mode) => !preset[mode]['sidebar-active']).map((mode) => [preset.id, mode] as const),
)

/** Bảng màu TỰ KHAI viên nền — không ép tương phản, chỉ kiểm khai đủ cặp. */
const tuKhai = themePresets.flatMap((preset) =>
  MODES.filter((mode) => preset[mode]['sidebar-active']).map((mode) => [preset.id, mode] as const),
)

function cssOf(id: string) {
  const preset = themePresets.find((item) => item.id === id)
  if (!preset) throw new Error(`không có bảng màu ${id}`)
  return buildThemeCss(preset)
}

describe('viên nền của mục menu đang mở', () => {
  it('có đủ hai nhóm để kiểm — suy ra và tự khai', () => {
    expect(suyRa.length).toBeGreaterThan(0)
    expect(tuKhai.length).toBeGreaterThan(0)
    expect(suyRa.length + tuKhai.length).toBe(themePresets.length * 2)
  })

  it.each(suyRa)('%s.%s (suy ra) — chữ đọc được trên viên nền', (id, mode) => {
    const css = cssOf(id)
    const nen = readVar(css, mode, 'sidebar-active')
    const chu = readVar(css, mode, 'sidebar-active-foreground')

    expect(nen, 'thiếu --sidebar-active').toMatch(/^#[0-9a-f]{6}$/i)
    expect(chu, 'thiếu --sidebar-active-foreground').toMatch(/^#[0-9a-f]{6}$/i)
    //  3:1 — xem `SIDEBAR_ACTIVE_MIN_CONTRAST` về việc vì sao cố ý không phải
    //  4.5: ngưỡng cao hơn thì lật luôn cả những cặp màu tweakcn vốn đang đẹp.
    expect(contrastRatio(chu, nen)).toBeGreaterThanOrEqual(3)
  })

  it.each(suyRa)('%s.%s — KHÔNG đụng vào màu chữ bảng màu đã chọn', (id, mode) => {
    //  Phản hồi 27/08/2026: bản đầu kéo màu CHỮ cho hợp viên nền. Bảng màu
    //  Twitter khai chữ trắng trên xanh `#1e9df1` (2.94:1) nên chữ trắng bị lật
    //  thành chữ tối — mục đang mở nhìn như bị lỗi. Gần như bảng màu nào cũng
    //  chọn chữ SÁNG trên viên màu đặc; đó là ý đồ thiết kế, không phải chỗ sửa.
    const preset = themePresets.find((item) => item.id === id)
    if (!preset) throw new Error(`không có bảng màu ${id}`)
    const goc = preset[mode]['sidebar-primary-foreground'] ?? preset[mode].background
    expect(readVar(cssOf(id), mode, 'sidebar-active-foreground').toLowerCase()).toBe(
      goc?.toLowerCase(),
    )
  })

  it('chỉ làm sâu viên nền khi thiếu tương phản, đủ rồi thì giữ nguyên', () => {
    //  Khẳng định theo TÍNH CHẤT chứ không bốc một bảng màu làm ví dụ: bốc ví dụ
    //  thì đổi dữ liệu bảng màu một cái là test nói dối.
    let daVa = 0
    for (const [id, mode] of suyRa) {
      const preset = themePresets.find((item) => item.id === id)
      if (!preset) throw new Error(`không có bảng màu ${id}`)
      const nenGoc = preset[mode]['sidebar-primary'] ?? preset[mode].primary
      const chu = preset[mode]['sidebar-primary-foreground'] ?? preset[mode].background
      if (!nenGoc || !chu) continue

      const ra = readVar(cssOf(id), mode, 'sidebar-active')
      if (contrastRatio(chu, nenGoc) >= 3) {
        expect(ra.toLowerCase(), `${id}.${mode} bị đổi oan`).toBe(nenGoc.toLowerCase())
      } else {
        expect(ra.toLowerCase(), `${id}.${mode} lẽ ra phải làm sâu`).not.toBe(nenGoc.toLowerCase())
        daVa++
      }
    }
    //  Quét ngày 27/08/2026: đúng 10/84 tổ hợp phải vá. Không phải nhánh chết.
    expect(daVa).toBeGreaterThan(0)
  })

  it.each(suyRa)('%s.%s (suy ra) — viên nền nổi được trên nền menu', (id, mode) => {
    const css = cssOf(id)
    const nen = readVar(css, mode, 'sidebar-active')
    const menu = readVar(css, mode, 'sidebar')

    //  1.31 là mức TỐT NHẤT mà cách cũ (`bg-primary/10`) đạt được trên toàn bộ
    //  42 bảng màu. Cách mới phải hơn hẳn con số đó, không thì coi như chưa sửa.
    expect(contrastRatio(nen, menu)).toBeGreaterThan(1.31)
  })

  it.each(tuKhai)('%s.%s (tự khai) — khai đủ cả viên nền lẫn màu chữ', (id, mode) => {
    const css = cssOf(id)
    expect(readVar(css, mode, 'sidebar-active')).toMatch(/^#[0-9a-f]{6}$/i)
    expect(readVar(css, mode, 'sidebar-active-foreground')).toMatch(/^#[0-9a-f]{6}$/i)
  })

  it('bảng màu DEGO giữ đúng vệt nhạt đang chạy, không bị ép sang viên đặc', () => {
    //  Quyết ngày 27/08/2026: xanh lơ #00aeef tô đặc cả dòng menu thì chói hẳn
    //  so với phần còn lại. Giá trị dưới đây là `bg-primary/10` đã chồng sẵn lên
    //  nền menu, nên đổi sang cặp token mới không lệch một pixel nào.
    const css = cssOf(themePresets[0].id)
    expect(readVar(css, 'light', 'sidebar-active')).toBe('#e6f7fd')
    expect(readVar(css, 'light', 'sidebar-active-foreground')).toBe('#00aeef')
    expect(readVar(css, 'dark', 'sidebar-active')).toBe('#1b364d')
  })
})
