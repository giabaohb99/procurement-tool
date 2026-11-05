import { ChevronDown, ChevronRight, Trash2 } from 'lucide-react'
import { useState, type ReactNode } from 'react'

import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity } from '@/shared/utils/format-money'
import type { PurchaseOrderDelivery } from '../types/purchase-order-detail'

/** Một ô của lần giao: khóa cột của bảng + nhãn hiện trên thẻ. */
export interface PurchaseOrderDeliveryField {
  key: string
  label: string
}

interface PurchaseOrderDeliveryCardProps {
  delivery: PurchaseOrderDelivery
  index: number
  /** Đủ các cột của bảng (trừ cột thao tác), đúng thứ tự cột. */
  fields: PurchaseOrderDeliveryField[]
  /**
   * CHÍNH `renderCell` của bảng — ô sửa, ô chỉ đọc, luật tính cước đều nằm một
   * chỗ, thẻ chỉ xếp chúng theo chiều dọc kèm nhãn.
   */
  renderField: (key: string) => ReactNode
  /** Thành tiền nhận + huy hiệu trạng thái giao, dựng sẵn bằng `renderField`. */
  receivedAmount: ReactNode
  status: ReactNode
  /** Có thì hiện nút xóa lần giao (đơn còn nhập được tiến độ giao). */
  onRemove?: () => void
  /** Lần giao mới thêm thì mở sẵn để gõ ngay; lần đã lưu thì gập cho gọn. */
  defaultOpen?: boolean
}

/**
 * Một LẦN GIAO của dòng ĐMH ở khổ điện thoại — thay cho bảng 27 cột trong hộp
 * Chi tiết dòng.
 *
 * Bảng này KHÔNG có hộp chi tiết riêng để đẩy việc sửa sang (nó đã nằm trong một
 * hộp thoại rồi), nên thẻ bày thẳng các ô sửa, mỗi ô một hàng: nhãn bên trái,
 * ô nhập bên phải. Xếp hai cột ô nhập thì ô chọn ngày (156px) không lọt khung
 * ~150px của máy 390px.
 *
 * Mặc định GẬP về một tóm tắt (lần, trạng thái, kho, SL nhận, thành tiền, còn
 * nợ): dòng nhận hàng năm sáu đợt mà mở hết là 130 ô nhập xếp chồng. Nút gập là
 * một `<button>`, nút xóa là anh em của nó.
 */
export function PurchaseOrderDeliveryCard({
  delivery,
  index,
  fields,
  renderField,
  receivedAmount,
  status,
  onRemove,
  defaultOpen = false,
}: PurchaseOrderDeliveryCardProps) {
  const [open, setOpen] = useState(defaultOpen)
  const deliveryNo = delivery.delivery_no || index + 1
  const Chevron = open ? ChevronDown : ChevronRight
  const meta = [
    delivery.warehouse_code && `Kho ${delivery.warehouse_code}`,
    delivery.received_date && `Nhận ${formatDate(delivery.received_date)}`,
  ].filter(Boolean)

  return (
    <div className="space-y-3 p-3">
      <div className="flex items-start gap-2">
        <button
          type="button"
          aria-expanded={open}
          onClick={() => setOpen((current) => !current)}
          className="flex min-w-0 flex-1 items-start gap-1.5 text-left"
        >
          <Chevron className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
          <span className="block min-w-0 flex-1 space-y-1">
            <span className="flex flex-wrap items-center gap-2">
              <span className="font-medium text-foreground">Lần {deliveryNo}</span>
              {status}
            </span>
            {meta.length > 0 && (
              <span className="block text-xs text-muted-foreground">{meta.join(' · ')}</span>
            )}
            <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
              <span className="tabular-nums">
                SL nhận {formatQuantity(delivery.received_qty || 0)}
              </span>
              <span className="text-sm text-foreground">{receivedAmount}</span>
            </span>
            {/*  Còn nợ chỉ có khi lần giao đã lưu (backend cộng từ sổ công nợ). */}
            {!!delivery.id && (delivery.remaining ?? 0) > 0 && (
              <span className="block text-xs font-medium tabular-nums text-destructive">
                Còn nợ {formatMoney(delivery.remaining ?? 0)} đ
              </span>
            )}
          </span>
        </button>

        {onRemove && (
          <Button
            type="button"
            variant="ghost"
            size="icon-sm"
            className="shrink-0 text-destructive hover:text-destructive"
            title="Xóa lần giao"
            aria-label={`Xóa lần giao ${deliveryNo}`}
            onClick={onRemove}
          >
            <Trash2 />
          </Button>
        )}
      </div>

      {open && (
        <div className="grid grid-cols-[6.5rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2 border-t pt-3 text-sm">
          {fields.map((field) => (
            <div
              key={field.key}
              role="group"
              aria-label={field.label}
              className="col-span-2 grid grid-cols-subgrid items-center"
            >
              <span className="text-xs text-muted-foreground">{field.label}</span>
              <div className="min-w-0 break-words">{renderField(field.key) || '—'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
