import { describe, expect, it } from 'vitest'

import { buildWordPreviewPage, unitlessWordLineHeights } from './word-preview-page'

//  Lỗi báo 24/09/2026: xem trước tệp Word thì các dòng đè lên nhau — `line-height`
//  ghi bằng `em` tính theo cỡ chữ của đoạn (nhỏ hơn chữ 13pt bên trong).
describe('unitlessWordLineHeights', () => {
  it('turns Word line spacing in em into a unitless multiplier', () => {
    expect(unitlessWordLineHeights('<p style="margin-top: 0px; line-height: 1.079em">x</p>')).toBe(
      '<p style="margin-top: 0px; line-height: 1.079">x</p>',
    )
  })

  it('handles every occurrence, integers and values without a leading zero', () => {
    const html = '<p style="line-height: 1em">a</p><p style="line-height:.95em">b</p>'
    expect(unitlessWordLineHeights(html)).toBe(
      '<p style="line-height: 1">a</p><p style="line-height: .95">b</p>',
    )
  })

  it('leaves exact spacing in px untouched (Word «Exactly» line spacing)', () => {
    const html = '<p style="line-height: 18px">a</p>'
    expect(unitlessWordLineHeights(html)).toBe(html)
  })

  it('does not touch the words "line-height" in the text itself', () => {
    const html = '<p>line-height: đọc là giãn dòng</p>'
    expect(unitlessWordLineHeights(html)).toBe(html)
  })
})

describe('buildWordPreviewPage', () => {
  it('wraps content in an A4-like page and applies the line-height fix', () => {
    const page = buildWordPreviewPage('<p style="line-height: 1em">Thông báo</p>')
    expect(page).toContain('<div class="page"><p style="line-height: 1">Thông báo</p></div>')
    expect(page).toContain('max-width: 794px')
  })

  it('empty content still yields a valid page (no crash, no "undefined")', () => {
    const page = buildWordPreviewPage('')
    expect(page).toContain('<div class="page"></div>')
    expect(page).not.toContain('undefined')
  })
})
