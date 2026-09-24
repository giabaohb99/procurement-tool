// bao-CR-470 — cột của bảng dòng hàng màn Tra cứu giá hải quan (bản v2).
//
// Đại ca chốt 23/09/2026: HIỆN ĐỦ mọi cột ngay từ đầu (không ẩn sẵn cột nào), xếp ĐÚNG thứ
// tự và ĐÚNG tiêu đề của tệp Excel GTT02 — tức đúng `COLUMNS` ở
// `backend/app/modules/customs/constants.py`, kể cả chính tả của tệp gốc — rồi nối hai cột
// suy ra (hoạt chất, hàm lượng / dạng) ở CUỐI. Không thêm cột "giá hiệu lực" riêng.
//
// ⚠️ Đổi thứ tự / thêm bớt cột ở đây thì đổi luôn `STORAGE_KEY` ở trang: bảng nhớ bố cục
// theo khóa đó và bản lưu cũ THẮNG toàn bộ (docs/ui/table.md §4).
import { CalendarSync } from 'lucide-react'

import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import type { CustomsLine } from '../types/customs'
import { formatUsd } from '../utils/customs'

function formatRate(value: number | null): string {
  return value === null || value === undefined ? '' : `${value}%`
}

function money(key: keyof CustomsLine, header: string): DataTableColumn<CustomsLine> {
  return {
    key,
    header,
    width: 130,
    align: 'right',
    cell: (row) => <span className="tabular-nums">{formatUsd(row[key] as number | null)}</span>,
  }
}

function rate(key: keyof CustomsLine, header: string): DataTableColumn<CustomsLine> {
  return {
    key,
    header,
    width: 100,
    align: 'right',
    cell: (row) => <span className="tabular-nums">{formatRate(row[key] as number | null)}</span>,
  }
}

function plain(key: keyof CustomsLine, header: string, width: number, wrap = false): DataTableColumn<CustomsLine> {
  return { key, header, width, wrap, cell: (row) => String(row[key] ?? '') }
}

export const CUSTOMS_LINE_COLUMNS: DataTableColumn<CustomsLine>[] = [
  {
    key: 'reg_date',
    header: 'Ngày đăng ký',
    width: 120,
    hideable: false,
    cell: (row) => (
      <span className="inline-flex items-center gap-1">
        {formatDate(row.reg_date)}
        {row.date_fixed && (
          <CalendarSync
            className="size-3.5 text-warning"
            aria-label="Ngày trong tệp bị đảo ngày/tháng — đã đọc lại"
          />
        )}
      </span>
    ),
  },
  plain('office_code', 'Tên nơi mở tờ khai', 140),
  plain('importer_tax_code', 'Mã doanh nghiệp XNK', 130),
  plain('importer_name', 'Tên doanh nghiệp XNK', 240, true),
  plain('partner_name', 'Đơn vị đối tác', 220, true),
  plain('hs_code', 'Mã hàng khai báo', 110),
  {
    key: 'line_no',
    header: 'Số thứ tự hàng',
    width: 100,
    align: 'right',
    cell: (row) => (row.line_no === null ? '' : row.line_no),
  },
  {
    key: 'product_name',
    header: 'Tên hàng',
    width: 360,
    wrap: true,
    hideable: false,
    cell: (row) => row.product_name,
  },
  money('price_usd', 'Đơn giá khai báo(USD)'),
  money('price_nt', 'Đơn giá NT khai báo'),
  money('adj_price_usd', 'Đơn giá điều chỉnh(USD)'),
  money('adj_price_nt', 'Đơn giá NT điều chỉnh'),
  plain('currency', 'Nguyên tệ', 90),
  money('fx_rate', 'Tỷ giá nguyên tệ'),
  money('usd_rate', 'Tỷ giá USD'),
  {
    key: 'quantity',
    header: 'Lượng',
    width: 120,
    align: 'right',
    cell: (row) => <span className="tabular-nums">{formatQuantity(row.quantity)}</span>,
  },
  plain('unit_code', 'Đơn vị tính', 90),
  plain('origin_country', 'Tên nuớc xuất xứ', 130),
  plain('contract_no', 'Số hợp đồng', 140),
  {
    key: 'contract_date',
    header: 'Ngày hợp đồng',
    width: 120,
    cell: (row) => formatDate(row.contract_date),
  },
  plain('incoterm', 'Điều kiện giao hàng', 110),
  {
    key: 'transport_mode',
    header: 'Phương tiện vận chuyển',
    width: 150,
    cell: (row) => row.transport_label || String(row.transport_mode ?? ''),
  },
  rate('rate_import', 'Thuế suất XNK'),
  rate('rate_excise', 'Thuế suất TTĐB'),
  rate('rate_vat', 'Thuế suất VAT'),
  rate('rate_safeguard', 'Thuế suất tự vệ'),
  money('tax_import', 'Thuế XNK'),
  money('tax_excise', 'Thuế TTĐB'),
  money('tax_vat', 'Thuế VAT'),
  money('tax_environment', 'Thuế môi trường'),
  money('tax_safeguard', 'Thuế tự vệ'),
  plain('import_country', 'Nước nhập khẩu', 120),
  plain('active_ingredient', 'Hoạt chất (suy ra)', 160, true),
  plain('formulation', 'Hàm lượng / dạng (suy ra)', 150),
]
