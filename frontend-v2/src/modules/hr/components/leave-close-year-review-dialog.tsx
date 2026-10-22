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
import { closeYearReviewExportUrl } from '../api/leave-api'
import { useCloseYearReview } from '../hooks/use-leave'
import type { LeaveCloseYearReviewRow } from '../types/leave'

/** Số ngày: tối đa 2 số lẻ, bỏ đuôi `.00` — `8` chứ không `8.00`. */
function formatDays(value: number): string {
  return Number.isInteger(value) ? String(value) : value.toFixed(2).replace(/0$/, '')
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

  const columns = useMemo<DataTableColumn<LeaveCloseYearReviewRow>[]>(
    () => [
      { key: 'employee', header: 'Nhân sự', width: 220, hideable: false, wrap: true,
        cell: (r) => `${r.employee_name} (${r.employee_code})` },
      { key: 'source', header: 'Loại nghỉ', width: 150, wrap: true, cell: (r) => r.source_type_name },
      { key: 'before', header: 'Số cũ (trước)', width: 110, align: 'right',
        cell: (r) => formatDays(r.before_days) },
      { key: 'after', header: 'Số mới (sau)', width: 110, align: 'right',
        cell: (r) => formatDays(r.after_days) },
      { key: 'diff', header: 'Chênh', width: 90, align: 'right',
        cell: (r) => formatDays(r.diff_days) },
      { key: 'dest', header: 'Sang loại', width: 150, wrap: true,
        cell: (r) => r.dest_type_name || 'Chưa khai' },
      { key: 'credited', header: 'Cộng vào năm sau', width: 130, align: 'right',
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
      <DialogContent className="sm:max-w-4xl">
        <DialogHeader>
          <DialogTitle>Đối chiếu kết sổ phép năm {year}</DialogTitle>
          <DialogDescription>
            Số dư năm {year} trước và sau khi kết sổ, kèm phần chuyển sang năm {(year ?? 0) + 1}.
          </DialogDescription>
        </DialogHeader>

        <DataTable
          columns={columns}
          rows={data?.items}
          getRowId={(r) => `${r.employee_id}-${r.source_type_id}`}
          isLoading={isLoading}
          isError={isError}
          emptyMessage={`Chưa có dòng nào được kết sổ cho năm ${year}.`}
          storageKey="hr.leave-close-year-review"
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
          duyệt hoặc hủy sau khi kết sổ sẽ làm số đổi theo. Phần «Sang loại» và «Cộng vào năm
          sau» tính theo cấu hình loại nghỉ hiện hành.
        </p>
      </DialogContent>
    </Dialog>
  )
}
