import { useMemo, useState } from 'react'
import { Check, CircleSlash, MapPin, Search, Users } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'
import { matchesVietnamese } from '@/shared/utils/vn-text'
import { useMeetingRooms, useRoomAvailability } from '../hooks/use-room'
import type { RoomAvailability } from '../types/room'
import { formatTimeRange } from '../utils/room-time'

interface RoomPickerDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Khung giờ đang chọn, ISO có giây. Rỗng = chưa chọn giờ, không tra được bận/trống. */
  startAt: string
  endAt: string
  selectedId: number
  onSelect: (roomId: number) => void
}

/**
 * HỘP CHỌN PHÒNG — có ô tìm, có trạng thái trống/bận theo đúng khung giờ đang đặt.
 *
 * ⚠️ Thay cho dải chip liệt kê MỌI phòng ở cột phải (khách chê 04/09/2026): với
 * 21 phòng nó thành một cột chip dài hơn cả form, và với 50 phòng thì không dùng
 * được. Danh sách dài thì phải **tìm**, không phải **cuộn**.
 *
 * ⚠️ Phòng bận **vẫn chọn được**, chỉ ghi rõ ai đang giữ tới mấy giờ. Người dùng
 * có thể đang định thương lượng, hoặc đặt trước rồi xin sau; chặn ở đây là bắt
 * họ đoán vì sao không bấm được. Chốt chặn thật nằm ở bước gửi duyệt (backend).
 */
export function RoomPickerDialog({
  open,
  onOpenChange,
  startAt,
  endAt,
  selectedId,
  onSelect,
}: RoomPickerDialogProps) {
  const [keyword, setKeyword] = useState('')
  //  Mặc định GIẤU phòng đang bận — xem `showBusyRooms` bên dưới.
  const [showBusyRooms, setHienCaPhongBan] = useState(false)
  const { data: roomData } = useMeetingRooms(open)
  const { data: availability } = useRoomAvailability(startAt, endAt)

  //  Trạng thái bận/trống tra theo id — `/availability` chỉ trả phòng đang dùng
  //  được, nên phòng nào không có trong đó thì coi như chưa biết (chưa chọn giờ).
  const busyById = useMemo(() => {
    const map = new Map<number, RoomAvailability>()
    for (const row of availability ?? []) map.set(row.room_id, row)
    return map
  }, [availability])

  const matchedRooms = useMemo(() => {
    const all = roomData?.items ?? []
    //  So BỎ DẤU: người Việt gõ ô tìm thường không bỏ dấu, và "tang 3" mà ra 0
    //  phòng thì họ kết luận là danh mục không có — xem `matchesVietnamese`.
    return all.filter((r) =>
      matchesVietnamese([r.name, r.code, r.location, r.equipment], keyword),
    )
  }, [roomData, keyword])

  /**
   * ⚠️ **Chỉ bày phòng ĐANG TRỐNG** trong khung giờ đã chọn (khách chốt
   * 04/09/2026). Hộp này để *chọn phòng đặt được*; phòng đã có người giữ thì
   * chọn vào cũng bị backend chặn lúc gửi duyệt, nên đưa lên đây chỉ tạo nhiễu
   * giữa hai chục dòng.
   *
   * Ba ngoại lệ, đều cần thiết:
   *  · **chưa chọn giờ** → không tra được trống/bận, bày hết còn hơn bày rỗng;
   *  · **phòng đang chọn** luôn hiện, kể cả khi nó bận — biến mất khỏi danh sách
   *    thì người dùng tưởng phòng bị xoá;
   *  · **bấm «Hiện cả phòng đang bận»** → xem đủ, để còn biết nên xin lại phòng
   *    của ai. Số phòng bị giấu nói thành lời, không giấu im.
   */
  const busyMatchedCount = matchedRooms.filter((r) => busyById.get(r.id)?.available === false).length
  const rooms = useMemo(() => {
    if (showBusyRooms || !availability?.length) return matchedRooms
    return matchedRooms.filter(
      (r) => busyById.get(r.id)?.available !== false || r.id === selectedId,
    )
  }, [matchedRooms, busyById, showBusyRooms, availability, selectedId])

  const freeCount = rooms.filter((r) => busyById.get(r.id)?.available !== false).length

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Chọn phòng họp</DialogTitle>
          <DialogDescription>
            {startAt && endAt
              ? `Phòng còn trống trong khung giờ ${formatTimeRange(startAt, endAt)} — ${freeCount} phòng.`
              : 'Chưa chọn khung giờ nên chưa tra được phòng nào trống — đang hiện tất cả.'}
          </DialogDescription>
        </DialogHeader>

        <div className="relative">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            autoFocus
            className="pl-9"
            placeholder="Tìm theo tên phòng, tầng, thiết bị…"
            value={keyword}
            onChange={(e) => setKeyword(e.target.value)}
          />
        </div>

        {/*  Danh sách cuộn TRONG hộp, cao cố định: 50 phòng thì hộp không được
             dài quá màn hình, còn 3 phòng thì không để lại khoảng trống. */}
        <div className="max-h-[52vh] min-h-0 space-y-1.5 overflow-auto pr-1">
          {rooms.length === 0 && (
            <p className="py-8 text-center text-sm text-muted-foreground">
              {keyword
                ? `Không có phòng trống nào khớp «${keyword}».`
                : 'Khung giờ này không còn phòng nào trống.'}
            </p>
          )}

          {rooms.map((room) => {
            const info = busyById.get(room.id)
            const isBusy = info?.available === false
            const isSelected = room.id === selectedId
            return (
              <button
                key={room.id}
                type="button"
                onClick={() => {
                  onSelect(room.id)
                  onOpenChange(false)
                }}
                className={cn(
                  'flex w-full items-center gap-3 rounded-lg border p-3 text-left transition-colors',
                  isSelected
                    ? 'border-primary bg-primary/5 ring-1 ring-primary'
                    : 'hover:bg-accent',
                )}
              >
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate font-medium">{room.name}</span>
                    <span className="shrink-0 rounded bg-muted px-1.5 py-0.5 text-[11px] text-muted-foreground">
                      {room.code}
                    </span>
                  </div>
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
                </div>

                {/*  Trạng thái nói RÕ ai giữ tới mấy giờ — «bận» trần thì người
                     dùng phải đi hỏi vòng quanh mới biết nên dời sang giờ nào. */}
                <div className="shrink-0 text-right text-xs">
                  {isBusy ? (
                    <span className="flex items-center gap-1 text-amber-700 dark:text-amber-400">
                      <CircleSlash className="size-3.5" />
                      {info?.bookings[0]
                        ? `Bận ${formatTimeRange(info.bookings[0].start_at, info.bookings[0].end_at)}`
                        : 'Đã có người giữ'}
                    </span>
                  ) : info ? (
                    <span className="text-emerald-700 dark:text-emerald-400">Còn trống</span>
                  ) : null}
                </div>

                {isSelected && <Check className="size-4 shrink-0 text-primary" />}
              </button>
            )
          })}
        </div>
        {/*  Nói ra số phòng bị giấu. Giấu im thì người dùng đếm thiếu phòng và
             tưởng danh mục hỏng. */}
        {busyMatchedCount > 0 && (
          <button
            type="button"
            className="text-left text-xs text-muted-foreground underline-offset-2 hover:underline"
            onClick={() => setHienCaPhongBan((truoc) => !truoc)}
          >
            {showBusyRooms
              ? `Đang hiện cả ${busyMatchedCount} phòng đang bận — chỉ hiện phòng trống`
              : `${busyMatchedCount} phòng đang bận đã được ẩn — hiện cả chúng`}
          </button>
        )}
      </DialogContent>
    </Dialog>
  )
}
