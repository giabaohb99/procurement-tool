import { describe, expect, it } from 'vitest'

import { buildThemeCss } from './build-theme-css'
import { themePresets } from './theme-presets'

/**
 * NỀN TRANG (`--canvas`) — mặt phẳng nằm sau thẻ nội dung.
 *
 * Lỗi 27/08/2026: biến này từng suy ra bằng
 * `color-mix(in oklab, var(--background) 95%, var(--foreground))`. Đo trên bảng
 * màu Claude nền sáng thì nó ra `#f0eeea` — trùng khít màu vằn hàng chẵn của
 * bảng danh sách, và còn TỐI HƠN menu trái `#f5f4ee`, tức lộn ngược thứ tự
 * chiều sâu. Nay suy ra bằng đúng `--background`, giống shadcn/tweakcn.
 */

/** Đọc một biến màu ra khỏi đoạn CSS đã dựng. */
function readVar(css: string, mode: 'light' | 'dark', name: string): string {
  const block = css.split('html.dark:root')[mode === 'light' ? 0 : 1]
  return new RegExp(`--${name}:\\s*([^;]+);`).exec(block)?.[1].trim() ?? ''
}

const MODES = ['light', 'dark'] as const

/** Bảng màu để TRỐNG `canvas` — tức nền trang do `build-theme-css.ts` suy ra. */
const suyRa = themePresets.flatMap((preset) =>
  MODES.filter((mode) => !preset[mode].canvas).map((mode) => [preset.id, mode] as const),
)

function cssOf(id: string) {
  const preset = themePresets.find((item) => item.id === id)
  if (!preset) throw new Error(`không có bảng màu ${id}`)
  return buildThemeCss(preset)
}

describe('nền trang', () => {
  it('có bảng màu để kiểm', () => {
    expect(suyRa.length).toBeGreaterThan(0)
  })

  it.each(suyRa)('%s.%s — nền trang lấy đúng --background của bảng màu', (id, mode) => {
    const css = cssOf(id)
    expect(readVar(css, mode, 'canvas')).toBe('var(--background)')
  })

  it.each(suyRa)('%s.%s — nền trang không trùng vằn hàng chẵn', (id, mode) => {
    //  Trùng thì cái thẻ chứa bảng danh sách tan vào nền trang. Cách suy ra cũ
    //  dính đúng lỗi này ở 15/86 tổ hợp: `--row-stripe` cũng là phép pha 95%,
    //  nên bảng màu nào để `card` = `background` là hai công thức ra cùng số.
    const preset = themePresets.find((item) => item.id === id)
    if (!preset) throw new Error(`không có bảng màu ${id}`)
    const colors = preset[mode]
    const nenTrang = colors.background
    const vanHang = readVar(cssOf(id), mode, 'row-stripe')

    //  Nền trang là màu NGUYÊN, vằn hàng là phép pha — không cách nào bằng nhau.
    expect(vanHang).not.toBe(nenTrang)
  })
})
