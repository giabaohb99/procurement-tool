import { describe, expect, it } from 'vitest'

import { buildThemeCss } from './build-theme-css'
import { contrastRatio } from './color-hue'
import { DEFAULT_THEME_ID, themePresets } from './theme-presets'

/**
 * MÀU CỘT BIỂU ĐỒ.
 *
 * Tổng quan Thu mua, Trang chủ và Tổng quan Tài chính đều vẽ biểu đồ 4 chuỗi
 * bằng `--chart-1..4`. Bảng màu nhập về không hề được thiết kế cho việc đó, và
 * đo ra thì hỏng thật:
 * - *Mono* có **cả 4 màu giống hệt nhau** (`#737373`) — bốn cột thành một màu;
 * - *Solar Dusk* trùng `chart-2` với `chart-4` (`#78716C`);
 * - 62/430 màu cột chìm hẳn vào nền thẻ (*Caffeine* mất 3/4 cột ở nền sáng,
 *   *Claude* mất 2 cột ở cả hai chế độ nền).
 *
 * Hai chỗ vá, tách bạch:
 * - TRÙNG NHAU sửa thẳng trong dữ liệu (`theme-presets.ts`) vì đó là lỗi của
 *   bộ màu, không phải của cách hiển thị;
 * - CHÌM VÀO NỀN sửa lúc dựng CSS (`ensureVisibleAgainst`) vì nó phụ thuộc nền
 *   thẻ, mà nền thẻ thì khác nhau giữa hai chế độ nền.
 */

const CHART_KEYS = ['chart-1', 'chart-2', 'chart-3', 'chart-4'] as const
const MODES = ['light', 'dark'] as const

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

describe('màu cột biểu đồ của mọi bảng màu', () => {
  it('bảng màu nào cũng khai đủ chart-1..4 cho cả hai chế độ nền', () => {
    const missing: string[] = []
    for (const preset of themePresets) {
      for (const mode of MODES) {
        for (const key of CHART_KEYS) {
          if (!preset[mode][key]) missing.push(`${preset.id}.${mode}.${key}`)
        }
      }
    }
    expect(missing).toEqual([])
  })

  it('không bảng màu nào có hai màu cột TRÙNG NHAU — hai chuỗi cùng màu là đọc nhầm số liệu', () => {
    const duplicated: string[] = []
    for (const preset of themePresets) {
      for (const mode of MODES) {
        const colors = CHART_KEYS.map((key) => preset[mode][key]?.toLowerCase()).filter(Boolean)
        const unique = new Set(colors)
        if (unique.size !== colors.length) {
          duplicated.push(`${preset.id}.${mode}: ${colors.join(', ')}`)
        }
      }
    }
    expect(duplicated).toEqual([])
  })

  it('mọi màu cột nổi được trên nền thẻ sau khi dựng CSS', () => {
    const invisible: string[] = []

    for (const preset of themePresets) {
      const css = buildThemeCss(preset)
      for (const [mode, selector] of [
        ['light', 'html:root'],
        ['dark', 'html.dark:root'],
      ] as const) {
        const vars = parseBlock(css, selector)
        const card = vars.card ?? vars.background
        for (const key of CHART_KEYS) {
          const ratio = contrastRatio(vars[key], card)
          if (ratio < 2) {
            invisible.push(`${preset.id}.${mode}.${key}=${vars[key]} / ${card} = ${ratio.toFixed(2)}:1`)
          }
        }
      }
    }

    expect(invisible).toEqual([])
  })

  it('bộ 4 màu của bảng màu DEGO đi thẳng ra CSS, không bị chuẩn hoá đụng vào', () => {
    //  Bộ này đã kiểm tương phản + mù màu protan/deutan (xem chú thích trong
    //  `index.css`). Nếu bước chuẩn hoá bắt đầu chỉnh nó thì hoặc ngưỡng đã bị
    //  vặn quá tay, hoặc dữ liệu DEGO đã bị sửa — cả hai đều phải biết ngay.
    const dego = themePresets.find((preset) => preset.id === DEFAULT_THEME_ID)!
    const css = buildThemeCss(dego)

    for (const [mode, selector] of [
      ['light', 'html:root'],
      ['dark', 'html.dark:root'],
    ] as const) {
      const vars = parseBlock(css, selector)
      for (const key of CHART_KEYS) {
        expect(vars[key], `${mode}.${key}`).toBe(dego[mode][key])
      }
    }
  })
})
