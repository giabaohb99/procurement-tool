import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import type { WorkScheduleAssignment } from '../types/work-schedule'
import { describeAssignmentTarget } from '../utils/describe-assignment-target'

interface WorkScheduleAssignmentViewDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  item: WorkScheduleAssignment
  /** Câu nói vì sao chỉ xem được — Trưởng phòng cần biết dòng nào là của Nhân sự. */
  reason: string
}

/**
 * Hộp CHỈ XEM một dòng gán lịch — mở khi người bấm dòng không có quyền sửa dòng đó (duoc-CR-757 lượt 2). Không có
 * nút Lưu / Xóa: để hộp sửa với nút Lưu thì người dùng gõ xong mới ăn 403.
 */
export function WorkScheduleAssignmentViewDialog({
  open,
  onOpenChange,
  item,
  reason,
}: WorkScheduleAssignmentViewDialogProps) {
  const rows: { label: string; value: string; multiline?: boolean }[] = [
    { label: 'Cấp áp dụng', value: item.target_level_label },
    { label: 'Đối tượng áp dụng', value: describeAssignmentTarget(item) },
    { label: 'Mẫu lịch', value: item.schedule_name },
    { label: 'Hiệu lực từ ngày', value: formatDate(item.effective_from) },
    { label: 'Đến ngày', value: item.effective_to ? formatDate(item.effective_to) : 'Không thời hạn' },
    { label: 'Ghi chú', value: item.note, multiline: true },
  ]

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-xl">
        <DialogHeader>
          <DialogTitle>Dòng gán lịch</DialogTitle>
          <DialogDescription>{reason}</DialogDescription>
        </DialogHeader>
        <div className="grid gap-4 sm:grid-cols-2">
          {rows.map((row) => (
            <div key={row.label} className={cn('space-y-1.5', row.multiline && 'sm:col-span-2')}>
              <Label>{row.label}</Label>
              <ReadOnlyValue multiline={row.multiline}>{row.value}</ReadOnlyValue>
            </div>
          ))}
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
