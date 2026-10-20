const MAX_LENGTH = 120
const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i
/** Ký tự backend chấp nhận ở `route` (`^/[A-Za-z0-9/_:\-.]*$`). */
const SAFE_SEGMENT = /^[A-Za-z0-9_:\-.]*$/

/**
 * Đổi đường dẫn thật thành ROUTE MẪU không chứa id/từ khóa — bản cho app cũ thumua (bao-CR-649).
 *
 * Khác v2: app cũ dùng `BrowserRouter` (không có `useMatches`) nên KHÔNG thay theo tên param, chỉ dùng lưới
 * an toàn: đoạn toàn chữ số hoặc dạng uuid → `:id`; đoạn có ký tự lạ (dấu tiếng Việt, `%xx`) → `:id`.
 * Nhờ vậy `new` trong `/purchase-requests/new` được giữ nguyên (ở app cũ `new` là giá trị của `:id`), màn tạo
 * mới không lẫn với màn chi tiết — khớp route v2 `/procurement/purchase-requests/new`.
 * Bỏ `?query` và `#hash`; cắt còn 120 ký tự.
 */
export function toRoutePattern(pathname: string): string {
  const clean = pathname.split(/[?#]/, 1)[0] || '/'
  const segments = clean.split('/').map((seg) => {
    if (!seg) return seg
    if (/^\d+$/.test(seg) || UUID.test(seg) || !SAFE_SEGMENT.test(seg)) return ':id'
    return seg
  })
  const joined = segments.join('/') || '/'
  return (joined.startsWith('/') ? joined : `/${joined}`).slice(0, MAX_LENGTH)
}
