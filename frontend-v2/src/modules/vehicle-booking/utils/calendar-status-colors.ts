import { BOOKING_STATUS } from '../types/vehicle-booking'

/**
 * Màu chip trên LỊCH đặt xe — mỗi trạng thái một màu riêng, đủ 8 mức.
 *
 * Cố ý KHÔNG dùng `BOOKING_STATUS_TONE` (bảng 5 tông của badge): bảng đó gộp
 * `approved` + `dispatched` vào cùng tông `info`, và `draft` + `cancelled` vào
 * cùng `neutral`. Trên bảng danh sách thì không sao vì đã có chữ ghi rõ bên
 * cạnh, nhưng trên lịch màu là THỨ DUY NHẤT nói trạng thái — mà "Đã duyệt"
 * (chưa có xe) với "Đã điều phối" (đã có xe) lại đúng là khác biệt điều phối
 * viên cần thấy. Nên lịch có bảng màu riêng, rộng hơn.
 *
 * KHAI BẰNG HEX + inline style, cùng lối `components/status-pill.tsx`: đây là
 * palette THIẾT KẾ cố định, không phải token theme, nên không đặt vào
 * `index.css`. Đổi màu lịch thì sửa DUY NHẤT bảng này.
 *
 * Về việc chọn thang màu — đã thử và bỏ HAI thái cực:
 *  - Thang Tailwind `-500` đặc: thanh chuyến nhiều ngày trải 3-5 cột, vài chuyến
 *    chồng nhau là cả tuần thành mảng tím/cam chói.
 *  - Thang `-100` nhạt: chữ giờ trên nền đó mờ gần như mất, lưới trông bệch.
 * Bảng dưới là mid-tone đã giảm bão hoà theo lối palette Google Calendar
 * (Blueberry · Peacock · Basil · Banana · Tomato · Graphite) — đủ đậm để chữ
 * trắng đọc rõ, đủ dịu để không giành mắt với lưới.
 */
export interface CalendarStatusStyle {
  /** Màu nhận dạng của trạng thái: nền thanh nhiều ngày + màu icon. */
  color: string
  /** Gạch ngang tiêu đề — chỉ dùng cho phiếu đã hủy. */
  strikethrough?: boolean
}

export const CALENDAR_STATUS_STYLE: Record<number, CalendarStatusStyle> = {
  [BOOKING_STATUS.draft]: { color: '#78828F' }, // Graphite — chưa gửi, trung tính
  [BOOKING_STATUS.pending]: { color: '#D69B2E' }, // Banana — đang chờ người duyệt
  [BOOKING_STATUS.approved]: { color: '#5C6BC0' }, // Blueberry — duyệt rồi, CHƯA có xe
  [BOOKING_STATUS.dispatched]: { color: '#2E96C9' }, // Peacock — ĐÃ có xe/tài xế
  [BOOKING_STATUS.completed]: { color: '#3B9B6B' }, // Basil — xong chuyến
  [BOOKING_STATUS.rejected]: { color: '#CF5F58' }, // Tomato — bị từ chối
  [BOOKING_STATUS.cancelled]: { color: '#9AA3AE', strikethrough: true }, // Graphite nhạt + gạch
  [BOOKING_STATUS.returned]: { color: '#D4794A' }, // Tangerine — trả về sửa
}

/** Mức mặc định cho trạng thái lạ (backend thêm mã mới mà frontend chưa biết). */
export const CALENDAR_STATUS_FALLBACK: CalendarStatusStyle = { color: '#78828F' }

export function calendarStatusStyle(status: number): CalendarStatusStyle {
  return CALENDAR_STATUS_STYLE[status] ?? CALENDAR_STATUS_FALLBACK
}

/**
 * Chuyến CHƯA ĐIỀU PHỐI — chưa gán cả xe lẫn tài xế.
 *
 * Đọc hai NHÃN chứ không đọc id: `serialize_booking` trả nhãn rỗng khi khóa trỏ
 * vào bản ghi đã xóa, nên nhãn mới là thứ khớp với cái người dùng thật sự thấy.
 */
export function needsDispatch(driverLabel: string, vehicleLabel: string): boolean {
  return !driverLabel && !vehicleLabel
}
