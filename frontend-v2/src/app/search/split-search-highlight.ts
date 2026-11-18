import { stripDiacritics } from '@/shared/utils/vn-text'

/** Một khúc của nhãn: `match = true` là phần trùng với chữ người gõ, tô đậm khi vẽ. */
export interface HighlightPart {
  text: string
  match: boolean
}

/**
 * Cắt nhãn thành các khúc khớp / không khớp với chữ người gõ, KHÔNG phân biệt dấu (duoc-CR-781).
 *
 * Bỏ dấu TỪNG KÝ TỰ một nên vị trí trong chuỗi đã bỏ dấu trùng 1:1 với chuỗi gốc ("Đơn" → "don", ba ký tự cả
 * hai bên) — tô được đúng chữ có dấu trên màn hình dù người dùng gõ không dấu. Mỗi chữ người gõ tô riêng
 * (gõ "don mua" tô cả "Đơn" lẫn "mua"); chuỗi rỗng / khoảng trắng thì trả nguyên nhãn.
 */
export function splitSearchHighlight(label: string, rawQuery: string): HighlightPart[] {
  const tokens = stripDiacritics(rawQuery).split(/\s+/).filter(Boolean)
  if (!label) return []
  if (!tokens.length) return [{ text: label, match: false }]

  const chars = Array.from(label)
  const folded = chars.map((char) => stripDiacritics(char).charAt(0) || char.toLowerCase()).join('')
  const marked = new Array<boolean>(chars.length).fill(false)
  for (const token of tokens) {
    let from = folded.indexOf(token)
    while (from !== -1) {
      for (let i = from; i < from + token.length; i += 1) marked[i] = true
      from = folded.indexOf(token, from + token.length)
    }
  }

  const parts: HighlightPart[] = []
  chars.forEach((char, i) => {
    const last = parts[parts.length - 1]
    if (last && last.match === marked[i]) last.text += char
    else parts.push({ text: char, match: marked[i] })
  })
  return parts
}
