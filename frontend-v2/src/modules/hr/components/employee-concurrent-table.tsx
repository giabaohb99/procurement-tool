import { useMemo, type ReactNode } from 'react'

import { DataTable } from '@/shared/data-table'
import { SectionHeading } from '@/shared/ui/section-heading'
import { sortRowsByCell } from '@/shared/utils/sort-rows-by-cell'
import {
  buildEmployeeConcurrentColumns,
  EMPLOYEE_CONCURRENT_SORT_GETTERS,
  type EmployeeConcurrentRowActions,
} from '../config/employee-concurrent-columns'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import { sortConcurrentRowsDefault } from '../utils/employee-concurrent-display'
import { EmployeeConcurrentMobileCard } from './employee-concurrent-mobile-card'

interface EmployeeConcurrentTableProps {
  items: EmployeeConcurrent[] | undefined
  isLoading: boolean
  isError: boolean
  canOpenFiles: boolean
  onOpenFiles: (row: EmployeeConcurrent) => void
  /** Bỏ trống = chỉ xem (không có cột Thao tác). */
  actions?: EmployeeConcurrentRowActions
  /** Nút "Thêm kiêm nhiệm" ở cuối dải công cụ. */
  addButton?: ReactNode
}

/**
 * Bảng dòng kiêm nhiệm của một hồ sơ. Nạp đủ mọi dòng (trần 30) nên xếp ở trình duyệt: chưa bấm cột nào thì theo thứ tự
 * mặc định Đang hiệu lực → Sắp tới → Đã hết, rồi từ ngày giảm dần.
 */
export function EmployeeConcurrentTable({
  items,
  isLoading,
  isError,
  canOpenFiles,
  onOpenFiles,
  actions,
  addButton,
}: EmployeeConcurrentTableProps) {
  const sort = useLocalTableSort()
  const rows = useMemo(() => {
    if (!items) return undefined
    const base = sortConcurrentRowsDefault(items)
    return sort.sortBy ? sortRowsByCell(base, sort.sortBy, sort.sortDir, EMPLOYEE_CONCURRENT_SORT_GETTERS) : base
  }, [items, sort.sortBy, sort.sortDir])

  const columns = useMemo(
    () => buildEmployeeConcurrentColumns({ canOpenFiles, onOpenFiles, actions }),
    [canOpenFiles, onOpenFiles, actions],
  )

  return (
    <DataTable
      columns={columns}
      rows={rows}
      getRowId={(row) => row.id}
      //  Số id dòng kiêm nhiệm không có nghĩa gì với người đọc, mà cột đó đẩy bảng phải cuộn ngang ở khổ 1440 — bỏ.
      idColumn={false}
      sortBy={sort.sortBy}
      sortDir={sort.sortDir}
      onSortChange={sort.onSortChange}
      isLoading={isLoading}
      isError={isError}
      errorMessage="Không tải được danh sách kiêm nhiệm."
      emptyMessage="Người này chưa có dòng kiêm nhiệm nào."
      storageKey="hr.employee-concurrents"
      filtersActive={false}
      mobileCard={(row) => (
        <EmployeeConcurrentMobileCard row={row} canOpenFiles={canOpenFiles} onOpenFiles={onOpenFiles} actions={actions} />
      )}
      toolbar={
        <div className="min-w-0 flex-1">
          <SectionHeading>Kiêm nhiệm</SectionHeading>
        </div>
      }
      toolbarEnd={addButton}
    />
  )
}
