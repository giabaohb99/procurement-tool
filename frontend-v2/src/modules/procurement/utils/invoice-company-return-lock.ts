import type { PermissionAction } from '@/core/authorization/permission-types'

/**
 * duoc-CR-803 — YCMH đang mua hàng được TRẢ VỀ chỉ để sửa Công ty nhận hóa đơn.
 *
 * Phiếu về Bị trả lại (rồi Chờ duyệt khi gửi lại) nhưng các ĐMH của nó vẫn còn nguyên. Trong
 * lúc đó backend chỉ nhận ô `company_id` khi lưu phiếu và khóa MỌI đường ghi của các ĐMH liên
 * quan; duyệt lại phiếu thì công ty mới chép xuống đơn và phiếu về Đang mua hàng. Giao diện
 * chỉ là lớp khóa cho êm tay — chặn thật nằm ở backend.
 */

/** Câu nhắc đầu trang YCMH khi phiếu đang ở chế độ chỉ sửa Công ty nhận hóa đơn. */
export const INVOICE_COMPANY_ONLY_NOTICE =
  'Phiếu được trả về chỉ để sửa Công ty nhận hóa đơn. Các đơn mua hàng liên quan đang tạm khóa tới khi phiếu được duyệt lại.'

/** Dòng thêm vào hộp lý do khi bấm Trả về trên phiếu Đang mua hàng. */
export const PURCHASING_RETURN_NOTICE =
  'Phiếu đang mua hàng: trả về chỉ để người lập sửa Công ty nhận hóa đơn, các ô khác giữ nguyên. Các đơn mua hàng liên quan sẽ tạm khóa tới khi phiếu được duyệt lại.'

/** Phiếu đang ở chế độ chỉ sửa Công ty nhận hóa đơn. Backend cũ không gửi khóa thì coi như KHÔNG. */
export function isInvoiceCompanyOnly(
  request: { invoice_company_only?: boolean } | null | undefined,
): boolean {
  return request?.invoice_company_only === true
}

/**
 * Câu chặn lúc lưu / gửi duyệt ở chế độ chỉ sửa công ty: chỉ đòi Công ty nhận hóa đơn. Các
 * ô khác backend bỏ qua nên đừng chặn theo chúng — phiếu cũ thiếu một ô bắt buộc nào đó sẽ
 * không bao giờ gửi duyệt lại được.
 */
export function validateInvoiceCompanyOnly(request: { company_id?: number }): string | null {
  return request.company_id ? null : 'Vui lòng chọn Công ty nhận hóa đơn'
}

/** Thao tác trên ĐMH vẫn mở khi đơn tạm khóa vì YCMH nguồn bị trả về: chỉ xem, in, xuất. */
const PO_ACTIONS_OPEN_WHILE_PR_RETURNED: ReadonlySet<PermissionAction> = new Set<PermissionAction>([
  'read',
  'print',
  'export',
])

/** ĐMH có đang tạm khóa vì YCMH nguồn bị trả về sửa công ty nhận hóa đơn không. */
export function isOrderLockedByPrReturn(
  order: { locked_by_pr_return?: boolean } | null | undefined,
): boolean {
  return order?.locked_by_pr_return === true
}

/** Còn được làm thao tác này trên ĐMH không, xét riêng khóa của duoc-CR-803 (quyền vai trò tính riêng). */
export function isPoActionOpenWhilePrReturned(
  action: PermissionAction,
  lockedByPrReturn: boolean,
): boolean {
  return !lockedByPrReturn || PO_ACTIONS_OPEN_WHILE_PR_RETURNED.has(action)
}

/** Câu nhắc đầu trang ĐMH đang tạm khóa. */
export function buildPrReturnLockNotice(prCode: string): string {
  const code = (prCode || '').trim()
  return `Đơn đang tạm khóa: yêu cầu mua hàng ${code || 'nguồn'} được trả về để sửa công ty nhận hóa đơn, chờ duyệt lại.`
}
