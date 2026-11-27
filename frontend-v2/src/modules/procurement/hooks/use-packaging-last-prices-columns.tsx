/**
 * duoc-CR-784 — cột của tab Giá mua gần nhất. Tiêu đề GỘP NHÓM do `DataTable` vẽ từ `group` của cột:
 * "Thông tin VTBB" | "Lần 1 (gần nhất)" … "Lần n" | "Biến động" | "Giá TB". Mỗi lần mua gồm Ngày mua, Nhà cung cấp,
 * (tùy chọn) Số lượng và Đơn giá; nhóm lẻ nhuộm nền, cuối nhóm kẻ vạch ngăn (do bảng lo).
 *
 * Tên vật tư / nhà cung cấp luôn MỘT dòng (cắt bằng "…", đầy đủ ở tooltip `title` của ô) để hàng cao bằng các bảng khác.
 *
 * Cột bật `sortable` gửi `sort_by` = khóa cột lên máy chủ — khóa phải nằm trong `SORT_KEYS` / mẫu `p{k}_price|date` của
 * `packaging_cost/last_prices_service.py`. Số lượng / nhà cung cấp không xếp được vì máy chủ chưa có khóa (luật §8).
 */
import { useMemo } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { formatDate } from '@/shared/utils/format-date'

import { PackagingCodeLink } from '../components/packaging-code-link'
import { EmptyDash, PercentText, PriceText } from '../components/packaging-price-cells'
import type { PackagingLastPricesRow } from '../types/packaging-cost-types'
import { formatPackagingPrice } from '../utils/packaging-price-format'
import { purchaseAt, purchaseGroupLabel, purchaseTrendTone } from '../utils/packaging-last-prices'

const INFO = 'Thông tin VTBB'
const VARIATION = 'Biến động'
const AVERAGE = 'Giá TB'

function purchaseColumns(index: number, showQty: boolean): DataTableColumn<PackagingLastPricesRow>[] {
  const slot = index + 1
  const group = purchaseGroupLabel(index)
  //  Mỗi cụm Lần một màu tiêu đề (người chủ chọn 20/11/2026), thân bảng để trắng.
  const groupTone = index
  const columns: DataTableColumn<PackagingLastPricesRow>[] = [
    {
      key: `p${slot}_date`,
      header: 'Ngày mua',
      group,
      groupTone,
      width: 120,
      sortable: true,
      sortDescFirst: true,
      cell: (row) => {
        const date = purchaseAt(row, index)?.date
        return date ? formatDate(date) : <EmptyDash />
      },
    },
    {
      key: `p${slot}_supplier`,
      header: 'Nhà cung cấp',
      group,
      groupTone,
      width: 220,
      cell: (row) => purchaseAt(row, index)?.supplier || <EmptyDash />,
    },
  ]
  if (showQty) {
    columns.push({
      key: `p${slot}_qty`,
      header: 'Số lượng',
      group,
      groupTone,
      width: 105,
      align: 'right',
      cell: (row) => {
        const text = formatPackagingPrice(purchaseAt(row, index)?.qty)
        return text ? <span className="tabular-nums">{text}</span> : <EmptyDash />
      },
    })
  }
  columns.push({
    key: `p${slot}_price`,
    header: 'Đơn giá',
    group,
    groupTone,
    width: 110,
    align: 'right',
    sortable: true,
    sortDescFirst: true,
    cell: (row) => (
      <PriceText
        value={purchaseAt(row, index)?.price}
        className={['font-semibold', purchaseTrendTone(row, index)].filter(Boolean).join(' ')}
      />
    ),
  })
  return columns
}

export function usePackagingLastPricesColumns(n: number, showQty: boolean) {
  return useMemo<DataTableColumn<PackagingLastPricesRow>[]>(
    () => [
      {
        key: 'code',
        header: 'Mã VTBB',
        group: INFO,
        width: 120,
        sortable: true,
        hideable: false,
        defaultPinned: true,
        cell: (row) => <PackagingCodeLink code={row.code} />,
      },
      {
        key: 'name',
        header: 'Tên vật tư',
        group: INFO,
        width: 260,
        sortable: true,
        //  Ghim cùng cột Mã (27/11/2026): cuộn ngang qua các lần mua vẫn thấy tên hàng.
        defaultPinned: true,
        cell: (row) => row.name || <span className="text-muted-foreground">(chưa có tên)</span>,
      },
      { key: 'group', header: 'Nhóm', group: INFO, width: 100, sortable: true, cell: (row) => row.group },
      { key: 'unit', header: 'ĐVT', group: INFO, width: 70, cell: (row) => row.unit },
      {
        key: 'purchase_count',
        header: 'Số lần có giá',
        group: INFO,
        width: 135,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => row.purchase_count,
      },
      ...Array.from({ length: n }, (_, index) => purchaseColumns(index, showQty)).flat(),
      {
        key: 'v12',
        header: 'Lần 1 so lần 2',
        group: VARIATION,
        width: 140,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PercentText value={row.v12} />,
      },
      {
        key: 'v1n',
        header: `Lần 1 so lần ${n}`,
        group: VARIATION,
        width: 145,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PercentText value={row.v1n} />,
      },
      {
        key: 'avg',
        header: `Giá TB ${n} lần`,
        group: AVERAGE,
        width: 130,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <PriceText value={row.avg} className="font-semibold" />,
      },
    ],
    [n, showQty],
  )
}
