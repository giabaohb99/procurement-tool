import { describe, expect, it } from 'vitest'

import { buildThemeCss } from './build-theme-css'
import { themePresets } from './theme-presets'

/**
 * THANG ĐỔ BÓNG (`--erp-shadow-2xs` … `--erp-shadow-2xl`).
 *
 * Lỗi 27/08/2026: ứng dụng không khai biến bóng nào, nên `shadow-sm` của thẻ và
 * bảng luôn là đen 10% mặc định của Tailwind, bất kể bảng màu. tweakcn cho mỗi
 * bảng màu một bộ bóng riêng và khoảng cách rất xa nhau, nên bảng màu nào cũng
 * thấy bóng nặng hơn bản gốc.
 */

const STEPS = ['2xs', 'xs', 'sm', 'md', 'lg', 'xl', '2xl'] as const
const MODES = ['light', 'dark'] as const

function readVar(css: string, mode: 'light' | 'dark', name: string): string {
  const block = css.split('html.dark:root')[mode === 'light' ? 0 : 1]
  return new RegExp(`--${name}:\\s*([^;]+);`).exec(block)?.[1].trim() ?? ''
}

function cssOf(id: string) {
  const preset = themePresets.find((item) => item.id === id)
  if (!preset) throw new Error(`không có bảng màu ${id}`)
  return buildThemeCss(preset)
}

const cases = themePresets.flatMap((preset) => MODES.map((mode) => [preset.id, mode] as const))

describe('thang đổ bóng', () => {
  it.each(cases)('%s.%s — khai đủ bảy bậc', (id, mode) => {
    const css = cssOf(id)
    for (const step of STEPS) {
      expect(readVar(css, mode, `erp-shadow-${step}`), step).not.toBe('')
    }
  })

  it('bảng màu không khai tham số bóng thì giữ đúng thang mặc định của Tailwind', () => {
    //  Đây là điều kiện để bộ màu DEGO không đổi một pixel nào: đen 10%, lệch
    //  xuống 1px, nhoè 3px, kèm lớp thứ hai `1px 2px -1px`.
    const dego = themePresets[0]
    expect(dego.light['shadow-opacity'], 'DEGO cố ý KHÔNG khai bóng').toBeUndefined()
    const sm = readVar(buildThemeCss(dego), 'light', 'erp-shadow-sm')
    expect(sm).toContain('0px 1px 3px 0px')
    expect(sm).toContain('0px 1px 2px -1px')
    expect(sm.match(/10\.00%/g)).toHaveLength(2)
  })

  it('bảng màu đặt độ mờ 0 thì mọi bậc đều trong suốt — cố ý không có bóng', () => {
    //  Twitter và Mono khai `shadow-opacity: 0`. Trước đây ta vẫn đổ bóng đen
    //  10% lên chúng, tức nặng hơn bản gốc đúng một lớp bóng.
    for (const id of ['twitter', 'mono']) {
      const preset = themePresets.find((item) => item.id === id)
      expect(preset?.light['shadow-opacity'], id).toBe('0')
      const css = cssOf(id)
      for (const step of STEPS) {
        expect(readVar(css, 'light', `erp-shadow-${step}`), `${id}/${step}`).toContain('0.00%')
      }
    }
  })

  it('lớp bóng thứ hai lùi spread 1px so với lớp đầu', () => {
    //  Đúng theo `getShadowMap` của tweakcn (`utils/shadows.ts`).
    const sm = readVar(cssOf('supabase'), 'light', 'erp-shadow-sm')
    const [lop1, lop2] = sm.split('), ').map((phan) => phan.trim())
    expect(lop1).toContain('0px 1px 3px 0px')
    expect(lop2).toContain('0px 1px 2px -1px')
  })

  it('giữ nguyên màu bóng bảng màu chọn, không ép về đen', () => {
    //  Bubblegum đổ bóng CỨNG màu hồng, lệch 3px, không nhoè — đó là nhận diện
    //  của nó. Ép về đen là mất hẳn.
    const sm = readVar(cssOf('bubblegum'), 'light', 'erp-shadow-sm')
    expect(sm).toContain('#d1519a')
    expect(sm).toContain('3px 3px 0px')
  })
})
