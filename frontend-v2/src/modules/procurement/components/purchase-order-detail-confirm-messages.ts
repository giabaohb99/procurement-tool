import { formatDate } from '@/shared/utils/format-date'
import {
  COST_STAGE_ESTIMATE,
  COST_STAGE_FINAL,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/**
 * Câu của các hộp hỏi lại trên trang chi tiết ĐMH — chép đúng chữ bản v1 (duoc-CR-741), gom
 * về một chỗ thành hàm thuần để bài kiểm đọc được câu mà không phải dựng cả trang.
 */

/** Câu hỏi khi bấm Mở lại một đơn đã Hoàn thành — nguyên văn bản v1. */
export const PO_REOPEN_CONFIRM_MESSAGE =
  'Mở lại đơn đã hoàn thành để xử lý tiếp (nhập Số HĐ, tạo yêu cầu thanh toán, cập nhật tiến độ)? Đơn trở về trạng thái theo tiến độ nhận hàng.'

/**
 * Câu hỏi khi bấm Hoàn thành. Bản v1 LUÔN hỏi (đơn chốt xong là khóa); v2 trước đây chỉ hỏi
 * khi còn nợ chi phí / còn dòng chưa quyết toán. Gộp lại: một hộp duy nhất, câu chính theo v1,
 * hai lời nhắc của v2 (bao-CR-319, bao-CR-453) nối xuống dưới khi đúng trường hợp — vẫn
 * không chặn, chỉ nhắc.
 */
export function buildCompleteConfirmMessage(
  order: Pick<PurchaseOrderDetail, 'status' | 'cost_stage' | 'import_cost_summary'>,
): string {
  const lines = [
    order.status === 'partial'
      ? 'Đơn mới nhận MỘT PHẦN. Xác nhận HOÀN THÀNH (chốt đơn dù còn thiếu)? Sau khi hoàn thành sẽ khóa, không chỉnh sửa được nữa.'
      : 'Xác nhận HOÀN THÀNH đơn mua hàng này? Sau khi hoàn thành sẽ khóa, không chỉnh sửa được nữa.',
  ]
  const remaining = order.import_cost_summary?.remaining_total ?? 0
  if (remaining > 0.01) {
    lines.push(
      `Đơn còn ${remaining.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ chi phí thu mua chưa thanh toán. Công nợ đó vẫn theo dõi được ở phân hệ Tài chính.`,
    )
  }
  const notFinal = order.import_cost_summary?.lines_not_final ?? 0
  if ((order.cost_stage ?? COST_STAGE_ESTIMATE) < COST_STAGE_FINAL && notFinal > 0) {
    lines.push(
      `Còn ${notFinal} dòng chi phí chưa quyết toán. Nên chốt Quyết toán trước khi Hoàn thành.`,
    )
  }
  return lines.join('\n\n')
}

export interface ExpectedDateDiff {
  name: string
  requestDate: string
  orderDate: string
}

/**
 * Các dòng có Ngày dự kiến có hàng LỆCH với YCMH nguồn. Hệ thống không tự sửa ngược lên YCMH
 * (đổi ngày ở đó là việc của NSTM và phải kèm lý do) — chỉ nhắc người đang sửa đơn. Dòng trống
 * (chưa chọn hàng) bị bỏ như lúc lưu; một trong hai ngày trống thì không tính là lệch.
 */
export function findExpectedDateDiffs(items: PurchaseOrderItem[]): ExpectedDateDiff[] {
  return items
    .filter((item) => item.product_name || item.product_code)
    .flatMap((item) => {
      const orderDate = (item.expected_date || '').trim()
      const requestDate = (item.pr_expected_date || '').trim()
      if (!orderDate || !requestDate || orderDate === requestDate) return []
      return [{ name: item.product_name || item.product_code, requestDate, orderDate }]
    })
}

/** Câu của hộp *Lệch ngày dự kiến có hàng* — nguyên văn bản v1. */
export function buildExpectedDateDiffMessage(prCode: string, diffs: ExpectedDateDiff[]): string {
  return (
    `Các dòng sau đang có ngày dự kiến khác với yêu cầu mua hàng ${prCode}:\n` +
    diffs
      .map(
        (diff) =>
          `• ${diff.name}: YCMH ${formatDate(diff.requestDate)} → đơn này ${formatDate(diff.orderDate)}`,
      )
      .join('\n') +
    '\n\nNgày trên YCMH sẽ KHÔNG tự đổi theo. Nếu cần đổi, vào phiếu YCMH sửa (phải kèm lý do).'
  )
}
