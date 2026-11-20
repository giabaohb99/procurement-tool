/**
 * duoc-CR-784 — bảng SẢN PHẨM BỊ ẢNH HƯỞNG của màn Tác động giá (bám `drawImpact` của bản mẫu).
 *
 * Máy chủ phân trang + tìm + xếp (luật §8: bảng phân trang tại máy chủ thì xếp tại máy chủ — chọn cả nhóm
 * nhãn có thể ra hàng nghìn sản phẩm). Bảng chỉ vẽ MỘT trang và báo thao tác của người dùng qua `view`
 * (`usePackagingImpactTableState`, nằm ở màn vì chúng là một phần thân `POST /impact`). Ô thành phần ghi mã +
 * "giá cũ → giá đang dùng"; mã nằm trong danh sách đang chọn thì tô nổi.
 */
import { Search } from 'lucide-react'
import { useMemo } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Input } from '@/shared/ui/input'

import { PACKAGING_PART_COLUMNS } from '../config/packaging-part-columns'
import type { PackagingImpactTableState } from '../hooks/use-packaging-impact-table-state'
import type { PackagingImpactProduct } from '../types/packaging-cost-types'
import { joinPackagingWarnings, packagingRoleLabel } from '../utils/packaging-warning-text'
import { PackagingPartCell } from './packaging-part-cell'
import { DiffText, PriceText } from './packaging-price-cells'

interface PackagingImpactProductsTableProps {
  /** Dòng của TRANG hiện tại (đã lọc + xếp ở máy chủ). */
  rows: PackagingImpactProduct[] | undefined
  /** Tổng số dòng sau lọc từ khóa (không phải số dòng của trang). */
  total: number
  isLoading: boolean
  isError: boolean
  view: PackagingImpactTableState
}

export function PackagingImpactProductsTable({
  rows,
  total,
  isLoading,
  isError,
  view,
}: PackagingImpactProductsTableProps) {
  const { keyword, sortBy, sortDir, page, pageSize } = view
  const offset = (page - 1) * pageSize

  const columns = useMemo<DataTableColumn<PackagingImpactProduct>[]>(
    () => [
      {
        key: 'stt',
        header: 'STT',
        width: 56,
        align: 'center',
        hideable: false,
        defaultPinned: true,
        cell: (row) => offset + (rows?.indexOf(row) ?? 0) + 1,
      },
      {
        key: 'hh_code',
        header: 'Mã HH',
        width: 110,
        hideable: false,
        defaultPinned: true,
        sortable: true,
        cell: (row) => <span className="font-medium tabular-nums">{row.hh_code}</span>,
      },
      {
        key: 'hh_name',
        header: 'Tên hàng hóa',
        width: 240,
        wrap: true,
        sortable: true,
        cell: (row) => row.hh_name,
      },
      {
        key: 'carton_qty',
        header: 'Quy cách thùng',
        width: 90,
        align: 'right',
        sortable: true,
        cell: (row) => (row.carton_qty ? row.carton_qty.toLocaleString('vi-VN') : <span>—</span>),
      },
      ...PACKAGING_PART_COLUMNS.map<DataTableColumn<PackagingImpactProduct>>((part) => ({
        key: `part_${part.role}`,
        header: part.perCarton
          ? `${packagingRoleLabel(part.role)} (giá /thùng)`
          : packagingRoleLabel(part.role),
        width: 140,
        cell: (row) => (
          <PackagingPartCell part={row.parts.find((item) => item.role === part.role)} />
        ),
      })),
      {
        key: 'cost_old_bottle',
        header: 'CP bao bì/chai cũ',
        width: 110,
        align: 'right',
        sortable: true,
        cell: (row) => <PriceText value={row.cost_old_bottle} />,
      },
      {
        key: 'cost_applied_bottle',
        header: 'CP bao bì/chai mới',
        width: 110,
        align: 'right',
        sortable: true,
        cell: (row) => <PriceText value={row.cost_applied_bottle} className="font-medium" />,
      },
      {
        key: 'diff_bottle',
        header: 'Tăng/giảm /chai',
        width: 100,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <DiffText value={row.diff_bottle} bold />,
      },
      {
        key: 'diff_carton',
        header: 'Tăng/giảm /thùng',
        width: 110,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        cell: (row) => <DiffText value={row.diff_carton} bold />,
      },
      {
        key: 'note',
        header: 'Ghi chú',
        width: 220,
        wrap: true,
        cell: (row) => (
          <span className="text-xs text-muted-foreground">
            {joinPackagingWarnings(row.warnings)}
          </span>
        ),
      },
    ],
    [offset, rows],
  )

  return (
    <DataTable
      //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
      idColumn={false}
      columns={columns}
      rows={rows}
      getRowId={(row) => row.hh_code}
      isLoading={isLoading}
      isError={isError}
      emptyMessage={
        keyword ? 'Không có sản phẩm khớp từ khóa.' : 'Không có sản phẩm nào dùng các mã đã chọn.'
      }
      storageKey="procurement.packaging-impact-products"
      filtersActive={keyword !== ''}
      onResetFilters={() => view.setKeyword('')}
      sortBy={sortBy}
      sortDir={sortDir}
      onSortChange={view.setSort}
      toolbar={
        <div className="relative w-full max-w-xs">
          <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            className="pl-9"
            aria-label="Tìm sản phẩm"
            placeholder="Tìm mã HH, tên, mã thành phần…"
            value={keyword}
            onChange={(event) => view.setKeyword(event.target.value)}
          />
        </div>
      }
      pagination={{
        page,
        pageSize,
        total,
        onPageChange: view.setPage,
        onPageSizeChange: view.setPageSize,
        unitLabel: 'sản phẩm',
      }}
    />
  )
}
