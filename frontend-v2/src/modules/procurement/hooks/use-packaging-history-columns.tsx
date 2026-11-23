/**
 * duoc-CR-784 — cột của tab Lịch sử mua hàng. Mọi ô MỘT dòng (cắt bằng "…", đầy đủ ở tooltip) để bảng không phình.
 *
 * Cột bật `sortable` gửi `sort_by` = khóa cột lên máy chủ — khóa phải nằm trong `SORT_KEYS` của
 * `packaging_cost/history_service.py` (`date, code, name, supplier, warehouse, qty, price, amount, vat, source`). "Lần" và
 * "So lần trước" là số tính theo từng mã nên chưa xếp được (luật §8: không bật `sortable` khi máy chủ chưa nhận khóa).
 * Số lượng kèm ĐVT trong một ô; nguồn + số ĐMH chung một cột. Dòng đơn giá 0 mờ đi (không tính vào KPI / biểu đồ); dòng ĐMH đang mở mang nhãn "ĐMH đang mở".
 */
import { useMemo } from 'react'
import type { DataTableColumn } from '@/shared/data-table'
import { PACKAGING_ROLE } from '@/shared/constants/statuses'
import { formatDate } from '@/shared/utils/format-date'
import { formatQuantity } from '@/shared/utils/format-money'

import { PackagingCodeLink } from '../components/packaging-code-link'
import { DiffCell, PriceCell, SourceCell } from '../components/packaging-history-cells'
import { EmptyDash, PriceText } from '../components/packaging-price-cells'
import type { PackagingHistoryRow } from '../types/packaging-cost-types'

const ROLE_LABEL = new Map(PACKAGING_ROLE.map((role) => [Number(role.value), role.label]))

/** "Chai, Nắp" — vai trò mã này đóng trong định mức các sản phẩm đã chọn. */
function roleText(row: PackagingHistoryRow): string {
  return row.roles.map((role) => ROLE_LABEL.get(role) ?? String(role)).join(', ')
}

export function usePackagingHistoryColumns(productMode: boolean, singleCode: boolean) {
  return useMemo<DataTableColumn<PackagingHistoryRow>[]>(() => {
    const columns: DataTableColumn<PackagingHistoryRow>[] = [
      {
        key: 'seq',
        header: 'Lần',
        width: 55,
        align: 'right',
        cell: (row) => <span className="text-muted-foreground tabular-nums">{row.seq}</span>,
      },
      {
        key: 'date',
        header: 'Ngày mua',
        width: 120,
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (row) => (row.date ? formatDate(row.date) : <EmptyDash />),
      },
      {
        key: 'code',
        header: 'Mã VTBB',
        width: 105,
        sortable: true,
        cell: (row) => <PackagingCodeLink code={row.code} />,
      },
    ]
    //  Một mã: tên giống nhau ở mọi dòng (đã có ở ô chọn + tiêu đề biểu đồ) — bỏ cột để nhường chỗ cho nhà cung cấp.
    if (!singleCode) {
      columns.push({
        key: 'name',
        header: 'Tên vật tư',
        width: 160,
        sortable: true,
        cell: (row) => row.name || <span className="text-muted-foreground">(chưa có tên)</span>,
      })
    }
    if (productMode) {
      columns.push({
        key: 'role',
        header: 'Vai trò',
        width: 110,
        cell: (row) => roleText(row) || <EmptyDash />,
      })
    }
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
        key: 'amount',
        header: 'Thành tiền',
        width: 120,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PriceText value={row.price ? row.amount : null} />,
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
