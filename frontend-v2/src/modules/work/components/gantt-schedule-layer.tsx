import { Plus } from 'lucide-react'
import { useRef, useState, type PointerEvent as ReactPointerEvent } from 'react'

import { cn } from '@/shared/utils/cn'
import { BAR_PAD, ROW_HEIGHT } from '../utils/gantt-layout'
import type { GanttTimeline } from '../utils/gantt-scale'

interface GanttScheduleLayerProps {
  timeline: GanttTimeline
  /** Lưu quãng ngày vừa chọn. Hai đầu đã sắp xuôi, `from <= to`. */
  onSchedule: (from: string, to: string) => void
}

/**
 * Lớp XẾP LỊCH phủ hàng của một việc CHƯA CÓ NGÀY — rê chuột vào hiện một ô nét
 * đứt kèm dấu `+`, bấm là đặt một ngày, kéo ngang là đặt cả quãng.
 *
 * Đúng thứ Lark gọi «Schedule task». Không có nó thì việc chưa đặt ngày nằm chết
 * trên biểu đồ: hàng trống trơn, muốn cho nó một cái lịch phải mở panel chi tiết
 * rồi gõ hai ô ngày — trong khi chỗ cần đặt thì đang nhìn thẳng vào.
 *
 * ⚠️ Chỉ dựng cho việc CHƯA có ngày. Việc đã có thanh thì cả hàng là vùng thao
 * tác của chính cái thanh ấy (kéo dời, kéo mép, nối phụ thuộc); chồng thêm một
 * lớp bắt chuột lên trên là mọi cú kéo đều rơi vào lớp này.
 *
 * Ngày tính từ TỌA ĐỘ so với chính lớp phủ (`offsetX / dayWidth`), không đọc
 * `clientX` rồi trừ đi vị trí khung: lớp này nằm trong khung cuộn nên `offsetX`
 * đã tính sẵn phần đã cuộn, còn `clientX` thì phải tự bù — và bù sai một nhịp là
 * lịch lệch vài ngày mà nhìn vẫn "có vẻ đúng".
 */
export function GanttScheduleLayer({ timeline, onSchedule }: GanttScheduleLayerProps) {
  /** Ô đang rê chuột tới. `null` = con trỏ ở ngoài. */
  const [hover, setHover] = useState<number | null>(null)
  /** Ô bắt đầu của cú kéo đang diễn ra. `null` = chưa kéo. */
  const [anchor, setAnchor] = useState<number | null>(null)
  //  Giữ thêm ở ref để `pointerup` đọc được giá trị mới nhất: `onPointerUp` bắn
  //  ngay sau `onPointerMove` cuối cùng, mà state lúc ấy có thể chưa kịp về.
  const cuoi = useRef<{ anchor: number; hover: number } | null>(null)

  function dayIndex(event: ReactPointerEvent<HTMLDivElement>): number {
    const i = Math.floor(event.nativeEvent.offsetX / timeline.dayWidth)
    return Math.min(timeline.days.length - 1, Math.max(0, i))
  }

  function handleMove(event: ReactPointerEvent<HTMLDivElement>) {
    const i = dayIndex(event)
    setHover(i)
    if (anchor !== null) cuoi.current = { anchor, hover: i }
  }

  function handleDown(event: ReactPointerEvent<HTMLDivElement>) {
    //  Chỉ nút TRÁI: chuột phải là menu ngữ cảnh, nút giữa là dán ở Linux —
    //  bắt hết thì người dùng bấm chuột phải cũng thành xếp lịch.
    if (event.button !== 0) return
    const i = dayIndex(event)
    event.currentTarget.setPointerCapture(event.pointerId)
    setAnchor(i)
    cuoi.current = { anchor: i, hover: i }
  }

  function handleUp(event: ReactPointerEvent<HTMLDivElement>) {
    const keo = cuoi.current
    cuoi.current = null
    setAnchor(null)
    if (!keo) return
    event.currentTarget.releasePointerCapture(event.pointerId)

    const [dau, cuoiNgay] = [Math.min(keo.anchor, keo.hover), Math.max(keo.anchor, keo.hover)]
    onSchedule(timeline.days[dau], timeline.days[cuoiNgay])
  }

  const vung = anchor !== null && hover !== null ? [Math.min(anchor, hover), Math.max(anchor, hover)] : null
  const oHien = vung ?? (hover !== null ? [hover, hover] : null)

  return (
    <div
      role="presentation"
      className="absolute inset-0 cursor-cell"
      onPointerMove={handleMove}
      onPointerLeave={() => {
        if (anchor === null) setHover(null)
      }}
      onPointerDown={handleDown}
      onPointerUp={handleUp}
      onPointerCancel={handleUp}
    >
      {oHien && (
        <div
          //  `title` thay cho tooltip riêng: một hàng có thể có hàng trăm ô, gắn
          //  component tooltip vào là bấy nhiêu lớp nổi chờ sẵn.
          title={vung ? 'Thả để đặt lịch' : 'Xếp lịch cho việc này'}
          className={cn(
            'pointer-events-none absolute flex items-center justify-center rounded-[3px] text-[11px] font-medium',
            vung
              ? 'bg-primary/15 text-primary ring-1 ring-primary'
              : 'border border-dashed border-muted-foreground/60 text-muted-foreground',
          )}
          style={{
            left: oHien[0] * timeline.dayWidth,
            width: (oHien[1] - oHien[0] + 1) * timeline.dayWidth,
            top: BAR_PAD,
            height: ROW_HEIGHT - BAR_PAD * 2,
          }}
        >
          {vung ? `${vung[1] - vung[0] + 1} ngày` : <Plus className="size-3.5" />}
        </div>
      )}
    </div>
  )
}
