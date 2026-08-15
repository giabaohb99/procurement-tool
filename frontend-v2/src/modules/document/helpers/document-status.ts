import {
  DOCUMENT_STATUS,
  STATUS_LABELS,
  STATUS_VARIANTS,
  type DocumentRecord,
} from '../types/document-record'

/** Nhãn hiệu lực hiện trên danh sách và trang chi tiết. */
export interface EffectiveLabel {
  text: string
  /** Biến thể của `<Badge>`. */
  variant: 'default' | 'secondary' | 'outline' | 'destructive'
}

/**
 * Nhãn hiệu lực THỰC TẾ của văn bản.
 *
 * "Hết hiệu lực theo ngày" và "chưa tới ngày hiệu lực" tính lúc HIỂN THỊ chứ
 * không lưu thành trạng thái: lưu thì mỗi ngày phải có ai đó (hoặc một tác vụ)
 * quét cả bảng để đổi, mà quên một hôm là cả hệ báo sai.
 *
 * Khác với việc CHUYỂN BẢN ĐANG DÙNG khi tới ngày — việc đó có đổi dữ liệu thật
 * và do backend làm (`service.activate_due_versions`).
 */
export function effectiveLabel(
  record: Pick<DocumentRecord, 'status' | 'effective_date' | 'expire_date'>,
  today = new Date(),
): EffectiveLabel {
  const fallback = {
    text: STATUS_LABELS[record.status] ?? String(record.status),
    variant: STATUS_VARIANTS[record.status] ?? 'secondary',
  } satisfies EffectiveLabel

  if (record.status !== DOCUMENT_STATUS.effective) return fallback

  const now = startOfDay(today)
  const from = record.effective_date ? startOfDay(new Date(record.effective_date)) : null
  const to = record.expire_date ? startOfDay(new Date(record.expire_date)) : null

  if (to && to < now) return { text: 'Hết hiệu lực', variant: 'secondary' }
  if (from && from > now) return { text: 'Chưa hiệu lực', variant: 'outline' }
  return { text: 'Có hiệu lực', variant: 'default' }
}

/** Bỏ phần giờ để so sánh theo NGÀY — văn bản chỉ tính hiệu lực theo ngày. */
function startOfDay(date: Date): Date {
  return new Date(date.getFullYear(), date.getMonth(), date.getDate())
}
