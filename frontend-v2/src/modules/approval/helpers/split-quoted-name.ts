/** Một mảnh chữ của câu dấu vết — `strong = true` là tên nằm trong ngoặc, hiện in đậm. */
export interface QuotedSegment {
  text: string
  strong: boolean
}

/**
 * Bóc tên trong ngoặc ra khỏi câu máy ghi, để hiện in đậm thay cho dấu ngoặc.
 *
 * Câu "Trình duyệt theo luồng ... bản N" do bộ máy duyệt ghi sẵn vào `comment`.
 * Phiếu cũ (trước bao-CR-695) lưu tên luồng trong ngoặc kép góc, phiếu mới lưu trong
 * nháy thẳng — dữ liệu đã nằm trong CSDL nên phải nhận cả hai. Ngoặc không đóng thì
 * giữ nguyên chữ, không đoán.
 */
export function splitQuotedName(text: string): QuotedSegment[] {
  //  Ngoặc kép góc viết bằng mã thoát để mã nguồn không chứa ký tự đó (bao-CR-695).
  const pattern = /\u00ab([^\u00bb]+)\u00bb|"([^"]+)"/g
  const segments: QuotedSegment[] = []
  let cursor = 0
  for (const match of text.matchAll(pattern)) {
    const start = match.index ?? 0
    if (start > cursor) segments.push({ text: text.slice(cursor, start), strong: false })
    segments.push({ text: match[1] ?? match[2] ?? '', strong: true })
    cursor = start + match[0].length
  }
  if (cursor < text.length) segments.push({ text: text.slice(cursor), strong: false })
  return segments
}
