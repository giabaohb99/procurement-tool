/**
 * Chữ cái đại diện cho ảnh mặc định (khi chưa có ảnh đại diện).
 *
 * Tiếng Việt: TÊN nằm ở từ CUỐI ("Nguyễn Văn An" → "A").
 * Bỏ phần trong ngoặc trước khi lấy — nếu không, "Nhân viên (Demo)" sẽ ra dấu "(",
 * và bỏ luôn mọi ký tự không phải chữ/số để không lòi ra dấu chấm, gạch nối…
 */
export function initialsOf(fullName: string): string {
  const words = (fullName || '')
    .replace(/\([^)]*\)/g, ' ')
    .split(/\s+/)
    .map((w) => w.replace(/[^\p{L}\p{N}]/gu, ''))
    .filter(Boolean)
  return words.length ? words[words.length - 1][0].toUpperCase() : '?'
}
