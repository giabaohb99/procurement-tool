/**
 * Đổi đường dẫn trong thông báo sang đường dẫn của app này.
 *
 * Backend sinh ra HAI kiểu link, vì nó phục vụ cả hai giao diện:
 *
 *  1. **Kiểu cũ** — `/purchase-orders/12`, từ thời app `frontend/`. Bản v2 gom
 *     màn hình theo phân hệ nên phải dịch qua `/procurement/purchase-orders/12`.
 *  2. **Kiểu v2 sẵn** — `/document/documents/273`. Phân hệ nào dựng thẳng trên
 *     v2 (Văn thư) thì backend ghi luôn đường dẫn v2.
 *
 * ⚠️ Trước 20/08/2026 hàm này **chỉ biết kiểu 1**. Nhánh "link v2 thì giữ
 * nguyên" so với đúng sáu đích trong `PREFIX_MAP`, nên `/document/documents/273`
 * rơi xuống cuối và trả `null` — bấm vào thông báo **không đi đâu cả**. Hai thư
 * duy nhất của phân hệ Văn thư đều dính: «Bản nháp cần xử lý» (pháp nhân con
 * nhận bản clone) và «Cần rà lại» (bản gốc lên phiên bản mới). Nghĩa là toàn bộ
 * đường báo việc của luồng clone gãy ở bước cuối cùng.
 *
 * Màn hình nào v2 chưa có (yêu cầu thanh toán, mẻ nhập) thì vẫn trả `null` —
 * chỗ gọi đánh dấu đã đọc nhưng không điều hướng, thà đứng yên còn hơn quăng
 * người dùng vào trang trắng.
 */
const PREFIX_MAP: [from: string, to: string][] = [
  ['/purchase-requests', '/procurement/purchase-requests'],
  ['/purchase-orders', '/procurement/purchase-orders'],
  ['/survey-requests', '/procurement/survey-requests'],
  ['/surveys', '/procurement/surveys'],
  ['/suppliers', '/production/suppliers'],
  ['/employees', '/hr/employees'],
]

/**
 * Tiền tố của các phân hệ v2 — link bắt đầu bằng một trong số này là đã đúng
 * dạng, đi thẳng.
 *
 * Danh sách này phải phủ mọi phân hệ đang bật trong `module-registry`; có bài
 * kiểm canh chuyện đó, thêm phân hệ mà quên thêm vào đây là test đỏ.
 */
const V2_PREFIXES = [
  '/approval',
  '/approval-seal',
  '/customer',
  '/dego-coffee',
  '/document',
  '/finance',
  '/hr',
  '/inventory',
  '/procurement',
  '/production',
  '/project',
  '/report',
  '/sales',
  '/system',
  '/vehicle-booking',
]

/** Link có nằm trong nhánh của tiền tố này không (`/document` khớp `/document/x`). */
function thuocNhanh(link: string, prefix: string): boolean {
  return link === prefix || link.startsWith(`${prefix}/`) || link.startsWith(`${prefix}?`)
}

export function toAppPath(link: string): string | null {
  if (!link) return null

  //  Đã là đường dẫn v2 thì giữ nguyên. Xét TRƯỚC bảng dịch: `/procurement/...`
  //  vừa là đích của bảng dịch vừa là tiền tố phân hệ, xét sau thì thừa một vòng.
  if (V2_PREFIXES.some((prefix) => thuocNhanh(link, prefix))) return link

  for (const [from, to] of PREFIX_MAP) {
    if (thuocNhanh(link, from)) return to + link.slice(from.length)
  }
  return null
}

export { V2_PREFIXES }
