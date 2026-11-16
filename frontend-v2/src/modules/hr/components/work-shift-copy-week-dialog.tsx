import { useRef, useState } from 'react'
import { toast } from 'sonner'

import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { useCopyWorkShiftWeek } from '../hooks/use-work-shifts'
import { BULK_MAX_EMPLOYEES } from '../utils/work-shift-bulk-limits'
import { shiftIsoDate } from '../utils/work-schedule-assignment-mode'
import { formatCopyWeekResult, formatVnDate, toShiftErrorView, type ShiftErrorView } from '../utils/work-shift-errors'
import { WorkShiftErrorAlert } from './work-shift-error-alert'

interface WorkShiftCopyWeekDialogProps {
  open: boolean
  onClose: () => void
  /** Thứ Hai của tuần ĐANG XEM (tuần đích). Tuần nguồn = tuần trước đó. */
  targetWeekStart: string
  employeeIds: number[]
  /** Người dùng đã tick chọn dòng (`true`) hay đang lấy mọi dòng sửa được trên trang (`false`). */
  fromSelection: boolean
  /** Trưởng phòng, không tick dòng: chỉ chép cho người thuộc phòng của mình — nói rõ trong câu. */
  ownDepartmentsOnly?: boolean
  /** Trưởng phòng: ngày đích đã qua bị bỏ qua — báo trước. */
  skipsPastDays: boolean
  nameOf: (employeeId: number) => string | undefined
}

function weekLabel(monday: string): string {
  return `${formatVnDate(monday)} – ${formatVnDate(shiftIsoDate(monday, 6))}`
}

/**
 * Xác nhận "Chép tuần trước" (duoc-CR-761): chép ca XẾP RIÊNG của tuần trước sang tuần đang xem cho các dòng đã chọn
 * (hoặc mọi dòng sửa được trên trang). Ngày theo mẫu tuần không chép. Mặc định KHÔNG ghi đè ngày đã có ca.
 */
export function WorkShiftCopyWeekDialog({
  open,
  onClose,
  targetWeekStart,
  employeeIds,
  fromSelection,
  ownDepartmentsOnly = false,
  skipsPastDays,
  nameOf,
}: WorkShiftCopyWeekDialogProps) {
  const [overwrite, setOverwrite] = useState(false)
  const [error, setError] = useState<ShiftErrorView | null>(null)
  const copy = useCopyWorkShiftWeek()
  const busy = useRef(false)
  const sourceWeekStart = shiftIsoDate(targetWeekStart, -7)
  const tooMany = employeeIds.length > BULK_MAX_EMPLOYEES

  const close = () => {
    setOverwrite(false)
    setError(null)
    onClose()
  }

  const submit = async () => {
    if (busy.current || employeeIds.length === 0 || tooMany) return
    busy.current = true
    setError(null)
    try {
      const result = await copy.mutateAsync({
        employee_ids: employeeIds,
        source_week_start: sourceWeekStart,
        target_week_start: targetWeekStart,
        overwrite,
      })
      toast.success(formatCopyWeekResult(result, nameOf))
      close()
    } catch (err) {
      setError(toShiftErrorView(err, nameOf))
    } finally {
      busy.current = false
    }
  }

  return (
    <Dialog open={open} onOpenChange={(next) => !next && close()}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Chép tuần trước</DialogTitle>
          <DialogDescription>
            Chép ca xếp riêng của tuần {weekLabel(sourceWeekStart)} sang tuần {weekLabel(targetWeekStart)} cho{' '}
            <strong>{employeeIds.length}</strong> nhân sự{' '}
            {fromSelection ? 'đã chọn' : ownDepartmentsOnly ? 'thuộc phòng của bạn trên trang này' : 'trên trang này'}.
          </DialogDescription>
        </DialogHeader>

        <ul className="list-disc space-y-1 pl-5 text-sm text-muted-foreground">
          <li>Chỉ chép những ngày đã xếp ca riêng (kể cả ngày nghỉ do xếp ca). Ngày theo mẫu tuần giữ nguyên.</li>
          {skipsPastDays && <li>Ngày đã qua của tuần này sẽ được bỏ qua.</li>}
          <li>Ngày đã có đơn nghỉ (chờ duyệt hoặc đã duyệt) không chép.</li>
          <li>Không chép cho chính bạn — ca của mình do người khác xếp.</li>
        </ul>

        <label className="flex cursor-pointer items-start gap-2 text-sm">
          <Checkbox checked={overwrite} onCheckedChange={(v) => setOverwrite(v === true)} className="mt-0.5" />
          <span>
            Ghi đè ngày đã có ca ở tuần này
            <span className="block text-xs text-muted-foreground">Bỏ trống thì ngày đã xếp ca ở tuần này được giữ nguyên.</span>
          </span>
        </label>

        {tooMany && (
          <p className="text-sm text-destructive">
            Mỗi lượt tối đa {BULK_MAX_EMPLOYEES} người — tick chọn bớt dòng rồi chép theo từng nhóm.
          </p>
        )}
        {error && <WorkShiftErrorAlert error={error} />}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={close}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={copy.isPending || employeeIds.length === 0 || tooMany}
            onClick={() => void submit()}
          >
            Chép ca
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
