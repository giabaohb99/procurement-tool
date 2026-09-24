import { describe, expect, it } from 'vitest'

import { buildHighlightParts } from './search-snippet-highlight'

describe('buildHighlightParts', () => {
  it('trả nguyên chuỗi, không tô, khi không có highlight nào', () => {
    expect(buildHighlightParts('không có gì tô sáng', [])).toEqual([
      { text: 'không có gì tô sáng', highlighted: false },
    ])
  })

  it('trả rỗng khi text rỗng, kể cả có highlight', () => {
    expect(buildHighlightParts('', [[0, 2]])).toEqual([])
  })

  it('cắt đúng MỘT đoạn giữa chuỗi', () => {
    expect(buildHighlightParts('hop dong lao dong', [[4, 8]])).toEqual([
      { text: 'hop ', highlighted: false },
      { text: 'dong', highlighted: true },
      { text: ' lao dong', highlighted: false },
    ])
  })

  it('gộp hai highlight CHỒNG LẤN thành một', () => {
    const parts = buildHighlightParts('van ban', [
      [0, 3],
      [2, 5],
    ])
    expect(parts).toEqual([
      { text: 'van b', highlighted: true },
      { text: 'an', highlighted: false },
    ])
  })

  it('gộp hai highlight LIỀN KỀ (end của cái trước = start của cái sau)', () => {
    const parts = buildHighlightParts('abcdef', [
      [0, 2],
      [2, 4],
    ])
    expect(parts).toEqual([
      { text: 'abcd', highlighted: true },
      { text: 'ef', highlighted: false },
    ])
  })

  it('KHÔNG THEO THỨ TỰ vẫn ra kết quả đúng (backend/caller có thể gửi lộn xộn)', () => {
    const parts = buildHighlightParts('0123456789', [
      [6, 8],
      [0, 2],
    ])
    expect(parts).toEqual([
      { text: '01', highlighted: true },
      { text: '2345', highlighted: false },
      { text: '67', highlighted: true },
      { text: '89', highlighted: false },
    ])
  })

  it('offset ÂM được gọt về 0, không ném lỗi', () => {
    expect(buildHighlightParts('abcde', [[-5, 2]])).toEqual([
      { text: 'ab', highlighted: true },
      { text: 'cde', highlighted: false },
    ])
  })

  it('offset VƯỢT QUÁ độ dài chuỗi được gọt về cuối chuỗi', () => {
    expect(buildHighlightParts('abc', [[1, 999]])).toEqual([
      { text: 'a', highlighted: false },
      { text: 'bc', highlighted: true },
    ])
  })

  it('highlight start === end (rỗng) bị loại bỏ, không tạo đoạn rỗng', () => {
    expect(buildHighlightParts('abcde', [[2, 2]])).toEqual([
      { text: 'abcde', highlighted: false },
    ])
  })

  it('highlight start > end (đảo ngược) bị loại bỏ', () => {
    expect(buildHighlightParts('abcde', [[4, 1]])).toEqual([
      { text: 'abcde', highlighted: false },
    ])
  })

  it('highlight phủ TOÀN BỘ chuỗi', () => {
    expect(buildHighlightParts('abc', [[0, 3]])).toEqual([{ text: 'abc', highlighted: true }])
  })

  it('nhiều highlight tách rời, đúng thứ tự xuất hiện', () => {
    const parts = buildHighlightParts('a-b-c-d', [
      [4, 5],
      [0, 1],
      [2, 3],
    ])
    expect(parts).toEqual([
      { text: 'a', highlighted: true },
      { text: '-', highlighted: false },
      { text: 'b', highlighted: true },
      { text: '-', highlighted: false },
      { text: 'c', highlighted: true },
      { text: '-d', highlighted: false },
    ])
  })
})
