import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'

/**
 * Trường chung của một PHƯƠNG ÁN ở hai bàn xử lý: phương án dòng YCMH
 * (`PurchaseRequestOption`) và phương án dòng YCBG (`SurveyProcessOption`). Khai
 * đúng phần giao của hai kiểu để một thẻ dùng được cho cả hai mà không phải ép kiểu.
 */
export interface ProcessOptionCardData {
  display_label: string
  public_id: number
  is_chosen: boolean
  supplier_code: string
  supplier_name: string
  snap_product_name: string
  snap_spec: string
  snap_price_by_volume: number
  snap_moq: number
  snap_quote_unit: string
  snap_vat: number
}

/** Một ô sửa / ô chữ đi kèm thẻ (ghi chú NSTM, mã SP hệ thống). */
export interface ProcessOptionCardField {
  label: string
  content: ReactNode
}

interface ProcessOptionCardProps {
  option: ProcessOptionCardData
  /** Chữ đứng trước số khi phương án chưa có nhãn: "Phương án" (YCMH) / "Option" (YCBG). */
  labelPrefix: string
  /** Thiếu `supplier:read` thì backend trả NCC rỗng — bỏ hẳn dòng NCC, đừng bày gạch ngang. */
  showSupplier?: boolean
  /** Nguồn phương án (từ khảo sát / nhập tay) — chỉ màn YCMH có. */
  sourceLabel?: string
  fields?: ProcessOptionCardField[]
  /** Nút sửa / gỡ — đứng ANH EM với khối chữ, bám góc phải. */
  actions?: ReactNode
}

/**
 * Một PHƯƠNG ÁN ở khổ điện thoại — thay cho bảng con 10–11 cột của màn xử lý.
 *
 * ⚠️ **NCC lên dòng đầu, nhãn "Phương án n" tụt xuống dòng phụ**: cả bảng con là
 * phương án của CÙNG một dòng hàng, nên thứ phân biệt chúng là AI báo giá chứ không
 * phải số thứ tự. Người xem không có quyền NCC thì tên SP theo NCC thay vào chỗ đó.
 *
 * ⚠️ **Thẻ là `div`, không phải `button`**: bên trong có ô nhập ghi chú, ô chọn mã SP
 * và nút gỡ — lồng chúng vào một vùng bấm là HTML sai và hai vùng chạm đè nhau.
 */
export function ProcessOptionCard({
  option,
  labelPrefix,
  showSupplier = true,
  sourceLabel,
  fields = [],
  actions,
}: ProcessOptionCardProps) {
  const label = option.display_label || `${labelPrefix} ${option.public_id}`
  const supplier = option.supplier_name || option.supplier_code
  const title = showSupplier ? supplier || '(chưa có NCC)' : option.snap_product_name || label
  const quoteUnit = option.snap_quote_unit ? `/${option.snap_quote_unit}` : ''

  return (
    <div className="flex items-start gap-2">
      <div className="min-w-0 flex-1 space-y-1">
        <p className="font-medium break-words text-foreground">{title}</p>

        {/*  Dấu `·` nằm CÙNG span với vế đứng sau — tách riêng thì lúc co chữ nó ở
             lại cuối dòng trên thành một dấu chấm mồ côi. */}
        <p className="flex flex-wrap items-center gap-1 text-xs text-muted-foreground">
          <span className="font-medium text-sky-600 dark:text-sky-400">{label}</span>
          {sourceLabel && (
            <span>
              <span aria-hidden="true">· </span>
              {sourceLabel}
            </span>
          )}
        </p>

        {showSupplier && (
          <p className="text-sm break-words">
            {option.snap_product_name || '—'}
            {option.snap_spec && (
              <span className="block text-xs text-muted-foreground">{option.snap_spec}</span>
            )}
          </p>
        )}
        {!showSupplier && option.snap_spec && (
          <p className="text-xs break-words text-muted-foreground">{option.snap_spec}</p>
        )}

        <p className="flex flex-wrap items-baseline gap-x-2 gap-y-1 text-xs text-muted-foreground">
          <span className="text-sm font-semibold tabular-nums text-foreground">
            {option.snap_price_by_volume
              ? `${formatUnitPrice(option.snap_price_by_volume)} đ${quoteUnit}`
              : 'Chưa có giá'}
          </span>
          {!!option.snap_moq && (
            <span className="tabular-nums">MOQ {formatQuantity(option.snap_moq)}</span>
          )}
          {!!option.snap_vat && <span className="tabular-nums">VAT {option.snap_vat}%</span>}
        </p>

        <div className="pt-0.5">
          {option.is_chosen ? (
            <Badge variant="secondary" className="border-0 bg-success/10 text-success">
              Người YC đã chọn
            </Badge>
          ) : (
            <span className="text-xs text-muted-foreground">Chưa chọn</span>
          )}
        </div>

        {fields.map((field) => (
          <div key={field.label} className="space-y-1 pt-1">
            <span className="block text-xs font-medium text-muted-foreground">{field.label}</span>
            <div className="text-sm">{field.content}</div>
          </div>
        ))}
      </div>

      {actions && <div className="flex shrink-0 items-start gap-0.5">{actions}</div>}
    </div>
  )
}
