/**
 * Rút danh sách BIẾN LẠ từ lỗi 422 khi tải mẫu .docx lên.
 *
 * Backend trả `{ success:false, error:{ code, message, details:{ unknown:[...] } } }`.
 * Đọc thận trọng từng tầng (và nhận cả `error.unknown`) vì phần `details` của lỗi
 * 422 do Pydantic sinh ra lại là MẢNG — gặp mảng thì không phải lỗi biến lạ.
 * Luôn trả mảng chuỗi đã khử trùng, bỏ phần tử rỗng / không phải chuỗi.
 */
export function extractUnknownPlaceholders(error: unknown): string[] {
  const body = (error as { response?: { data?: { error?: unknown } } } | null)?.response?.data
  const err = body?.error as { unknown?: unknown; details?: unknown } | undefined
  if (!err || typeof err !== 'object') return []

  const details = err.details
  const fromDetails =
    details && typeof details === 'object' && !Array.isArray(details)
      ? (details as { unknown?: unknown }).unknown
      : undefined
  const raw = Array.isArray(fromDetails) ? fromDetails : Array.isArray(err.unknown) ? err.unknown : []

  const seen = new Set<string>()
  for (const item of raw) {
    if (typeof item === 'string' && item.trim()) seen.add(item.trim())
  }
  return [...seen]
}
