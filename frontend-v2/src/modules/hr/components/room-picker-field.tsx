import { useState } from 'react'
import { CircleSlash, DoorOpen, MapPin, Users } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { useMeetingRooms, useRoomAvailability } from '../hooks/use-room'
import { formatTimeRange } from '../utils/room-time'
import { RoomPickerDialog } from './room-picker-dialog'

interface RoomPickerFieldProps {
  roomId: number
  onChange: (roomId: number) => void
  /** Khung giờ đang chọn, ISO có giây — để hiện phòng đang bận hay trống. */
  startAt: string
  endAt: string
  /**
   * Phòng đã được xác định từ trước (bấm ô trống trên LỊCH). Lúc đó **không bày
   * bộ chọn ra nữa**: người dùng vừa chỉ tay vào đúng phòng đúng giờ, dí thêm
   * hai chục phòng khác vào mặt họ là hỏi lại một câu đã trả lời rồi. Vẫn đổi
   * được, nhưng phải bấm «Đổi phòng» — một chủ ý rõ ràng.
   */
  lockedFromCalendar?: boolean
}

/**
 * Ô CHỌN PHÒNG trên form đặt.
 *
 * ⚠️ Thay cho `<Select>` 21 dòng + dải chip ở cột phải (khách chê 04/09/2026):
 * hai chỗ làm cùng một việc, và cả hai đều không tìm được. Ở đây là **một thẻ
 * phòng** đọc được ngay (tên · tầng · sức chứa · trạng thái theo khung giờ), bấm
 * vào mở hộp chọn có ô tìm.
 */
export function RoomPickerField({
  roomId,
  onChange,
  startAt,
  endAt,
  lockedFromCalendar = false,
}: RoomPickerFieldProps) {
  const [open, setOpen] = useState(false)
  const { data: roomData } = useMeetingRooms()
  const { data: availability } = useRoomAvailability(startAt, endAt)

  const room = roomData?.items.find((r) => r.id === roomId)
  const info = availability?.find((r) => r.room_id === roomId)
  const isBusy = info?.available === false

  return (
    <>
      {room ? (
        <div
          className={cn(
            'flex items-center gap-3 rounded-lg border p-3',
            isBusy ? 'border-amber-300 bg-amber-50/60 dark:bg-amber-950/30' : 'bg-muted/30',
          )}
        >
          <DoorOpen className="size-5 shrink-0 text-muted-foreground" />

          <div className="min-w-0 flex-1">
            <p className="flex items-center gap-2 truncate font-medium">
              {room.name}
              {/*  Nói ra VÌ SAO ô này đã điền sẵn. Không có dòng này thì người
                   dùng mở form ra thấy một phòng tự nhiên nằm đó và không chắc
                   mình có chọn nhầm hay không. */}
              {lockedFromCalendar && (
                <span className="shrink-0 rounded bg-primary/10 px-1.5 py-0.5 text-[11px] font-normal text-primary">
                  chọn từ lịch
                </span>
              )}
            </p>
            <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-0.5 text-xs text-muted-foreground">
              {room.location ? (
                <span className="flex items-center gap-1">
                  <MapPin className="size-3" />
                  {room.location}
                </span>
              ) : null}
              {room.capacity ? (
                <span className="flex items-center gap-1">
                  <Users className="size-3" />
                  {room.capacity} chỗ
                </span>
              ) : null}
              {room.equipment ? <span className="truncate">{room.equipment}</span> : null}
            </div>

            {isBusy && (
              <p className="mt-1 flex items-center gap-1 text-xs text-amber-700 dark:text-amber-400">
                <CircleSlash className="size-3.5" />
                {info?.bookings[0]
                  ? `Đã có phiếu ${info.bookings[0].code} giữ ${formatTimeRange(
                      info.bookings[0].start_at,
                      info.bookings[0].end_at,
                    )} — gửi duyệt sẽ bị chặn.`
                  : 'Phòng này đã có người giữ trong khung giờ đã chọn.'}
              </p>
            )}
          </div>

          <Button type="button" variant="outline" size="sm" onClick={() => setOpen(true)}>
            Đổi phòng
          </Button>
        </div>
      ) : (
        //  Chưa có phòng (vào từ nút «Đặt phòng»): một nút mở bộ chọn, không
        //  phải một ô select rỗng — nút nói rõ bấm vào sẽ được gì.
        <Button
          type="button"
          variant="outline"
          className="h-auto w-full justify-start gap-3 p-3 text-left font-normal"
          onClick={() => setOpen(true)}
        >
          <DoorOpen className="size-5 text-muted-foreground" />
          <span className="flex-1">
            <span className="block font-medium">Chọn phòng họp</span>
            <span className="block text-xs text-muted-foreground">
              {startAt && endAt
                ? `Còn ${(availability ?? []).filter((r) => r.available).length}/${
                    (availability ?? []).length
                  } phòng trống ở khung giờ này`
                : 'Chọn khung giờ trước để biết phòng nào còn trống'}
            </span>
          </span>
        </Button>
      )}

      {/*  Vào từ lịch thì bộ chọn chỉ mở khi người dùng CHỦ ĐỘNG bấm «Đổi phòng» —
           xem `lockedFromCalendar`. Ở đây cờ đó không chặn gì thêm, nó chỉ có
           nghĩa là ta KHÔNG tự bung hộp chọn lúc mở trang. */}
      <RoomPickerDialog
        open={open}
        onOpenChange={setOpen}
        startAt={startAt}
        endAt={endAt}
        selectedId={roomId}
        onSelect={onChange}
      />
    </>
  )
}
