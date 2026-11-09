import { PauseCircle, PlayCircle } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { ProgressStatusBadge } from './document-status-badge'

interface PurchaseOrderLineProgressCellProps {
  item: PurchaseOrderItem
  /** Đơn đã duyệt trở đi, dòng đã lưu và chưa khóa. */
  controllable: boolean
  onProgressChange?: (item: PurchaseOrderItem, status: string) => void
  align?: 'center' | 'start'
}

/**
 * Huy hiệu tiến độ dòng + nút Tạm ngưng / Tiếp tục / Hủy + lý do. Dùng chung cho cột Trạng
 * thái của bảng (canh giữa), thẻ khổ điện thoại (canh trái) và ô *Trạng thái tiến độ* trong
 * hộp chi tiết dòng — bản v1 có cụm nút này ở cả bảng lẫn popup (duoc-CR-741). Trang lo hỏi
 * lý do trước khi gọi API, nên mọi chỗ bấm đều đi chung một luồng.
 */
export function PurchaseOrderLineProgressCell({
  item,
  controllable,
  onProgressChange,
  align = 'center',
}: PurchaseOrderLineProgressCellProps) {
  return (
    <div className={cn(align === 'center' ? 'text-center' : 'text-left')}>
      <ProgressStatusBadge status={item.progress_status ?? 'not_ordered'} />
      {controllable && (
        <div
          className={cn(
            'mt-1 flex flex-wrap items-center gap-1',
            align === 'center' ? 'justify-center' : 'justify-start',
          )}
        >
          {item.progress_status === 'paused' ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 px-2 text-xs"
              onClick={() => onProgressChange?.(item, '__resume__')}
            >
              <PlayCircle />
              Tiếp tục
            </Button>
          ) : (
            <>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs"
                onClick={() => onProgressChange?.(item, 'paused')}
              >
                <PauseCircle />
                Tạm ngưng
              </Button>
              <Button
                type="button"
                variant="outline"
                size="sm"
                className="h-7 px-2 text-xs text-destructive hover:text-destructive"
                onClick={() => onProgressChange?.(item, 'cancelled')}
              >
                Hủy
              </Button>
            </>
          )}
        </div>
      )}
      {/*  Chỉ hiện lý do khi dòng ĐANG Tạm ngưng / Hủy — đúng điều kiện v1 ở cả bảng lẫn popup
           (`PurchaseOrderDetail.tsx` ~:1529, ~:2221). Dòng đã Tiếp tục vẫn giữ `pause_reason`
           cũ trong dữ liệu, hiện ra là đọc như dòng còn đang ngưng. */}
      {item.pause_reason && ['paused', 'cancelled'].includes(item.progress_status ?? '') && (
        <p className="mt-1 text-xs text-muted-foreground" title={item.pause_reason}>
          Lý do: {item.pause_reason}
        </p>
      )}
    </div>
  )
}
