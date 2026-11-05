import { CalendarSync } from 'lucide-react'

import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import type { CustomsLine } from '../../types/customs'
import { formatUsd, formatVnd } from '../../utils/customs'

/**
 * Một DÒNG TỜ KHAI hải quan ở khổ điện thoại — thay cho bảng 37 cột của mục Danh sách
 * (bề rộng tự nhiên ~5.500px, khung 322px chỉ thấy *ID · Ngày đăng ký*).
 *
 * ⚠️ **Tên hàng lên dòng đầu, mã HS / ID tụt xuống dòng phụ**: mười dòng liền nhau thường
 * cùng một mã HS 3808, thứ phân biệt chúng là TÊN HÀNG và AI NHẬP.
 *
 * ⚠️ **Đơn giá giữ đủ 4 số lẻ và chữ USD** (`formatUsd`, như bảng): 2,817 USD/kg mà làm tròn
 * thành 3 là mất hết ý nghĩa của màn tra giá. Đủ 37 trường vẫn xem được ở hộp chi tiết —
 * bảng khai `onRowClick` nên cả thẻ là vùng bấm mở hộp đó, trong thẻ không có nút.
 *
 * Ruột dựng bằng `<span>` (block/flex) vì thẻ nằm trong `<button>` — nút chỉ nhận nội dung chữ.
 */
export function CustomsLineCard({ row }: { row: CustomsLine }) {
  const meta = [row.hs_code && `HS ${row.hs_code}`, `ID ${row.id}`, row.product_kind_label].filter(
    Boolean,
  ) as string[]
  const origin = [row.partner_name && `Đối tác: ${row.partner_name}`, row.origin_country]
    .filter(Boolean)
    .join(' · ')
  const unit = row.unit_code ? `/${row.unit_code}` : ''

  return (
    <span className="block space-y-1.5">
      <span className="block font-medium break-words text-foreground">{row.product_name || '—'}</span>

      <span className="flex min-w-0 flex-wrap items-center gap-x-1 text-xs text-muted-foreground">
        <span className="inline-flex items-center gap-1 tabular-nums">
          {formatDate(row.reg_date) || '—'}
          {row.date_fixed && (
            <CalendarSync
              className="size-3.5 text-warning"
              aria-label="Ngày trong tệp bị đảo ngày/tháng — đã đọc lại"
            />
          )}
        </span>
        {meta.map((text) => (
          <span key={text}>
            <span aria-hidden="true">· </span>
            {text}
          </span>
        ))}
      </span>

      <span className="block text-sm break-words">
        {row.importer_name || row.importer_tax_code || '—'}
      </span>
      {origin && <span className="block text-xs break-words text-muted-foreground">{origin}</span>}

      <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs text-muted-foreground">
        <span>
          Khai báo{' '}
          <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
            {formatUsd(row.price_usd)} USD{unit}
          </span>
        </span>
        {row.adj_price_usd !== null && (
          <span>
            Điều chỉnh{' '}
            <span className="font-medium whitespace-nowrap tabular-nums text-foreground">
              {formatUsd(row.adj_price_usd)} USD{unit}
            </span>
          </span>
        )}
        {row.quantity !== null && (
          <span className="whitespace-nowrap tabular-nums">
            Lượng {formatQuantity(row.quantity)} {row.unit_code}
          </span>
        )}
      </span>

      {row.price_vnd_flat !== null && (
        <span className="block text-xs text-muted-foreground">
          Giá VND (thuế NK 7%){' '}
          <span className="whitespace-nowrap tabular-nums text-foreground">
            {formatVnd(row.price_vnd_flat)}
          </span>
        </span>
      )}
    </span>
  )
}
