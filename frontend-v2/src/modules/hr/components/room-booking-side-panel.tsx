import { AlertTriangle, CalendarClock, DoorOpen, Timer, Users } from 'lucide-react'

import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { cn } from '@/shared/utils/cn'
import { useMeetingRooms } from '../hooks/use-room'
import type { RoomBookingFormValues } from '../utils/room-form-values'
import { formatTimeRange, minutesBetween } from '../utils/room-time'

interface RoomBookingSidePanelProps {
  value: RoomBookingFormValues
}

/**
 * CỘT PHẢI của màn đặt phòng: chọn phòng + soi lại phiếu trước khi gửi.
 *
 * Sinh ra ngày 04/09/2026 vì bản đầu đổ hết vào một cột chạy suốt bề ngang màn
 * hình: trên màn 2200px mỗi ô nhập dài hơn hai gang tay, mắt phải quét ngang cả
 * mét để đi từ nhãn sang giá trị, còn nửa dưới trang thì trắng trơn.
 *
 * Chia hai cột theo đúng hai việc: bên trái **nhập**, bên phải **soi lại** (họp
 * bao lâu · có quá sức chứa không). Cột phải dính khi cuộn nên cảnh báo không
 * trôi khỏi tầm mắt lúc người dùng đang gõ ở dưới.
 *
 * ⚠️ Việc CHỌN PHÒNG đã rời khỏi đây (04/09/2026): dải chip liệt kê mọi phòng
 * dài hơn cả form khi công ty có 21 phòng, và nó lặp lại ô chọn phòng bên trái.
 * Nay chỉ còn MỘT chỗ chọn phòng — `RoomPickerField` trong form.
 */
export function RoomBookingSidePanel({ value }: RoomBookingSidePanelProps) {
  const { data: roomData } = useMeetingRooms()
  const room = roomData?.items.find((r) => r.id === value.roomId)

  const durationMinutes = value.startAt && value.endAt
    ? minutesBetween(`${value.startAt}:00`, `${value.endAt}:00`)
    : 0
  const isOverCapacity = Boolean(room?.capacity && value.attendeeCount > room.capacity)

  return (
    <div className="space-y-4 lg:sticky lg:top-20">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Phiếu này</CardTitle>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <Row icon={DoorOpen} label="Phòng">
            {room ? (
              <span className="font-medium">{room.name}</span>
            ) : (
              <span className="text-muted-foreground">Chưa chọn</span>
            )}
          </Row>

          <Row icon={CalendarClock} label="Khung giờ">
            {value.startAt && value.endAt && value.endAt > value.startAt ? (
              <span className="font-medium tabular-nums">
                {formatTimeRange(`${value.startAt}:00`, `${value.endAt}:00`)}
              </span>
            ) : (
              <span className="text-muted-foreground">Chưa hợp lệ</span>
            )}
          </Row>

          <Row icon={Timer} label="Thời lượng">
            {durationMinutes > 0 ? (
              <span className="tabular-nums">
                {Math.floor(durationMinutes / 60) ? `${Math.floor(durationMinutes / 60)} giờ ` : ''}
                {durationMinutes % 60 ? `${durationMinutes % 60} phút` : ''}
              </span>
            ) : (
              <span className="text-muted-foreground">—</span>
            )}
          </Row>

          <Row icon={Users} label="Người dự">
            <span className={cn('tabular-nums', isOverCapacity && 'font-semibold text-destructive')}>
              {value.attendeeCount || 0}
              {room?.capacity ? ` / ${room.capacity} chỗ` : ''}
            </span>
          </Row>

          {value.attendeeIds.length > 0 && (
            <p className="text-xs text-muted-foreground">
              Đã mời đích danh {value.attendeeIds.length} người — họ nhận thông báo sau khi
              phiếu được duyệt.
            </p>
          )}

          {/*  Cảnh báo sức chứa đứng ở ĐÂY chứ không nằm cạnh ô nhập: người dùng
               gõ số người trước rồi mới chọn phòng, nên lỗi chỉ lộ ra khi ghép
               hai thứ lại — mà chỗ ghép chính là thẻ tóm tắt này. */}
          {isOverCapacity && (
            <p className="flex items-start gap-1.5 rounded-md border border-destructive/40 bg-destructive/10 p-2 text-xs text-destructive">
              <AlertTriangle className="mt-px size-3.5 shrink-0" />
              Vượt sức chứa của {room?.name}. Phiếu sẽ bị chặn lúc lưu — chọn phòng lớn hơn
              hoặc sửa lại số người.
            </p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

function Row({
  icon: Icon,
  label,
  children,
}: {
  icon: typeof DoorOpen
  label: string
  children: React.ReactNode
}) {
  return (
    <div className="flex items-center justify-between gap-3">
      <span className="flex items-center gap-1.5 text-muted-foreground">
        <Icon className="size-3.5" />
        {label}
      </span>
      <span className="min-w-0 truncate text-right">{children}</span>
    </div>
  )
}
