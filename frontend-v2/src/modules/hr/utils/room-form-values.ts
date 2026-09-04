import type { RoomBooking, RoomBookingPayload } from '../types/room'
import { defaultSlot, fromApiTime, toApiTime } from './room-time'

/**
 * Giá trị của form đặt phòng — tách khỏi component để kiểm được bằng test và
 * để trang chi tiết không phải tự nhớ cách dựng payload.
 */
export interface RoomBookingFormValues {
  roomId: number
  title: string
  /** Dạng `datetime-local` (`2026-09-10T09:00`), giờ ĐỊA PHƯƠNG. */
  startAt: string
  endAt: string
  attendeeCount: number
  purpose: string
  attendeeIds: number[]
}

export function emptyRoomForm(now: Date = new Date()): RoomBookingFormValues {
  const slot = defaultSlot(now)
  return {
    roomId: 0,
    title: '',
    startAt: slot.start,
    endAt: slot.end,
    attendeeCount: 0,
    purpose: '',
    attendeeIds: [],
  }
}

export function formValuesOf(booking: RoomBooking): RoomBookingFormValues {
  return {
    roomId: booking.room_id,
    title: booking.title,
    startAt: fromApiTime(booking.start_at),
    endAt: fromApiTime(booking.end_at),
    attendeeCount: booking.attendee_count,
    purpose: booking.purpose,
    attendeeIds: (booking.attendees ?? []).map((a) => a.employee_id),
  }
}

export function toRoomPayload(values: RoomBookingFormValues): RoomBookingPayload {
  return {
    room_id: values.roomId,
    title: values.title.trim(),
    start_at: toApiTime(values.startAt),
    end_at: toApiTime(values.endAt),
    purpose: values.purpose.trim(),
    attendee_count: values.attendeeCount,
    //  Luôn gửi mảng, kể cả rỗng: backend ghi đè danh sách người dự theo đúng
    //  thứ gửi lên, nên bỏ trống trường này khi người dùng vừa XÓA hết người
    //  được mời sẽ giữ nguyên danh sách cũ.
    attendees: values.attendeeIds.map((id) => ({ employee_id: id })),
  }
}

/**
 * Thiếu gì thì chưa gửi duyệt được. Trả câu nói thẳng ra thiếu gì, không trả cờ
 * boolean — nút mờ đi mà không nói vì sao là kiểu chặn khó chịu nhất.
 */
export function missingBeforeSubmit(values: RoomBookingFormValues): string {
  if (!values.title.trim()) return 'Thiếu «Nội dung cuộc họp»'
  if (!values.roomId) return 'Chưa chọn phòng họp'
  if (!values.startAt || !values.endAt) return 'Chưa chọn khung giờ'
  if (values.endAt <= values.startAt) return '«Kết thúc» phải sau «Bắt đầu»'
  return ''
}
