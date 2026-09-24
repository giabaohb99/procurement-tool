import { Info, LayoutGrid, List } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { IconTooltip } from '@/shared/ui/icon-tooltip'
import { cn } from '@/shared/utils/cn'

const SEGMENT_CLASS = 'size-7 text-muted-foreground hover:bg-transparent hover:text-foreground'
const SEGMENT_ACTIVE_CLASS = 'bg-background text-foreground shadow-sm hover:bg-background'

interface FolderViewModeControlsProps {
  isGrid: boolean
  onToggleGrid: (grid: boolean) => void
  detailsOpen: boolean
  onToggleDetails: () => void
}

/**
 * Segmented Danh sách/Lưới + nút bật/tắt khung chi tiết — tách khỏi
 * `folder-view-toolbar.tsx` (Hàng 1 của một thư mục THẬT) để dùng LẠI y
 * nguyên ở `folder-my-drive-panel.tsx` (Hàng 1 của gốc «Thư mục của bạn»,
 * chưa chọn thư mục nào nên không có `folder`/nút «Chia sẻ» để vẽ). Hai nơi
 * PHẢI cùng một khối UI — khác nhau là bộ nhớ chế độ lệch giữa gốc và một
 * thư mục thật, người dùng thấy "tự nhảy chế độ" khi mở/đóng thư mục.
 *
 * Đoạn ĐANG BẬT nổi lên nền `bg-background` + bóng trên rãnh `bg-muted`
 * (kiểu segmented của shadcn Tabs), GIỮ icon Danh sách/Lưới của chính nó.
 * Bản trước thay icon bằng dấu `Check` — người dùng nhìn «✓ ⊞» không đọc ra
 * đang ở chế độ nào (làm lại 24/09/2026).
 */
export function FolderViewModeControls({
  isGrid,
  onToggleGrid,
  detailsOpen,
  onToggleDetails,
}: FolderViewModeControlsProps) {
  return (
    <div className="flex shrink-0 items-center gap-2">
      <div className="flex items-center rounded-md bg-muted p-0.5">
        <IconTooltip label="Danh sách">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-pressed={!isGrid}
            aria-label="Xem dạng danh sách"
            className={cn(SEGMENT_CLASS, !isGrid && SEGMENT_ACTIVE_CLASS)}
            onClick={() => onToggleGrid(false)}
          >
            <List className="size-4" />
          </Button>
        </IconTooltip>
        <IconTooltip label="Lưới">
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            aria-pressed={isGrid}
            aria-label="Xem dạng lưới"
            className={cn(SEGMENT_CLASS, isGrid && SEGMENT_ACTIVE_CLASS)}
            onClick={() => onToggleGrid(true)}
          >
            <LayoutGrid className="size-4" />
          </Button>
        </IconTooltip>
      </div>

      <IconTooltip label="Chi tiết">
        <Button
          type="button"
          variant="outline"
          size="icon-sm"
          aria-pressed={detailsOpen}
          aria-label="Bật/tắt khung chi tiết"
          className={cn(detailsOpen && 'bg-accent')}
          onClick={onToggleDetails}
        >
          <Info className="size-4" />
        </Button>
      </IconTooltip>
    </div>
  )
}
