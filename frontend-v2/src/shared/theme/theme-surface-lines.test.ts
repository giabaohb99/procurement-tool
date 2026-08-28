import { describe, expect, it } from 'vitest'

import { buildThemeCss } from './build-theme-css'
import { contrastRatio } from './color-hue'
import { DEFAULT_THEME_ID, themePresets } from './theme-presets'

/**
 * ĐƯỜNG KẺ TRÊN MẶT THẺ — `--border` (lưới bảng, viền thẻ) và `--input` (viền ô
 * nhập / ô chọn / ô tick, qua lớp `border-input` của shadcn).
 *
 * Sinh ra từ báo lỗi 28/08/2026: chọn bảng màu *Twitter* thì thanh công cụ của
 * màn danh sách mất sạch viền ô nhập và ô chọn, chỉ còn chữ trôi trên nền. Gốc
 * là tweakcn hiểu `--input` là màu NỀN ô nhập, còn shadcn dùng nó làm màu VIỀN:
 * Twitter khai `#f7f9fa` trên thẻ `#f7f8f8`, tức 1.008:1 — cùng một màu.
 * *Notebook* và *Sage Garden* còn khai TRÙNG KHÍT nền (1.000:1).
 *
 * Vá lúc dựng CSS chứ không sửa dữ liệu, vì mức mờ phụ thuộc nền thẻ mà nền thẻ
 * khác nhau giữa hai chế độ nền.
 */

const MODES = [
  ['light', 'html:root'],
  ['dark', 'html.dark:root'],
] as const

const LINE_KEYS = ['border', 'input'] as const

/** Ngưỡng phải khớp `SURFACE_LINE_MIN_CONTRAST` trong `build-theme-css.ts`. */
const MIN_CONTRAST = 1.2

/** Bóc `--ten: giá trị;` trong một khối của chuỗi CSS do `buildThemeCss` sinh. */
function parseBlock(css: string, selector: string): Record<string, string> {
  const open = css.indexOf('{', css.indexOf(selector))
  const close = css.indexOf('}', open)
  const vars: Record<string, string> = {}
  for (const match of css.slice(open + 1, close).matchAll(/--([a-z0-9-]+):\s*([^;]+);/g)) {
    vars[match[1]] = match[2].trim()
  }
  return vars
}

describe('surface line colors across every preset', () => {
  it('keeps every border and input line visible against the card it sits on', () => {
    const invisible: string[] = []

    for (const preset of themePresets) {
      const css = buildThemeCss(preset)
      for (const [mode, selector] of MODES) {
        const vars = parseBlock(css, selector)
        const surface = vars.card ?? vars.background
        for (const key of LINE_KEYS) {
          const ratio = contrastRatio(vars[key], surface)
          if (ratio < MIN_CONTRAST) {
            invisible.push(
              `${preset.id}.${mode}.${key}=${vars[key]} / ${surface} = ${ratio.toFixed(3)}:1`,
            )
          }
        }
      }
    }

    expect(invisible).toEqual([])
  })

  it('rescues the three presets whose input color was identical to the card', () => {
    //  Ba trường hợp tệ nhất trước khi vá. Giữ lại để nếu ai hạ ngưỡng xuống
    //  dưới mức chúng cần thì test đỏ ngay, chứ không đợi người dùng báo lại.
    const worst = [
      { id: 'twitter', mode: 'light' },
      { id: 'notebook', mode: 'light' },
      { id: 'sage-garden', mode: 'light' },
    ] as const

    for (const { id, mode } of worst) {
      const preset = themePresets.find((item) => item.id === id)!
      const selector = mode === 'light' ? 'html:root' : 'html.dark:root'
      const vars = parseBlock(buildThemeCss(preset), selector)
      const surface = vars.card ?? vars.background

      expect(vars.input, `${id}.${mode}.input`).not.toBe(preset[mode].input)
      expect(contrastRatio(vars.input, surface)).toBeGreaterThanOrEqual(MIN_CONTRAST)
    }
  })

  it('leaves the DEGO preset untouched — it is the reference the threshold was set from', () => {
    //  DEGO đo được 1.233:1 ở cả hai khóa nền sáng, tức chỉ nhỉnh hơn ngưỡng.
    //  Nếu bước chuẩn hoá bắt đầu chỉnh nó thì ngưỡng đã bị vặn quá tay.
    const dego = themePresets.find((preset) => preset.id === DEFAULT_THEME_ID)!
    const css = buildThemeCss(dego)

    for (const [mode, selector] of MODES) {
      const vars = parseBlock(css, selector)
      for (const key of LINE_KEYS) {
        expect(vars[key], `${mode}.${key}`).toBe(dego[mode][key])
      }
    }
  })
})
