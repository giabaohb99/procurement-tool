/**
 * Cắt đoạn trích TÌM KIẾM TOÀN VĂN (phase 07, duoc-CR-477) thành các đoạn
 * thường/tô sáng theo offset — hàm THUẦN, tách khỏi `search-snippet.tsx` để
 * file component chỉ export component (ESLint `react-refresh/only-export-
 * components` — xuất kèm hàm thường trong file component làm Fast Refresh
 * của Vite không nhận diện được, phải reload cả trang mỗi lần sửa).
 */

export interface HighlightPart {
  text: string
  highlighted: boolean
}

/**
 * Tự vệ trước offset THẤT THƯỜNG (dù backend đã dựng cẩn thận): âm, vượt quá
 * độ dài chuỗi, chồng lấn, không theo thứ tự, `start >= end` — mọi trường hợp
 * đó đều bị gọt/lọc/gộp thay vì làm hỏng cả đoạn trích hoặc ném lỗi render.
 */
export function buildHighlightParts(
  text: string,
  highlights: readonly (readonly [number, number])[],
): HighlightPart[] {
  if (!text) return []
  if (highlights.length === 0) return [{ text, highlighted: false }]

  const clipped = highlights
    .map(([start, end]): [number, number] => [
      Math.max(0, Math.min(start, text.length)),
      Math.max(0, Math.min(end, text.length)),
    ])
    .filter(([start, end]) => end > start)
    .sort((a, b) => a[0] - b[0])

  if (clipped.length === 0) return [{ text, highlighted: false }]

  //  Gộp các khoảng CHỒNG LẤN hoặc LIỀN KỀ — hai `<mark>` dính nhau không có
  //  khoảng trắng ở giữa trông như một, tách ra chỉ thêm nút DOM vô ích.
  const merged: [number, number][] = [clipped[0]!]
  for (const [start, end] of clipped.slice(1)) {
    const last = merged[merged.length - 1]!
    if (start <= last[1]) last[1] = Math.max(last[1], end)
    else merged.push([start, end])
  }

  const parts: HighlightPart[] = []
  let cursor = 0
  for (const [start, end] of merged) {
    if (start > cursor) parts.push({ text: text.slice(cursor, start), highlighted: false })
    parts.push({ text: text.slice(start, end), highlighted: true })
    cursor = end
  }
  if (cursor < text.length) parts.push({ text: text.slice(cursor), highlighted: false })
  return parts
}
