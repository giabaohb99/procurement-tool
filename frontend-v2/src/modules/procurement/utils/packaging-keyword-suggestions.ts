/**
 * duoc-CR-784 — lọc gợi ý cho ô tìm của thanh lọc chip (27/11/2026): sản phẩm (mã HH + tên) trước, mã thành phần sau, mỗi
 * loại tối đa vài dòng. Không dấu, mọi từ phải có mặt trong mã hoặc tên. Dùng ở `packaging-keyword-suggest-input.tsx`.
 */
import { stripDiacritics } from '@/shared/utils/vn-text'

/** Số dòng gợi ý tối đa mỗi loại — đủ để chọn nhanh, không thành danh sách dài. */
const SUGGEST_MAX = 6

export interface KeywordSuggestion {
  kind: 'product' | 'component'
  code: string
  name: string
}

const fold = (text: string) => stripDiacritics(text).toLowerCase().trim()

/** Gợi ý khớp `keyword`: sản phẩm trước, mã thành phần sau, mỗi loại tối đa `SUGGEST_MAX` dòng. */
export function pickKeywordSuggestions(
  keyword: string,
  products: readonly { code: string; name: string }[],
  components: readonly { code: string; name: string }[],
): KeywordSuggestion[] {
  const terms = fold(keyword).split(/\s+/).filter(Boolean)
  if (terms.length === 0) return []
  const match = (item: { code: string; name: string }) => {
    const haystack = fold(`${item.code} ${item.name}`)
    return terms.every((term) => haystack.includes(term))
  }
  const take = (items: readonly { code: string; name: string }[], kind: KeywordSuggestion['kind']) =>
    items
      .filter(match)
      .slice(0, SUGGEST_MAX)
      .map((item) => ({ kind, code: item.code, name: item.name }))
  return [...take(products, 'product'), ...take(components, 'component')]
}
