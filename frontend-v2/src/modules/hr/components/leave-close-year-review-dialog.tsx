import { Download } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { downloadFile } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { sortRowsBy, type SortValue } from '@/shared/utils/compare-sort-values'
import { closeYearReviewExportUrl } from '../api/leave-api'
import { useCloseYearReview } from '../hooks/use-leave'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import type { LeaveCloseYearReviewRow } from '../types/leave'
import { formatCloseYearDays as formatDays } from '../utils/format-close-year-days'
import { LeaveCloseYearReviewCard } from './leave-close-year-review-card'

/** Chữ ô "Nhân sự" — một chỗ cho cả ô lẫn phép xếp. */
function employeeText(r: LeaveCloseYearReviewRow): string {
  return `${r.employee_name} (${r.employee_code})`
}

/**
 * Giá trị đem xếp của từng cột (duoc-CR-748) — đúng thứ ô đang hiện. Cột số in cả số 0 nên 0 là giá trị thật;
 * "Sang loại" chưa khai (chữ *Chưa khai*) là ô trống, xuống cuối cả hai chiều.
 */
const REVIEW_SORT_GETTERS: Record<string, (r: LeaveCloseYearReviewRow) => SortValue> = {
  employee: employeeText,
  source: (r) => r.source_type_name,
  before: (r) => r.before_days,
  after: (r) => r.after_days,
  diff: (r) => r.diff_days,
  dest: (r) => r.dest_type_name,
  credited: (r) => r.credited_days,
}

/** Bằng nhau thì theo người rồi theo loại nghỉ nguồn — dòng không có `id`, khóa dòng là cặp đó. */
function byEmployeeThenSource(a: LeaveCloseYearReviewRow, b: LeaveCloseYearReviewRow): number {
  return a.employee_id - b.employee_id || a.source_type_id - b.source_type_id
}

interface LeaveCloseYearReviewDialogProps {
  /** Năm VỪA kết sổ (năm cũ). `null` = đóng hộp. */
  year: number | null
  onClose: () => void
}

/**
 * BẢNG ĐỐI CHIẾU trước/sau kết sổ phép cuối năm (kh-HR2-3, duoc-CR-664): từng người,
 * từng loại nghỉ — số cũ, số mới, chênh, và phần sang năm sau.
 *
 * Số cũ được DỰNG LẠI từ sổ quỹ (còn lại + đã chuyển đi), không phải ảnh chụp lúc
 * bấm nút — xem `carryover_review_service.py`. Vì thế đơn năm cũ duyệt/hủy sau kết
 * sổ sẽ làm số đổi theo; câu ghi chú ở chân hộp nói rõ điều đó.
 */
export function LeaveCloseYearReviewDialog({ year, onClose }: LeaveCloseYearReviewDialogProps) {
  const { can } = usePermission()
  const { data, isLoading, isError } = useCloseYearReview(year ?? 0, year !== null)
  const [exporting, setExporting] = useState(false)
  //  Xếp ngay ở trình duyệt: API trả đủ mọi dòng của năm (không phân trang).
  const sort = useLocalTableSort()
  const items = data?.items
  const rows = useMemo(() => {
    const getValue = REVIEW_SORT_GETTERS[sort.sortBy]
    if (!items || !getValue) return items
    return sortRowsBy(items, getValue, sort.sortDir, byEmployeeThenSource)
  }, [items, sort.sortBy, sort.sortDir])

  const columns = useMemo<DataTableColumn<LeaveCloseYearReviewRow>[]>(
    () => [
      { key: 'employee', header: 'Nhân sự', width: 200, hideable: false, wrap: true, sortable: true,
        cell: employeeText },
      { key: 'source', header: 'Loại nghỉ', width: 130, wrap: true, sortable: true,
        cell: (r) => r.source_type_name },
      { key: 'before', header: 'Số cũ (trước)', width: 110, align: 'right', sortable: true,
        cell: (r) => formatDays(r.before_days) },
      { key: 'after', header: 'Số mới (sau)', width: 110, align: 'right', sortable: true,
        cell: (r) => formatDays(r.after_days) },
      { key: 'diff', header: 'Chênh', width: 90, align: 'right', sortable: true,
        cell: (r) => formatDays(r.diff_days) },
      { key: 'dest', header: 'Sang loại', width: 130, wrap: true, sortable: true,
        cell: (r) => r.dest_type_name || 'Chưa khai' },
      { key: 'credited', header: 'Cộng vào năm sau', width: 120, align: 'right', sortable: true,
        cell: (r) => formatDays(r.credited_days) },
    ],
    [],
  )

  const exportExcel = async () => {
    if (year === null) return
    setExporting(true)
    try {
      await downloadFile(closeYearReviewExportUrl, `doi-chieu-ket-so-phep-${year}.xlsx`, { year })
    } catch {
      toast.error('Không xuất được tệp Excel.')
    } finally {
      setExporting(false)
    }
  }

  const totals = data?.totals

  return (
    <Dialog open={year !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="sm:max-w-5xl">
        <DialogHeader>
          <DialogTitle>Đối chiếu kết sổ phép năm {year}</DialogTitle>
          <DialogDescription>
            Số dư năm {year} trước và sau khi kết sổ, kèm phần chuyển sang năm {(year ?? 0) + 1}.
          </DialogDescription>
        </DialogHeader>

        <DataTable
          columns={columns}
          rows={rows}
          getRowId={(r) => `${r.employee_id}-${r.source_type_id}`}
          sortBy={sort.sortBy}
          sortDir={sort.sortDir}
          onSortChange={sort.onSortChange}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={`Chưa có dòng nào được kết sổ cho năm ${year}.`}
          storageKey="hr.leave-close-year-review"
          mobileCard={(r) => <LeaveCloseYearReviewCard row={r} />}
          toolbarEnd={
            can('leave_balance', 'export') && (
              <Button variant="outline" size="sm" onClick={() => void exportExcel()}
                disabled={exporting || !data?.items.length}>
                <Download className="size-4" />
                Xuất Excel
              </Button>
            )
          }
        />

        {totals && totals.row_count > 0 && (
          <p className="text-sm font-medium">
            Tổng {totals.row_count} dòng: số cũ {formatDays(totals.before_days)} → số mới{' '}
            {formatDays(totals.after_days)} (chênh {formatDays(totals.diff_days)}), cộng vào năm
            sau {formatDays(totals.credited_days)} ngày.
          </p>
        )}
        <p className="text-xs text-muted-foreground">
          Số cũ = số còn lại + số đã chuyển đi, dựng lại từ sổ quỹ hiện tại: đơn năm {year} được
          duyệt hoặc hủy sau khi kết sổ sẽ làm số đổi theo. Phần <strong>Sang loại</strong> và <strong>Cộng vào năm
          sau</strong> tính theo cấu hình loại nghỉ hiện hành.
        </p>
      </DialogContent>
    </Dialog>
  )
}
