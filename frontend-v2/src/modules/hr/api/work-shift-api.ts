import { apiDelete, apiGet, apiPost, apiPut } from '@/core/api'
import type {
  MyShiftRange,
  WorkShift,
  WorkShiftBody,
  WorkShiftBulkBody,
  WorkShiftBulkResult,
  WorkShiftCopyWeekBody,
  WorkShiftCopyWeekResult,
} from '../types/work-shift'

/**
 * Lượt ghi hàng loạt tự bày lỗi trong hộp thoại (danh sách ô bị từ chối đọc được), nên tắt toast tự động của
 * `http-client` — không thì người dùng thấy cùng một lỗi hai lần, một lần là câu gộp khó đọc.
 */
//  why: `_silent` là cờ nội bộ của `http-client` (không có trong kiểu axios) — cùng cách `auth-service` truyền.
const SILENT = { _silent: true } as never

/**
 * Xếp ca theo ngày (duoc-CR-761) — `/api/work-shifts`. Quyền và luật ngày do backend chốt. Lưới Xem lịch đọc ca qua
 * ô của `/tools/roster` (khối `shift`), nên ở đây không có hàm đọc danh sách ca.
 */
export const workShiftApi = {
  /** Ca CỦA TÔI từng ngày (mẫu tuần + ca xếp riêng đã gộp). Ai đăng nhập cũng gọi được. */
  getMine: (params: { from_date: string; to_date: string }) =>
    apiGet<MyShiftRange>('/api/work-shifts/me', { params }),
  /** Đặt ca một người một ngày — THAY cả danh sách khung (rỗng = nghỉ cả ngày). */
  save: (employeeId: number, workDate: string, body: WorkShiftBody) =>
    apiPut<WorkShift>(`/api/work-shifts/${employeeId}/${workDate}`, body),
  /** Gỡ ca riêng — ngày đó quay về mẫu lịch tuần. */
  clear: (employeeId: number, workDate: string) =>
    apiDelete<{ deleted: boolean }>(`/api/work-shifts/${employeeId}/${workDate}`),
  /** Áp CÙNG bộ khung cho nhiều người × nhiều ngày; sai một ô là không ghi ô nào. */
  bulk: (body: WorkShiftBulkBody) => apiPost<WorkShiftBulkResult>('/api/work-shifts/bulk', body, SILENT),
  /** Chép ca riêng của tuần nguồn sang tuần đích (thứ Hai → thứ Hai). */
  copyWeek: (body: WorkShiftCopyWeekBody) =>
    apiPost<WorkShiftCopyWeekResult>('/api/work-shifts/copy-week', body, SILENT),
}
