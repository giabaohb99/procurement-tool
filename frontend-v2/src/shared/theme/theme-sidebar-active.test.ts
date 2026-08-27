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

  it('giữ nguyên chữ tweakcn đã chọn khi cặp đó vốn đã đọc được', () => {
    //  Phản hồi 27/08/2026: ngưỡng 4.5 lật chữ gần trắng #fbfbfb của bảng màu
    //  Claude (3.83:1 trên viên mocha #c96442) thành chữ gần đen — thô, và mất
    //  hẳn dáng bản gốc. Test này ghim lại đúng ca đó.
    const css = cssOf('claude')
    expect(readVar(css, 'light', 'sidebar-active')).toBe('#c96442')
    expect(readVar(css, 'light', 'sidebar-active-foreground')).toBe('#fbfbfb')
  })

  it('chỉ đụng vào cặp dưới ngưỡng, cặp nào đạt rồi thì giữ nguyên', () => {
    //  Khẳng định theo TÍNH CHẤT chứ không bốc một bảng màu làm ví dụ: bốc ví dụ
    //  thì đổi dữ liệu bảng màu một cái là test nói dối. Đây đúng là hợp đồng
    //  của `ensureVisibleAgainst` tại chỗ này.
    let daVa = 0
    for (const [id, mode] of suyRa) {
      const preset = themePresets.find((item) => item.id === id)
      if (!preset) throw new Error(`không có bảng màu ${id}`)
      const goc = preset[mode]['sidebar-primary-foreground']
      const nen = preset[mode]['sidebar-primary']
      if (!goc || !nen) continue

      const ra = readVar(cssOf(id), mode, 'sidebar-active-foreground')
      if (contrastRatio(goc, nen) >= 3) {
        expect(ra.toLowerCase(), `${id}.${mode} bị đổi oan`).toBe(goc.toLowerCase())
      } else {
        expect(ra.toLowerCase(), `${id}.${mode} lẽ ra phải vá`).not.toBe(goc.toLowerCase())
        daVa++
      }
    }
    //  Có vá thật, không phải nhánh chết.
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
