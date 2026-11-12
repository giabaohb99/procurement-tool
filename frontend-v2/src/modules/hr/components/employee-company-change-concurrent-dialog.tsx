import { Building2 } from 'lucide-react'
import { useState } from 'react'

import {
  AlertDialog,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import type { EmployeeConcurrent } from '../types/employee-concurrent'
import {
  buildCompanyChangeChoice,
  type CompanyChangeConcurrentChoice,
} from '../utils/company-change-concurrent-choice'
import { concurrentPeriodLabel, isConcurrentUnstarted } from '../utils/employee-concurrent-display'
import { todayInVietnamISO } from '../utils/work-roster-range'

interface EmployeeCompanyChangeConcurrentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  oldCompanyName: string
  newCompanyName: string
  /** Dòng ở công ty CŨ còn hiệu lực / sắp tới (`concurrentRowsAtOldCompany`). */
  rows: EmployeeConcurrent[]
  /** `YYYY-MM-DD` giờ VN — để báo dòng chưa bắt đầu sẽ bị xóa. Bỏ trống = hôm nay theo giờ Việt Nam (khớp `vn_today()` ở backend). */
  today?: string
  pending?: boolean
  onConfirm: (choice: CompanyChangeConcurrentChoice) => void
}

/**
 * duoc-CR-755 (Q4) — đổi pháp nhân CHÍNH thì các dòng kiêm nhiệm ở công ty CŨ mặc định KẾT THÚC (đến ngày = hôm qua).
 * Hộp này cho tick từng dòng muốn GIỮ. Dòng chưa bắt đầu (từ ngày ≥ hôm nay) không kết thúc được vào hôm qua nên backend
 * XÓA kèm tệp — nói rõ ngay trên dòng. Dòng ở công ty khác không bao giờ bị đụng, nên không hiện ở đây.
 *
 * Mặc định không tick dòng nào (= kết thúc hết), cùng hướng với luật backend khi không gửi gì.
 */
export function EmployeeCompanyChangeConcurrentDialog({
  open,
  onOpenChange,
  oldCompanyName,
  newCompanyName,
  rows,
  today = todayInVietnamISO(),
  pending = false,
  onConfirm,
}: EmployeeCompanyChangeConcurrentDialogProps) {
  const [keepIds, setKeepIds] = useState<Set<number>>(new Set())

  function toggle(id: number, checked: boolean) {
    setKeepIds((prev) => {
      const next = new Set(prev)
      if (checked) next.add(id)
      else next.delete(id)
      return next
    })
  }

  const hasUnstarted = rows.some((r) => isConcurrentUnstarted(r, today))
  const endingCount = rows.length - rows.filter((r) => keepIds.has(r.id)).length

  return (
    <AlertDialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <AlertDialogContent className="sm:max-w-xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Building2 className="size-5 text-primary" />
            Kiêm nhiệm ở công ty cũ
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">
              <p>
                Pháp nhân chính đổi từ <strong>{oldCompanyName}</strong> sang <strong>{newCompanyName}</strong>. Người này
                còn {rows.length} dòng kiêm nhiệm ở <strong>{oldCompanyName}</strong>. Dòng không tick giữ sẽ kết thúc vào
                hôm qua{hasUnstarted && '; dòng chưa bắt đầu sẽ bị xóa kèm tệp QĐ'}.
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        <ul className="max-h-72 space-y-2 overflow-y-auto">
          {rows.map((row) => {
            const unstarted = isConcurrentUnstarted(row, today)
            const checkboxId = `keep-concurrent-${row.id}`
            return (
              <li key={row.id} className="flex items-start gap-3 rounded-md border p-3">
                <Checkbox
                  id={checkboxId}
                  checked={keepIds.has(row.id)}
                  onCheckedChange={(value) => toggle(row.id, value === true)}
                  disabled={pending}
                  className="mt-0.5"
                />
                <label htmlFor={checkboxId} className="min-w-0 flex-1 space-y-0.5 text-sm">
                  <span className="block font-medium">Giữ: {row.department_name}</span>
                  <span className="block text-xs text-muted-foreground">
                    {[row.position_label, concurrentPeriodLabel(row)].filter(Boolean).join(' · ')}
                  </span>
                  {unstarted && !keepIds.has(row.id) && (
                    <span className="block text-xs text-destructive">Chưa bắt đầu — sẽ bị xóa nếu không giữ.</span>
                  )}
                </label>
              </li>
            )
          })}
        </ul>

        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Hủy</AlertDialogCancel>
          <Button type="button" autoFocus disabled={pending} onClick={() => onConfirm(buildCompanyChangeChoice(rows, keepIds))}>
            {endingCount > 0 ? `Lưu, kết thúc ${endingCount} dòng` : 'Lưu, giữ tất cả'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
