import { apiDelete, apiGet, apiPatch, apiPost } from '@/core/api'
import type { ListParams, PaginatedResult } from '@/shared/types/api'
import type {
  MeetingRoom,
  RoomAvailability,
  RoomBooking,
  RoomBookingAttendee,
  RoomBookingPayload,
  RoomInboxRow,
} from '../types/room'

/** Tầng API của Đặt phòng họp — chỉ gọi HTTP, không chứa logic React. */

const BOOKINGS = '/api/room-bookings'
const INBOX = '/api/room-bookings/inbox'
const ROOMS = '/api/meeting-rooms'

export const roomApi = {
  // ── Phiếu đặt ───────────────────────────────────────────────────────────────
  listBookings: (params: ListParams) =>
    apiGet<PaginatedResult<RoomBooking>>(BOOKINGS, { params }),

  getBooking: (id: number) => apiGet<RoomBooking>(`${BOOKINGS}/${id}`),

  createBooking: (values: RoomBookingPayload) => apiPost<RoomBooking>(BOOKINGS, values),

  updateBooking: (id: number, values: Partial<RoomBookingPayload>) =>
    apiPatch<RoomBooking>(`${BOOKINGS}/${id}`, values),

  /**
   * Dời giờ / đổi phòng — đường riêng của thao tác KÉO THẢ trên màn Lịch.
   *
   * ⚠️ Không dùng `updateBooking` cho việc này: `PATCH /{id}` chỉ nhận phiếu
   * CHƯA vào luồng, mà lịch thì chỉ vẽ phiếu ĐÃ vào luồng — gọi nhầm là mọi cú
   * kéo đều trả về "Phiếu đã gửi duyệt nên không sửa được".
   */
  rescheduleBooking: (id: number, values: { room_id: number; start_at: string; end_at: string }) =>
    apiPatch<RoomBooking>(`${BOOKINGS}/${id}/reschedule`, values),

  deleteBooking: (id: number) => apiDelete(`${BOOKINGS}/${id}`),

  submitBooking: (id: number) => apiPost<RoomBooking>(`${BOOKINGS}/${id}/submit`, {}),

  /** Duyệt THẲNG — chỉ chạy khi phiếu chưa có luồng nhiều bước. */
  approveBooking: (id: number) => apiPost<RoomBooking>(`${BOOKINGS}/${id}/approve`, {}),

  rejectBooking: (id: number, reason: string) =>
    apiPost<RoomBooking>(`${BOOKINGS}/${id}/reject?reason=${encodeURIComponent(reason)}`, {}),

  cancelBooking: (id: number, reason: string) =>
    apiPost<RoomBooking>(`${BOOKINGS}/${id}/cancel?reason=${encodeURIComponent(reason)}`, {}),

  listAttendees: (id: number) => apiGet<RoomBookingAttendee[]>(`${BOOKINGS}/${id}/attendees`),

  /**
   * Phòng nào trống trong khoảng này. **Cảnh báo sớm**, không phải chốt chặn —
   * chốt thật nằm ở bước gửi duyệt phía backend.
   */
  availability: (startAt: string, endAt: string, companyId = 0) =>
    apiGet<RoomAvailability[]>(`${BOOKINGS}/availability`, {
      params: { start_at: startAt, end_at: endAt, company_id: companyId },
    }),

  // ── Hộp việc duyệt ──────────────────────────────────────────────────────────
  //  Hai đường này KHÔNG gác theo khóa vai trò: quyền ở đây là «bộ máy có giao
  //  việc cho tôi không» — xem docstring của `inbox_controller.py`.
  toApprove: () => apiGet<{ total: number; items: RoomInboxRow[] }>(`${INBOX}/to-approve`),

  handled: (days = 30) =>
    apiGet<{ total: number; items: RoomInboxRow[] }>(`${INBOX}/handled`, { params: { days } }),

  // ── Danh mục phòng ──────────────────────────────────────────────────────────
  listRooms: (params: ListParams = {}) =>
    apiGet<PaginatedResult<MeetingRoom>>(ROOMS, {
      //  Ô chọn phòng cần cả danh sách trong một lượt: phòng họp của một công ty
      //  đếm bằng đầu ngón tay, phân trang ở đây chỉ tổ phải bấm "trang sau".
      //
      //  Sắp theo `sort_order` chứ không để mặc định (id giảm dần): thứ tự cột
      //  trên lịch là thứ tự người quản trị đã xếp, phòng hay dùng để lên đầu.
      params: { page_size: 200, sort_by: 'sort_order', sort_dir: 'asc', ...params },
    }),
}
