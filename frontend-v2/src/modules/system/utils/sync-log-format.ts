import type { TONE_CLASS } from '@/shared/ui/status-tone'

import { SYNC_STATUS } from '../api/sync-log-api'

type Tone = keyof typeof TONE_CLASS

/**
 * Màu cho trạng thái một dòng sổ đồng bộ.
 *
 * *Bỏ qua* cố ý là XÁM chứ không xanh: về kỹ thuật nó là kết cục êm (không có
 * gì thay đổi, hoặc cầu dao đang tắt), nhưng tô xanh thì một màn hình toàn dòng
 * *bỏ qua* nhìn y hệt một màn hình toàn dòng *thành công* — trong khi hai tình
 * huống đó trả lời hai câu hỏi khác hẳn nhau ("đồng bộ có chạy không" và "đồng
 * bộ có ghi được gì không").
 */
export function syncStatusTone(status: number): Tone {
  switch (status) {
    case SYNC_STATUS.SUCCESS:
      return 'done'
    case SYNC_STATUS.FAILED:
      return 'danger'
    case SYNC_STATUS.RUNNING:
      return 'active'
    case SYNC_STATUS.PENDING:
      return 'pending'
    default:
      return 'neutral'
  }
}

/**
 * Ba số đếm của một dòng LƯỢT CHẠY, gộp thành một ô đọc được.
 *
 * Lượt chạy không kéo về gì cả là chuyện thường (ba phút một lần, phần lớn lần
 * không có phiếu nào đổi) — trả về chuỗi gạch ngang để mắt lướt qua, thay vì
 * "0 / 0 / 0" nhìn như một lỗi.
 */
export function runCountsText(fetched: number, written: number, skipped: number): string {
  if (!fetched && !written && !skipped) return '—'
  return `${fetched} kéo · ${written} ghi · ${skipped} bỏ`
}

/**
 * Rút gọn câu lỗi nguyên văn cho ô trong bảng.
 *
 * Cắt theo DÒNG ĐẦU trước rồi mới cắt theo độ dài: câu lỗi của Python thường là
 * một khối traceback nhiều dòng mà dòng đầu đã nói đủ loại lỗi. Cắt thẳng theo
 * ký tự thì ô nào cũng hiện mấy chữ "Traceback (most recent call last)".
 */
export function shortMessage(message: string, limit = 120): string {
  const firstLine = (message || '').split('\n')[0].trim()
  if (!firstLine) return ''
  return firstLine.length > limit ? `${firstLine.slice(0, limit)}…` : firstLine
}
