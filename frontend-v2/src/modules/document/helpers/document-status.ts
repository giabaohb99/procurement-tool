import type { DocumentRecord } from '../types/document-record'
import { STATUS_LABELS } from '../types/document-record'

/** Nhãn hiệu lực hiện trên danh sách và trang chi tiết. */
export interface EffectiveLabel {
  text: string
  /** Biến thể của `<Badge>`. */
  variant: 'default' | 'secondary' | 'outline' | 'destructive'
}

/**
 * Nhãn hiệu lực THỰC TẾ của văn bản.
 *
 * "Hết hiệu lực" tính từ `effective_to` chứ không lưu thành trạng thái: lưu thì
 * mỗi ngày phải có người (hoặc một job) chạy quét cả bảng để đổi trạng thái, mà
 * quên một hôm là cả hệ báo sai.
 */
export function effectiveLabel(
  record: Pick<DocumentRecord, 'status' | 'effective_from' | 'effective_to'>,
  today = new Date(),
): EffectiveLabel {
  if (record.status !== 'effective') {
    return {
      text: STATUS_LABELS[record.status],
      variant: record.status === 'revoked' ? 'destructive' : 'secondary',
    }
  }

  const now = startOfDay(today)
  const from = record.effective_from ? startOfDay(new Date(record.effective_from)) : null
  const to = record.effective_to ? startOfDay(new Date(record.effective_to)) : null

  if (to && to < now) return { text: 'Hết hiệu lực', variant: 'secondary' }
  if (from && from > now) return { text: 'Chưa hiệu lực', variant: 'outline' }
  return { text: 'Còn hiệu lực', variant: 'default' }
}

/** Bỏ phần giờ để so sánh theo NGÀY — văn bản chỉ tính hiệu lực theo ngày. */
function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}
