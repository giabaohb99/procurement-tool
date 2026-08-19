import { describe, expect, it } from 'vitest'

import { fillPageMarkers, hasPageMarkerContent, PAGE_MARKERS } from './page-marker'

describe('fillPageMarkers', () => {
  it('thay đủ các thẻ trong một dòng', () => {
    const ra = fillPageMarkers('{{so_hieu}} — trang {{trang}}/{{tong_trang}}', {
      soHieu: '08/2026/TB-DEGO',
      trang: 2,
      tongTrang: 5,
    })

    expect(ra).toBe('08/2026/TB-DEGO — trang 2/5')
  })

  it('thẻ chưa có giá trị thì để TRỐNG, không để lại thẻ thô', () => {
    //  In ra tờ giấy mang dòng "{{so_hieu}}" là lỗi ai cũng thấy.
    expect(fillPageMarkers('Số: {{so_hieu}}', {})).toBe('Số: ')
  })

  it('thay mọi lần xuất hiện của cùng một thẻ', () => {
    expect(fillPageMarkers('{{trang}} · {{trang}}', { trang: 3 })).toBe('3 · 3')
  })

  it('giữ nguyên chữ không phải thẻ', () => {
    expect(fillPageMarkers('Ban hành nội bộ', {})).toBe('Ban hành nội bộ')
  })

  it('chuỗi rỗng thì trả rỗng, không nổ', () => {
    expect(fillPageMarkers('', { trang: 1 })).toBe('')
  })

  it('nhận số 0 như một giá trị thật, không coi là chưa có', () => {
    expect(fillPageMarkers('trang {{trang}}', { trang: 0 })).toBe('trang 0')
  })

  it('mọi thẻ được gợi ý trên giao diện đều thay được', () => {
    //  Gợi ý một thẻ mà không thay nổi thì người dùng gõ đúng vẫn ra thẻ thô.
    const mau = PAGE_MARKERS.map((m) => m.the).join(' ')
    const ra = fillPageMarkers(mau, {
      trang: 1,
      tongTrang: 2,
      soHieu: 'A',
      tenVanBan: 'B',
      ngay: '19/08/2026',
    })

    expect(ra).not.toMatch(/\{\{/)
  })
})

describe('hasPageMarkerContent', () => {
  it('bốn ô đều rỗng thì không vẽ dải đầu/chân trang', () => {
    expect(hasPageMarkerContent('', '   ', undefined, '')).toBe(false)
  })

  it('chỉ cần một ô có chữ là phải vẽ', () => {
    expect(hasPageMarkerContent('', '', 'Nội bộ', '')).toBe(true)
  })
})
