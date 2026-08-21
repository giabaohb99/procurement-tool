import type { StatusTone } from '@/shared/ui/status-tone'

/**
 * Nhãn + tông màu của phân hệ Phiếu hỗ trợ, tách riêng khỏi các huy hiệu
 * (`ticket-meta.tsx`) để tệp `.tsx` chỉ xuất component — nếu không quy tắc
 * `react-refresh/only-export-components` sẽ cảnh báo.
 *
 * Nhãn khớp `backend/app/modules/ticket/service.py`. Màu quy về bảng tông dùng
 * chung (`status-tone.ts`) thay cho hex một-lần như bản cũ — bốn tình huống của
 * phiếu ánh xạ gọn vào bốn tông sẵn có, giữ đúng bảng màu v1 (Mới xanh dương,
 * Đang xử lý vàng cam, Đã trả lời xanh lá, Đã đóng xám).
 */

export const TICKET_STATUS_TONE: Record<string, StatusTone> = {
  open: 'progress',
  in_progress: 'pending',
  answered: 'done',
  closed: 'neutral',
}

export const TICKET_STATUS_LABELS: Record<string, string> = {
  open: 'Mới',
  in_progress: 'Đang xử lý',
  answered: 'Đã trả lời',
  closed: 'Đã đóng',
}

export const TICKET_PRIORITY_TONE: Record<string, StatusTone> = {
  low: 'neutral',
  normal: 'progress',
  high: 'pending',
  urgent: 'danger',
}

export const TICKET_PRIORITY_LABELS: Record<string, string> = {
  low: 'Thấp',
  normal: 'Trung bình',
  high: 'Cao',
  urgent: 'Khẩn',
}

/** Dựng danh sách ô chọn từ bảng nhãn — một nguồn sự thật, không chép tay hai lần. */
function toOptions(labels: Record<string, string>): { value: string; label: string }[] {
  return Object.entries(labels).map(([value, label]) => ({ value, label }))
}

/** Ô chọn trạng thái ở thanh công cụ danh sách (chưa gồm nhánh "tất cả"). */
export const TICKET_STATUS_OPTIONS = toOptions(TICKET_STATUS_LABELS)

/** Ô chọn mức ưu tiên ở thanh công cụ danh sách. */
export const TICKET_PRIORITY_OPTIONS = toOptions(TICKET_PRIORITY_LABELS)
