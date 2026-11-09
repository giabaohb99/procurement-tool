import { formatDate } from '@/shared/utils/format-date'
import { formatPercent, formatQuantity } from '@/shared/utils/format-money'

import type { CustomsImporterRow } from '../../types/customs'
import { formatUsd } from '../../utils/customs'

interface CustomsImporterCardProps {
  row: CustomsImporterRow & { rank: number }
  /** Nhãn đơn vị đang xếp hạng (kg, lít…) — cùng chữ với tiêu đề cột của bảng. */
  unit: string
}

/**
 * Một DOANH NGHIỆP NHẬP KHẨU ở khổ điện thoại — thay bảng xếp hạng 8 cột (~1.150px).
 *
 * ⚠️ **Hạng là cột riêng bên trái**, không dính vào tên: đây là bảng XẾP HẠNG, đọc dọc mép
 * trái phải ra 1, 2, 3… như cột "#" của bảng.
 *
 * ⚠️ **Giá bình quân giữ đủ số lẻ và đơn vị USD/đơn vị** (`formatUsd`) — đó là con số người
 * ta mở mục này ra để so. Thanh thị phần giữ y như ô của bảng để mắt so nhanh giữa các thẻ.
 *
 * Bảng khai `onRowClick` (lọc danh sách theo doanh nghiệp) nên cả thẻ là `<button>`: trong
 * thẻ không có nút, ruột dựng bằng `<span>`.
 */
export function CustomsImporterCard({ row, unit }: CustomsImporterCardProps) {
  return (
    <span className="flex items-start gap-2">
      <span className="shrink-0 text-xs leading-5 tabular-nums text-muted-foreground">{row.rank}.</span>

      <span className="block min-w-0 flex-1 space-y-1.5">
        <span className="block font-medium break-words text-foreground">{row.name || '—'}</span>
        <span className="block text-xs text-muted-foreground">
          {row.tax_code ? `MST ${row.tax_code}` : 'Chưa có mã số thuế'}
          {row.last_date && <span> · Nhập gần nhất {formatDate(row.last_date)}</span>}
        </span>

        <span className="flex flex-wrap items-baseline gap-x-3 gap-y-1 text-xs text-muted-foreground">
          <span>
            Giá BQ{' '}
            <span className="text-sm font-semibold whitespace-nowrap tabular-nums text-foreground">
              {formatUsd(row.wavg)} {unit ? `USD/${unit}` : 'USD'}
            </span>
          </span>
          <span className="whitespace-nowrap tabular-nums">
            {formatQuantity(row.qty)}
            {unit && ` ${unit}`} · {row.count} dòng
          </span>
        </span>

        {row.share !== null && (
          <span className="flex items-center gap-2 text-xs">
            <span className="h-1.5 w-24 overflow-hidden rounded-full bg-chart-track">
              <span
                className="block h-full bg-chart-1"
                style={{ width: `${Math.round(row.share * 100)}%` }}
              />
            </span>
            <span className="tabular-nums">Thị phần {formatPercent(row.share * 100)}</span>
          </span>
        )}
      </span>
    </span>
  )
}
