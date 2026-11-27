import { useEffect, useRef, type ReactNode } from 'react'
import { Label } from '@/shared/ui/label'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { PO_VAT_OPTIONS, type PurchaseOrderItem } from '../types/purchase-order-detail'
import {
  isQtyBelowReceived,
  isRepriceFieldChanged,
  type RepriceField,
} from '../utils/purchase-order-reprice'
import {
  applyPriceAfterVatInput,
  applyPriceBeforeVatInput,
  repriceOnVatChange,
  resolveLinePriceAfterVat,
} from '../utils/vat-price'

/**
 * Tô sáng CHÍNH ô nhập giá (viền + nền hổ phách), không bọc cả khối bằng khung màu — người chủ chốt 20/11/2026:
 * nhìn vào là thấy ngay ô nào gõ được, phần còn lại của hộp giữ nguyên.
 */
const REPRICE_INPUT_CLASS = 'border-warning bg-warning/10 ring-2 ring-warning/25'

interface PurchaseOrderRepriceLineFieldsProps {
  item: PurchaseOrderItem
  /** Dòng như đang lưu — để hiện số cũ dưới ô vừa đổi. */
  original?: PurchaseOrderItem
  /** Lý do dòng bị chặn; rỗng = sửa được. */
  lockReason: string
  /** Đơn nhập khẩu không có VAT dòng (thuế nằm ở chi phí lô hàng) — bỏ hai ô VAT. */
  importMode: boolean
  onChange: (changes: Partial<PurchaseOrderItem>) => void
}

/**
 * Khối 4 ô Sửa giá sau duyệt trong hộp chi tiết dòng ĐMH: SL đặt · Đơn giá · VAT · Đơn giá sau VAT. Ghi vào
 * cùng bản nháp với bảng dòng; lưu thật ở thanh dưới đáy trang. Trên điện thoại đây là chỗ sửa chính.
 */
export function PurchaseOrderRepriceLineFields({
  item,
  original,
  lockReason,
  importMode,
  onChange,
}: PurchaseOrderRepriceLineFieldsProps) {
  const sectionRef = useRef<HTMLElement>(null)
  const editable = !lockReason
  //  Vừa bấm Sửa giá (hoặc mở hộp của dòng khác khi đang Sửa giá): đưa con trỏ vào ô Đơn giá. KHÔNG bôi đen
  //  cả số (người chủ chốt 20/11/2026). Chờ tới khi dòng được xác nhận sửa được — lúc đầu `lockReason` là câu
  //  "Đang kiểm tra…".
  useEffect(() => {
    if (!editable) return
    sectionRef.current?.querySelector<HTMLInputElement>('#po-reprice-price')?.focus()
  }, [editable])

  if (lockReason) {
    return (
      <p className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-sm">
        Dòng này không sửa giá được: {lockReason}.
      </p>
    )
  }

  const changed = (...fields: RepriceField[]) =>
    !!original && fields.some((field) => isRepriceFieldChanged(original, item, field))

  return (
    <section
      ref={sectionRef}
      aria-label="Sửa giá sau duyệt"
      className="grid gap-x-4 gap-y-3 sm:grid-cols-2 lg:grid-cols-4"
    >
      <p className="text-sm text-muted-foreground sm:col-span-2 lg:col-span-4">
        Đang sửa giá sau duyệt. Sửa xong bấm <b>Xong</b>, rồi <b>Lưu giá mới</b> ở thanh dưới đáy trang.
      </p>
      <RepriceFieldBox
        label="SL đặt"
        htmlFor="po-reprice-qty"
        changed={changed('qty_order')}
        oldText={original ? formatQuantity(original.qty_order) : ''}
      >
        <NumberInput
          id="po-reprice-qty"
          className={REPRICE_INPUT_CLASS}
          value={item.qty_order || 0}
          onChange={(value) => onChange({ qty_order: value })}
        />
        {isQtyBelowReceived(item) && (
          <span role="alert" className="block text-xs text-destructive">
            Không được nhỏ hơn SL đã nhận ({formatQuantity(item.qty_received ?? 0)})
          </span>
        )}
      </RepriceFieldBox>
      <RepriceFieldBox
        label="Đơn giá"
        htmlFor="po-reprice-price"
        changed={changed('price')}
        oldText={original ? formatUnitPrice(original.price) : ''}
      >
        <NumberInput
          id="po-reprice-price"
          className={REPRICE_INPUT_CLASS}
          value={item.price || 0}
          maxDecimals={PRICE_MAX_DECIMALS}
          onChange={(value) => onChange(applyPriceBeforeVatInput(value))}
        />
      </RepriceFieldBox>
      {!importMode && (
        <>
          <RepriceFieldBox
            label="VAT (%)"
            changed={changed('vat')}
            oldText={original ? `${original.vat ?? 0}%` : ''}
          >
            <Select
              value={String(item.vat ?? 0)}
              onValueChange={(value) =>
                onChange({ vat: Number(value), ...repriceOnVatChange(item, item.vat, Number(value)) })
              }
            >
              <SelectTrigger className={cn('w-full', REPRICE_INPUT_CLASS)} aria-label="VAT (%)">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {PO_VAT_OPTIONS.map((option) => (
                  <SelectItem key={option} value={String(option)}>
                    {option}%
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </RepriceFieldBox>
          <RepriceFieldBox
            label="Đơn giá (Sau VAT)"
            htmlFor="po-reprice-price-after-vat"
            changed={changed('price', 'vat')}
            oldText={original ? formatUnitPrice(resolveLinePriceAfterVat(original, original.vat)) : ''}
          >
            <NumberInput
              id="po-reprice-price-after-vat"
              className={REPRICE_INPUT_CLASS}
              value={resolveLinePriceAfterVat(item, item.vat)}
              maxDecimals={2}
              onChange={(value) => onChange(applyPriceAfterVatInput(value, item.vat))}
            />
          </RepriceFieldBox>
        </>
      )}
    </section>
  )
}

function RepriceFieldBox({
  label,
  htmlFor,
  changed,
  oldText,
  children,
}: {
  label: string
  htmlFor?: string
  changed: boolean
  oldText: string
  children: ReactNode
}) {
  return (
    <div className="space-y-1.5">
      <Label htmlFor={htmlFor}>{label}</Label>
      {children}
      {changed && (
        <span className="block text-xs text-warning tabular-nums">
          Đang lưu: <span className="line-through">{oldText}</span>
        </span>
      )}
    </div>
  )
}
