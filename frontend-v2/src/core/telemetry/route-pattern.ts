const MAX_LENGTH = 120
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
/** Ký tự backend chấp nhận ở `route` (`^/[A-Za-z0-9/_:\-.]*$`). */
const SAFE_SEGMENT = /^[A-Za-z0-9_:\-.]*$/

/**
 * Đổi đường dẫn thật thành ROUTE MẪU không chứa id/từ khóa.
 *
 *  1. Đoạn trùng giá trị một param của router → `:tên` param.
 *  2. Lưới an toàn: đoạn toàn chữ số hoặc dạng uuid → `:id`; đoạn có ký tự lạ
 *     (dấu tiếng Việt, `%xx`…) → `:id` — tránh làm 422 cả lô và tránh lọt chữ.
 *  3. Bỏ `?query` và `#hash`; cắt còn 120 ký tự.
 */
export function toRoutePattern(pathname: string, params: Record<string, string | undefined> = {}): string {
  const clean = pathname.split(/[?#]/, 1)[0] || '/'
  const byValue = new Map<string, string>()
  for (const [name, value] of Object.entries(params)) {
    // Param splat (`*`) là phần đuôi có thể chứa nhiều đoạn — để lưới an toàn lo.
    if (value && name !== '*') byValue.set(value, name)
  }
  const segments = clean.split('/').map((seg) => {
    if (!seg) return seg
    const name = byValue.get(seg)
    if (name) return `:${name}`
    if (/^\d+$/.test(seg) || UUID.test(seg) || !SAFE_SEGMENT.test(seg)) return ':id'
    return seg
  })
  const joined = segments.join('/') || '/'
  return (joined.startsWith('/') ? joined : `/${joined}`).slice(0, MAX_LENGTH)
}
