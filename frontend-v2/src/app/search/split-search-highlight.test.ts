import { describe, expect, it } from 'vitest'

import { splitSearchHighlight } from './split-search-highlight'

const marked = (label: string, query: string) =>
  splitSearchHighlight(label, query)
    .filter((part) => part.match)
    .map((part) => part.text)

describe('splitSearchHighlight (duoc-CR-781)', () => {
  it('marks the accented letters on screen even when typed without diacritics', () => {
    expect(marked('Đơn mua hàng', 'don')).toEqual(['Đơn'])
    expect(marked('Biểu thuế', 'BIEU THUE')).toEqual(['Biểu', 'thuế'])
  })

  it('keeps every character of the label, spaces included, in the original order', () => {
    const parts = splitSearchHighlight('Đơn mua hàng', 'mua')
    expect(parts.map((part) => part.text).join('')).toBe('Đơn mua hàng')
    expect(parts).toEqual([
      { text: 'Đơn ', match: false },
      { text: 'mua', match: true },
      { text: ' hàng', match: false },
    ])
  })

  it('marks every occurrence and merges touching matches into one part', () => {
    expect(marked('Yêu cầu mua hàng, mua lại', 'mua')).toEqual(['mua', 'mua'])
    expect(marked('Nhân sự', 'nhan su')).toEqual(['Nhân', 'sự'])
  })

  it('returns the label untouched for an empty query and nothing for an empty label', () => {
    expect(splitSearchHighlight('Kho', '   ')).toEqual([{ text: 'Kho', match: false }])
    expect(splitSearchHighlight('', 'kho')).toEqual([])
  })

  it('treats regex characters as plain text and survives a token longer than the label', () => {
    expect(marked('Báo cáo (tháng)', '(')).toEqual(['('])
    expect(marked('Kho', 'kho tong hop')).toEqual(['Kho'])
  })
})
