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
import {
  concurrentKindLabel,
  concurrentPeriodLabel,
  concurrentPlaceLabel,
  isConcurrentUnstarted,
} from '../utils/employee-concurrent-display'
import { todayInVietnamISO } from '../utils/work-roster-range'

interface EmployeeCompanyChangeConcurrentDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  oldCompanyName: string
  newCompanyName: string
  /** Dòng sẽ kết thúc (`concurrentRowsEndingOnCompanyChange`): loại Phòng ban ở công ty cũ + loại Công ty trùng công ty mới. */
  rows: EmployeeConcurrent[]
  /** Đã có dòng loại Công ty ở công ty cũ còn hiệu lực — không hỏi giữ nữa (backend cũng bỏ qua). */
  oldCompanyKept?: boolean
  /** `YYYY-MM-DD` giờ VN — để báo dòng chưa bắt đầu sẽ bị xóa. Bỏ trống = hôm nay theo giờ Việt Nam (khớp `vn_today()` ở backend). */
  today?: string
  pending?: boolean
  onConfirm: (choice: CompanyChangeConcurrentChoice) => void
}

/**
 * duoc-CR-756 (Q4) — đổi pháp nhân CHÍNH A → C. Liệt kê dòng sẽ KẾT THÚC (đến ngày = hôm qua): dòng loại Phòng ban ở A
 * (phòng đó không còn là phòng của công ty hiện tại) và dòng loại Công ty trùng C (kiêm nhiệm chính công ty mình là
 * thừa). Dòng chưa bắt đầu (từ ngày ≥ hôm nay) không kết thúc được vào hôm qua nên backend XÓA kèm tệp — nói rõ trên dòng.
 *
 * Chỉ còn MỘT câu hỏi: **Vẫn kiêm nhiệm ở công ty cũ** → backend thêm một dòng loại Công ty (A) từ hôm nay, qua chốt
 * L2 loại Công ty (người lưu phải có phạm vi ghi toàn công ty A). Mặc định không tick (= không giữ), cùng hướng với luật
 * backend khi không gửi gì. Đổi cả phòng chính thì câu này thay luôn câu "giữ phòng cũ" (câu hỏi mở 5).
 */
export function EmployeeCompanyChangeConcurrentDialog({
  open,
  onOpenChange,
  oldCompanyName,
  newCompanyName,
  rows,
  oldCompanyKept = false,
  today = todayInVietnamISO(),
  pending = false,
  onConfirm,
}: EmployeeCompanyChangeConcurrentDialogProps) {
  const [keepOld, setKeepOld] = useState(false)
  const hasUnstarted = rows.some((r) => isConcurrentUnstarted(r, today))

  return (
    <AlertDialog open={open} onOpenChange={(next) => !pending && onOpenChange(next)}>
      <AlertDialogContent className="sm:max-w-xl">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            <Building2 className="size-5 text-primary" />
            Kiêm nhiệm khi đổi pháp nhân
          </AlertDialogTitle>
          <AlertDialogDescription asChild>
            <div className="space-y-2 text-sm">
              <p>
                Pháp nhân chính đổi từ <strong>{oldCompanyName}</strong> sang <strong>{newCompanyName}</strong>.
                {rows.length > 0 ? (
                  <>
                    {' '}
                    {rows.length} dòng kiêm nhiệm dưới đây sẽ kết thúc vào hôm qua
                    {hasUnstarted && '; dòng chưa bắt đầu sẽ bị xóa kèm tệp QĐ'}.
                  </>
                ) : (
                  ' Không có dòng kiêm nhiệm nào phải kết thúc.'
                )}
              </p>
            </div>
          </AlertDialogDescription>
        </AlertDialogHeader>

        {rows.length > 0 && (
          <ul className="max-h-60 space-y-2 overflow-y-auto">
            {rows.map((row) => (
              <li key={row.id} className="space-y-0.5 rounded-md border p-3 text-sm">
                <span className="block font-medium">
                  {concurrentKindLabel(row)}: {concurrentPlaceLabel(row)}
                </span>
                <span className="block text-xs text-muted-foreground">
                  {[row.position_label, concurrentPeriodLabel(row)].filter(Boolean).join(' · ')}
                </span>
                {isConcurrentUnstarted(row, today) && (
                  <span className="block text-xs text-destructive">Chưa bắt đầu — sẽ bị xóa.</span>
                )}
              </li>
            ))}
          </ul>
        )}

        {oldCompanyKept ? (
          <p className="rounded-md border bg-muted/40 p-3 text-sm text-muted-foreground">
            Người này đã có dòng kiêm nhiệm loại Công ty ở <strong>{oldCompanyName}</strong> nên vẫn được tính là người
            của công ty đó.
          </p>
        ) : (
          <label htmlFor="keep-old-company-concurrent" className="flex items-start gap-3 rounded-md border p-3 text-sm">
            <Checkbox
              id="keep-old-company-concurrent"
              checked={keepOld}
              onCheckedChange={(value) => setKeepOld(value === true)}
              disabled={pending}
              className="mt-0.5"
            />
            <span className="min-w-0 flex-1 space-y-0.5">
              <span className="block font-medium">
                Vẫn kiêm nhiệm ở công ty cũ (thêm dòng loại Công ty từ hôm nay)
              </span>
              <span className="block text-xs text-muted-foreground">
                Người này vẫn được tính là người của {oldCompanyName} theo bậc vai trò đang có. Người lưu cần quyền ghi
                hồ sơ bậc Công ty ở đó.
              </span>
            </span>
          </label>
        )}

        <AlertDialogFooter>
          <AlertDialogCancel disabled={pending}>Hủy</AlertDialogCancel>
          <Button
            type="button"
            autoFocus
            disabled={pending}
            onClick={() => onConfirm(buildCompanyChangeChoice(!oldCompanyKept && keepOld))}
          >
            {rows.length > 0 ? `Lưu, kết thúc ${rows.length} dòng` : 'Lưu'}
          </Button>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  )
}
