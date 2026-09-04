import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { queryKeys } from '@/shared/constants/query-keys'
import type { ListParams } from '@/shared/types/api'
import { roomApi } from '../api/room-api'
import type { RoomBookingPayload } from '../types/room'
import { toApiTime } from '../utils/room-time'

/**
 * Hook của ĐẶT PHÒNG HỌP.
 *
 * ⚠️ Mọi lượt ghi đều dọn cả nhánh `queryKeys.hr.all`, không dọn lẻ từng khóa.
 * Một phiếu xuất hiện ở BA chỗ đọc cùng dữ liệu — danh sách phiếu, lịch đặt
 * phòng, và ô «phòng trống» trên form đang mở — nên dọn lẻ là chắc chắn có màn
 * hiện phòng còn trống trong khi nó vừa bị giữ.
 */

function useInvalidateRooms() {
  const queryClient = useQueryClient()
  return () => void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
}

export function useRoomBookings(params: ListParams = {}, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.roomBookings(params),
    queryFn: () => roomApi.listBookings(params),
    enabled,
  })
}

export function useRoomBooking(id: number) {
  return useQuery({
    queryKey: queryKeys.hr.roomBooking(id),
    queryFn: () => roomApi.getBooking(id),
    enabled: id > 0,
  })
}

export function useMeetingRooms(enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.meetingRooms(),
    queryFn: () => roomApi.listRooms(),
    //  Danh mục phòng đổi vài lần một năm; hỏi lại mỗi lần mở form là phí.
    staleTime: 5 * 60 * 1000,
    enabled,
  })
}

/**
 * Phòng trống trong một khoảng giờ. `enabled` tắt khi chưa chọn đủ giờ — gọi
 * với khoảng rỗng thì backend trả 400 và người dùng ăn toast đỏ ngay lúc mới
 * mở form.
 */
export function useRoomAvailability(startAt: string, endAt: string, companyId = 0) {
  return useQuery({
    queryKey: queryKeys.hr.roomAvailability(startAt, endAt, companyId),
    queryFn: () => roomApi.availability(startAt, endAt, companyId),
    enabled: Boolean(startAt && endAt && startAt < endAt),
  })
}

/** Phiếu đang chờ CHÍNH TÔI ký — tab «Cần tôi duyệt». */
export function useRoomToApprove(enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.roomToApprove(),
    queryFn: () => roomApi.toApprove(),
    //  Người khác duyệt xong thì việc biến khỏi hộp của mình — hỏi lại khi quay
    //  về tab là đủ, không cần nhịp đều.
    refetchOnWindowFocus: true,
    enabled,
  })
}

/** Phiếu chính tôi vừa quyết định — tab «Tôi đã duyệt». */
export function useRoomHandled(days = 30, enabled = true) {
  return useQuery({
    queryKey: queryKeys.hr.roomHandled({ days }),
    queryFn: () => roomApi.handled(days),
    enabled,
  })
}

export function useSaveRoomBooking() {
  const invalidate = useInvalidateRooms()
  return useMutation({
    mutationFn: ({ id, values }: { id?: number; values: RoomBookingPayload }) =>
      id ? roomApi.updateBooking(id, values) : roomApi.createBooking(values),
    onSuccess: (_data, variables) => {
      toast.success(variables.id ? 'Đã cập nhật phiếu' : 'Đã lưu phiếu đặt phòng')
      invalidate()
    },
  })
}

/**
 * DỜI LỊCH bằng kéo thả. Trạng thái phiếu giữ nguyên — xem `service.reschedule`.
 *
 * Không báo toast lúc thành công: người dùng vừa nhìn khối rơi đúng chỗ mình
 * thả, một hộp thông báo nói lại điều đó chỉ là tiếng ồn — và kéo vài khối liên
 * tiếp thì chồng lên nhau kín góc màn. Hỏng thì vẫn phải báo: khối sẽ **bật về
 * chỗ cũ** sau lượt nạp lại, và không có câu lỗi thì đó là một cú nhảy không
 * lời giải thích.
 */
export function useRescheduleRoomBooking() {
  const invalidate = useInvalidateRooms()
  return useMutation({
    mutationFn: ({ id, roomId, start, end }: {
      id: number
      roomId: number
      start: string
      end: string
    }) =>
      roomApi.rescheduleBooking(id, {
        room_id: roomId,
        start_at: toApiTime(start),
        end_at: toApiTime(end),
      }),
    onSuccess: () => invalidate(),
    //  ⚠️ KHÔNG gọi `toast.error` ở đây — `http-client` đã tự báo lỗi cho mọi
    //  lệnh không phải GET. Báo thêm lần nữa là hai hộp chữ y hệt nhau chồng
    //  lên nhau (đo được 04/09/2026 khi kéo một phiếu vào khung đã có người).
    //  Vẫn phải nạp lại: khối đang nằm ở chỗ mới trên màn, dữ liệu thì không đổi.
    onError: () => invalidate(),
  })
}

export function useDeleteRoomBooking() {
  const invalidate = useInvalidateRooms()
  return useMutation({
    mutationFn: (id: number) => roomApi.deleteBooking(id),
    onSuccess: () => {
      toast.success('Đã xóa phiếu')
      invalidate()
    },
  })
}

export type RoomBookingAction = 'submit' | 'approve' | 'reject' | 'cancel'

const ACTION_LABELS: Record<RoomBookingAction, string> = {
  submit: 'Đã gửi duyệt',
  approve: 'Đã duyệt phiếu',
  reject: 'Đã từ chối phiếu',
  cancel: 'Đã hủy phiếu',
}

/**
 * Bốn thao tác trên chính TỜ PHIẾU (khác `useApprovalAction` — cái kia bấm vào
 * PHIÊN DUYỆT của bộ máy). Đừng gọi nhầm: `approve`/`reject` ở đây là đường
 * duyệt THẲNG, chỉ chạy khi phiếu chưa có luồng nhiều bước, và backend chặn nếu
 * phiếu đang trong luồng.
 */
export function useRoomBookingAction() {
  const invalidate = useInvalidateRooms()
  return useMutation({
    mutationFn: ({ id, action, reason = '' }: {
      id: number
      action: RoomBookingAction
      reason?: string
    }) => {
      if (action === 'submit') return roomApi.submitBooking(id)
      if (action === 'approve') return roomApi.approveBooking(id)
      if (action === 'reject') return roomApi.rejectBooking(id, reason)
      return roomApi.cancelBooking(id, reason)
    },
    onSuccess: (_data, variables) => {
      toast.success(ACTION_LABELS[variables.action])
      invalidate()
    },
  })
}
