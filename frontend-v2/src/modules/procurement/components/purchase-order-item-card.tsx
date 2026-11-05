import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Checkbox } from '@/shared/ui/checkbox'
import { RequiredMark } from '@/shared/ui/required-mark'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'

/** Một ô sửa tại chỗ của dòng: nhãn + ô do `renderCell` của bảng dựng sẵn. */
export interface PurchaseOrderItemEditField {
  key: string
  label: string
  required: boolean
  content: ReactNode
}

interface PurchaseOrderItemCardProps {
  item: PurchaseOrderItem
  index: number
  /**
   * Ô thành tiền và ô quy đổi VNĐ dựng sẵn bằng CHÍNH `renderCell` của bảng —
   * luật hậu tố tiền tệ của đơn nhập khẩu nằm một chỗ, thẻ không tự tính lại.
   */
  amount: ReactNode
  baseAmount?: ReactNode
  /** Huy hiệu tiến độ kèm nút Tạm ngưng / Tiếp tục / Hủy — có nút nên đứng NGOÀI vùng chạm. */
  progress: ReactNode
  /** Nút "Hồ sơ" (% báo cáo thực hiện); không có thì bỏ trống. */
  report?: ReactNode
  /** Lịch sử mua hàng · nhân bản · xóa — anh em của vùng chạm. */
  actions: ReactNode
  /**
   * Các ô mà bảng cho sửa tại chỗ nhưng hộp chi tiết dòng KHÔNG có (mã hàng, SL
   * đặt, đơn giá, VAT). Rỗng / không truyền = dòng không sửa được.
   */
  editFields?: PurchaseOrderItemEditField[]
  /** Có thì cả khối chữ là một nút mở hộp Chi tiết dòng & các lần giao hàng. */
  onOpenDetail?: () => void
  /** Ô tick xóa nhiều dòng; `undefined` = bảng không bật chọn nhiều. */
  selection?: {
    checked: boolean
    disabledReason?: string
    onToggle: () => void
  }
}

/**
 * Một DÒNG HÀNG của ĐMH ở khổ điện thoại — thay cho bảng 14–15 cột.
 *
 * Ba cột ghim (*# · Mã hàng · Tên hàng*) đã rộng ~560px, hơn cả khung 322px của
 * máy 390px, nên ở khổ đó không vị trí cuộn nào nhìn thấy được SL, thành tiền
 * hay tiến độ. Lối bày giống `PurchaseRequestLineCard`: tên hàng lên đầu, mã
 * tụt xuống dòng phụ màu sky.
 *
 * ⚠️ **Sửa dòng đi HAI đường, không phải một.** Tên hàng, phân loại, ĐVT, kho,
 * ngày… nằm trong hộp Chi tiết dòng (chạm vào thẻ). Nhưng mã hàng, SL đặt, đơn
 * giá, VAT thì hộp KHÔNG có — trên bảng chúng chỉ sửa ngay trong ô — nên thẻ bày
 * các ô đó (`editFields`) có nhãn, dưới vùng chạm. Thiếu chúng thì dòng mới thêm
 * trên điện thoại kẹt ở "(chưa chọn hàng)" vì không có chỗ nào chọn hàng.
 *
 * Nút thao tác và cụm tiến độ là ANH EM của vùng chạm, không nằm trong nó — lồng
 * `<button>` vào `<button>` là HTML sai. Ruột vùng chạm chỉ dùng `<span>`.
 */
export function PurchaseOrderItemCard({
  item,
  index,
  amount,
  baseAmount,
  progress,
  report,
  actions,
  editFields,
  onOpenDetail,
  selection,
}: PurchaseOrderItemCardProps) {
  const body = (
    <>
      <span className="line-clamp-2 block font-medium text-foreground">
        {item.product_name || item.product_code || '(chưa chọn hàng)'}
      </span>

      {/*  Dấu `·` nằm cùng span với vế sau để lúc co chữ không thành chấm mồ côi. */}
      <span className="flex min-w-0 flex-wrap items-center gap-1 text-xs text-muted-foreground">
        <span className="font-medium text-sky-600 dark:text-sky-400">
          {item.product_code || '—'}
        </span>
        {item.item_group && (
          <span>
            <span aria-hidden="true">· </span>
            {item.item_group}
          </span>
        )}
      </span>

      <span className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
        <span className="tabular-nums">
          {formatQuantity(item.qty_order)} {item.unit || ''} × {formatUnitPrice(item.price)}
        </span>
        <span className="text-sm">{amount}</span>
      </span>

      {baseAmount && (
        <span className="block text-xs text-muted-foreground">Quy đổi {baseAmount}</span>
      )}

      {/*  Tiến độ giao chỉ có nghĩa khi đã nhận ít nhất một đợt — "0/10" trên mọi
           dòng mới là nhiễu. Giao thiếu thì luôn hiện vì đó là việc phải xử lý. */}
      {((item.qty_received ?? 0) > 0 || item.is_short_delivery) && (
        <span className="flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
          <span className="tabular-nums">
            Nhận {formatQuantity(item.qty_received ?? 0)}/{formatQuantity(item.qty_order)}
          </span>
          {item.is_short_delivery && (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Giao thiếu
            </Badge>
          )}
        </span>
      )}
    </>
  )

  return (
    <div className="space-y-3 p-3">
      <div className="flex items-start gap-2">
        {/*  Số thứ tự là CỘT RIÊNG (như thẻ YCMH): nhét vào dòng tiêu đề thì mép trái
           thẻ thành răng cưa. Ô tick đứng trên số để ngón cái chạm trúng. */}
        <span className="flex shrink-0 flex-col items-center gap-1.5">
          {selection && (
            <Checkbox
              aria-label={`Chọn dòng ${index + 1}`}
              checked={selection.checked}
              disabled={!!selection.disabledReason}
              title={selection.disabledReason}
              onCheckedChange={selection.onToggle}
            />
          )}
          <span className="text-xs leading-5 text-muted-foreground tabular-nums">{index + 1}.</span>
        </span>

        <div className="min-w-0 flex-1 space-y-2">
          {onOpenDetail ? (
            <button
              type="button"
              onClick={onOpenDetail}
              aria-label={`Chi tiết dòng ${index + 1}: ${item.product_name || item.product_code || 'dòng mới'}`}
              className="block w-full min-w-0 space-y-1 text-left"
            >
              {body}
            </button>
          ) : (
            <span className="block min-w-0 space-y-1">{body}</span>
          )}

          <div className="flex flex-wrap items-start gap-2">
            {progress}
            {report}
          </div>
        </div>

        <div className="flex shrink-0 items-start gap-0.5">{actions}</div>
      </div>

      {/*  Ô sửa tại chỗ trải HẾT bề ngang thẻ (chỉ thụt bằng cột số thứ tự), không nằm
           trong cột giữa: cột nút bên phải ăn mất ~60px, ô chọn hàng kèm hai nút
           chép / lịch sử sẽ không còn chỗ hiện mã. */}
      {editFields && editFields.length > 0 && (
        <div className="ml-7 grid grid-cols-[5rem_minmax(0,1fr)] items-center gap-x-3 gap-y-2 border-t pt-3 text-sm">
          {editFields.map((field) => (
            <div
              key={field.key}
              role="group"
              aria-label={field.label}
              className="col-span-2 grid grid-cols-subgrid items-center"
            >
              <span className="text-xs text-muted-foreground">
                {field.label}
                {field.required && <RequiredMark />}
              </span>
              <div className="min-w-0">{field.content}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
