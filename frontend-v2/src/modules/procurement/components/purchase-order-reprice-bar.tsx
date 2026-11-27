import { Loader2, Save, Tag } from 'lucide-react'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { formatMoney } from '@/shared/utils/format-money'
import type { RepriceSummary } from '../utils/purchase-order-reprice'

interface PurchaseOrderRepriceBarProps {
  summary: RepriceSummary
  /** Đuôi tiền của tổng — đơn nội địa `đ`, đơn nhập khẩu theo đồng tiền của đơn. */
  currencySuffix: string
  saving: boolean
  onCancel: () => void
  onSave: () => void
}

/**
 * Thanh nổi MỘT HÀNG ở giữa đáy màn khi đang Sửa giá sau duyệt: số dòng đã sửa, tổng đơn cũ → mới và hai
 * nút Thôi / Lưu giá mới. Không hỏi lý do (người chủ chốt 20/11/2026): nhật ký đã ghi đủ từng ô cũ → mới.
 * Bảng dòng lẫn hộp chi tiết dòng đều lưu qua đây — một lần bấm cho mọi dòng.
 *
 * Cố ý không trải hết bề ngang: bản đầu trải full làm thanh nặng, hai tầng chữ, đè nút Trợ lý AI ở góc phải.
 */
export function PurchaseOrderRepriceBar({
  summary,
  currencySuffix,
  saving,
  onCancel,
  onSave,
}: PurchaseOrderRepriceBarProps) {
  const delta = summary.newTotal - summary.oldTotal
  const hasChanges = summary.changedCount > 0

  return (
    //  `sticky bottom-4` ở cuối khung trang: cuộn tới đâu thanh cũng nổi sát đáy. Lớp ngoài không nhận chuột
    //  để phần trống hai bên thanh vẫn bấm xuyên xuống nội dung bên dưới.
    <div className="pointer-events-none sticky bottom-4 z-30 mt-3 flex justify-center px-2">
      <div
        role="region"
        aria-label="Sửa giá sau duyệt"
        className="pointer-events-auto flex max-w-full flex-wrap items-center gap-x-3 gap-y-2 rounded-xl border border-warning/40 bg-background px-3 py-2 shadow-lg"
      >
        <span className="flex items-center gap-1.5 text-sm font-semibold text-warning">
          <Tag className="size-4" />
          Sửa giá
        </span>
        <span className="text-sm text-muted-foreground tabular-nums">
          {hasChanges ? (
            <>
              {summary.changedCount} dòng · {formatMoney(summary.oldTotal)} →{' '}
              <b className="text-foreground">{formatMoney(summary.newTotal)}</b> {currencySuffix}{' '}
              <span className={cn(delta < 0 ? 'text-success' : 'text-destructive')}>
                ({delta > 0 ? '+' : ''}
                {formatMoney(delta)})
              </span>
            </>
          ) : (
            'Chưa sửa dòng nào'
          )}
        </span>

        <div className="flex gap-2">
          <Button type="button" variant="ghost" size="sm" onClick={onCancel} disabled={saving}>
            Thôi
          </Button>
          <Button
            type="button"
            size="sm"
            onClick={onSave}
            disabled={saving || !hasChanges}
          >
            {saving ? <Loader2 className="animate-spin" /> : <Save />}
            Lưu giá mới
          </Button>
        </div>
      </div>
    </div>
  )
}
