import { CalendarCheck, ChevronLeft, ChevronRight } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { ZOOM_LABELS, type GanttZoom } from '../utils/gantt-scale'

interface GanttTimelineControlsProps {
  zoom: GanttZoom
  onZoomChange: (zoom: GanttZoom) => void
  /** Cuộn trục thời gian: `-1` lùi một trang, `1` tiến một trang. */
  onStep: (direction: -1 | 1) => void
  onToday: () => void
}

/**
 * Cụm điều khiển trục thời gian — **mức phóng · Hôm nay · lùi/tiến**, đúng cụm
 * Lark đặt ở góc phải phía trên biểu đồ.
 *
 * Vì sao mức phóng dời từ hàng tab sang đây: nó chỉ có nghĩa với Gantt, mà đứng
 * cạnh ba tab khung nhìn thì nhìn như tab thứ tư. Về đây thì cả ba nút cùng nói
 * về một thứ — cửa sổ thời gian đang nhìn — và nằm ngay trên chính cái trục
 * chúng điều khiển.
 *
 * Nút **Hôm nay** không thừa dù biểu đồ đã tự cuộn tới hôm nay lúc mở: cuộn đi
 * xem quý sau rồi muốn quay về thì cách duy nhất là kéo ngược, mà ở mức phóng
 * Ngày thì một quý dài cả nghìn pixel.
 */
export function GanttTimelineControls({
  zoom,
  onZoomChange,
  onStep,
  onToday,
}: GanttTimelineControlsProps) {
  return (
    <div className="flex items-center gap-1">
      <Select value={zoom} onValueChange={(v) => onZoomChange(v as GanttZoom)}>
        {/*  Ô chọn KHÔNG viền, nền trong: nó nằm ngay trên dải tiêu đề nên một
             cái hộp viền quanh chữ "Ngày" là thêm một khung trong khung — mà ba
             nút cạnh nó đều không có viền. */}
        <SelectTrigger
          size="sm"
          aria-label="Mức phóng trục thời gian"
          className="w-24 border-0 bg-transparent shadow-none hover:bg-accent dark:bg-transparent"
        >
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {(Object.keys(ZOOM_LABELS) as GanttZoom[]).map((z) => (
            <SelectItem key={z} value={z}>
              {ZOOM_LABELS[z]}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      <span aria-hidden className="mx-1 h-5 w-px bg-border" />

      <Button variant="ghost" size="sm" className="px-2.5" onClick={onToday}>
        <CalendarCheck className="size-4" />
        Hôm nay
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Lùi lại một trang"
        onClick={() => onStep(-1)}
      >
        <ChevronLeft className="size-4" />
      </Button>
      <Button
        variant="ghost"
        size="icon-sm"
        aria-label="Tiến tới một trang"
        onClick={() => onStep(1)}
      >
        <ChevronRight className="size-4" />
      </Button>
    </div>
  )
}
