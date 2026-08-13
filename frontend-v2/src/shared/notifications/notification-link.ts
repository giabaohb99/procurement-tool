/**
 * Đổi đường dẫn trong thông báo sang đường dẫn của app này.
 *
 * Thông báo và cảnh báo do backend sinh ra từ thời app CŨ, nên `link` là dạng
 * `/purchase-orders/12`. Bản v2 gom màn hình theo phân hệ (`/procurement/...`)
 * nên nhảy thẳng link cũ là ra trang trắng.
 *
 * Màn hình nào v2 chưa có (công nợ, hợp đồng) thì trả `null` — chỗ gọi vẫn đánh
 * dấu đã đọc nhưng không điều hướng, thà đứng yên còn hơn quăng người dùng vào
 * trang 404.
 */
const PREFIX_MAP: [from: string, to: string][] = [
  ['/purchase-requests', '/procurement/purchase-requests'],
  ['/purchase-orders', '/procurement/purchase-orders'],
  ['/survey-requests', '/procurement/survey-requests'],
  ['/surveys', '/procurement/surveys'],
  ['/suppliers', '/production/suppliers'],
  ['/employees', '/hr/employees'],
]

export function toAppPath(link: string): string | null {
  if (!link) return null

  // Link nội bộ v2 (đã đúng dạng) thì giữ nguyên.
  if (PREFIX_MAP.some(([, to]) => link.startsWith(to))) return link

  for (const [from, to] of PREFIX_MAP) {
    if (link === from || link.startsWith(`${from}/`) || link.startsWith(`${from}?`)) {
      return to + link.slice(from.length)
    }
  }
  return null
}
