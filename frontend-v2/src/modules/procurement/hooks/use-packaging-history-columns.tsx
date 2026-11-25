/**
 * duoc-CR-784 — cột của tab Lịch sử mua hàng. Mọi ô MỘT dòng (cắt bằng "…", đầy đủ ở tooltip) để bảng không phình.
 *
 * Cột bật `sortable` gửi `sort_by` = khóa cột lên máy chủ — khóa phải nằm trong `SORT_KEYS` của
 * `packaging_cost/history_service.py` (`date, code, name, supplier, warehouse, qty, price, amount, vat, source` + `hh_code,
 * hh_name, role` chỉ ở chế độ sản phẩm). "Lần" và "So lần trước" là số tính theo từng mã nên chưa xếp được (luật §8: không
 * bật `sortable` khi máy chủ chưa nhận khóa). Số lượng kèm ĐVT trong một ô; nguồn + số ĐMH chung một cột. Dòng đơn giá 0 mờ đi
 * (không tính vào KPI / biểu đồ); dòng ĐMH đang mở mang nhãn "ĐMH đang mở".
 *
 * Chế độ "Theo sản phẩm" (bản mẫu `renderHistBySP`): mỗi dòng = một lần mua x một (sản phẩm, thành phần), các cột đầu theo thứ
 * tự bản mẫu: Mã SP · Tên sản phẩm · Thành phần · Mã VTBB · Tên vật tư · Lần · Ngày mua...; chế độ mã: Lần · Ngày mua · Mã VTBB...
 */
import { useMemo } from 'react'
import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import { PackagingCodeLink } from '../components/packaging-code-link'
import { DiffCell, PriceCell, SourceCell } from '../components/packaging-history-cells'
import { EmptyDash, PriceText } from '../components/packaging-price-cells'
import type { PackagingHistoryRow } from '../types/packaging-cost-types'
import { historyRoleText } from '../utils/packaging-history'

const seqColumn: DataTableColumn<PackagingHistoryRow> = {
  key: 'seq',
  header: 'Lần',
  width: 55,
  align: 'right',
  cell: (row) => <span className="text-muted-foreground tabular-nums">{row.seq}</span>,
}

const dateColumn: DataTableColumn<PackagingHistoryRow> = {
  key: 'date',
  header: 'Ngày mua',
  width: 120,
  sortable: true,
  sortDescFirst: true,
  hideable: false,
  cell: (row) => (row.date ? formatDate(row.date) : <EmptyDash />),
}

const codeColumn: DataTableColumn<PackagingHistoryRow> = {
  key: 'code',
  header: 'Mã VTBB',
  width: 105,
  sortable: true,
  cell: (row) => <PackagingCodeLink code={row.code} />,
}

const nameColumn: DataTableColumn<PackagingHistoryRow> = {
  key: 'name',
  header: 'Tên vật tư',
  width: 160,
  sortable: true,
  cell: (row) => row.name || <span className="text-muted-foreground">(chưa có tên)</span>,
}

/** Ba cột đầu của chế độ sản phẩm (bản mẫu: Mã SP · Tên sản phẩm · Thành phần). */
const productColumns: DataTableColumn<PackagingHistoryRow>[] = [
  {
    key: 'hh_code',
    header: 'Mã SP',
    width: 110,
    sortable: true,
    cell: (row) => <span className="font-medium">{row.hh_code}</span>,
  },
  {
    key: 'hh_name',
    header: 'Tên sản phẩm',
    width: 200,
    sortable: true,
    cell: (row) => row.hh_name || <span className="text-muted-foreground">(chưa có tên)</span>,
  },
  {
    key: 'role',
    header: 'Thành phần',
    width: 110,
    sortable: true,
    cell: (row) => historyRoleText(row) || <EmptyDash />,
  },
]

export function usePackagingHistoryColumns(productMode: boolean, singleCode: boolean) {
  return useMemo<DataTableColumn<PackagingHistoryRow>[]>(() => {
    //  Một mã: tên giống nhau ở mọi dòng (đã có ở ô chọn + tiêu đề biểu đồ) — bỏ cột để nhường chỗ cho nhà cung cấp.
    const columns: DataTableColumn<PackagingHistoryRow>[] = productMode
      ? [...productColumns, codeColumn, nameColumn, seqColumn, dateColumn]
      : [seqColumn, dateColumn, codeColumn, ...(singleCode ? [] : [nameColumn])]
    columns.push(
      {
        key: 'supplier',
        header: 'Nhà cung cấp',
        width: singleCode ? 220 : 140,
        sortable: true,
        cell: (row) => row.supplier || <EmptyDash />,
      },
      {
        // Kho nhập hàng của lần mua (chép theo dòng sổ giá). Một dòng, cắt bằng "…"; đầy đủ ở tooltip.
        key: 'warehouse',
        header: 'Kho',
        width: 190,
        sortable: true,
        cell: (row) => row.warehouse || <EmptyDash />,
      },
      {
        key: 'qty',
        header: 'Số lượng',
        width: 110,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => {
          const text = formatQuantity(row.qty)
          if (!text) return <EmptyDash />
          return (
            <span className="tabular-nums">
              {text}
              {row.unit && <span className="ml-1 text-xs text-muted-foreground">{row.unit}</span>}
            </span>
          )
        },
      },
      {
        key: 'price',
        header: 'Đơn giá',
        width: 100,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PriceCell row={row} />,
      },
      {
        // Giá trị mua = thành tiền Misa khi có, không thì giá x số lượng (máy chủ tính); dòng giá 0 không có giá trị.
        key: 'amount',
        header: 'Giá trị mua',
        width: 120,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PriceText value={row.amount} />,
      },
      {
        key: 'diff',
        header: 'So lần trước',
        width: 140,
        align: 'right',
        cell: (row) => <DiffCell row={row} />,
      },
      {
        key: 'source',
        header: 'Nguồn',
        width: 120,
        sortable: true,
        cell: (row) => <SourceCell row={row} />,
      },
    )
    return columns
  }, [productMode, singleCode])
}
