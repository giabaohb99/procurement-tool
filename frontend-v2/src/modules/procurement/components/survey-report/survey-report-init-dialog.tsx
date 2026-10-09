// duoc-CR-614 (09/10/2026) — «Khởi tạo báo cáo mẫu» có CHỌN MẪU. Trước đây nút đổ thẳng mẫu chung
// (5 giai đoạn, bộ hồ sơ chứng từ nhập khẩu); nay thêm mẫu «Tiến độ kế hoạch công việc nhập khẩu»
// theo file Excel của Phòng Thu mua (21 việc, một giai đoạn). Danh sách mẫu lấy từ backend.
import { Loader2 } from 'lucide-react'
import { useState } from 'react'

import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
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
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { cn } from '@/shared/utils/cn'
import { useReportTemplates } from '../../hooks/use-survey-request-report'
import type { ReportOwnerEntity } from '../../types/survey-request-report'

interface SurveyReportInitDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  ownerId: number
  entity: ReportOwnerEntity
  pending: boolean
  /** Mã mẫu đã chọn — chỗ gọi khởi tạo rồi tự đóng hộp khi xong. */
  onConfirm: (template: number) => Promise<unknown>
}

export function SurveyReportInitDialog({
  open,
  onOpenChange,
  ownerId,
  entity,
  pending,
  onConfirm,
}: SurveyReportInitDialogProps) {
  const templates = useReportTemplates(ownerId, entity, open)
  //  `''` = chưa chọn tay → dùng mẫu ĐẦU danh sách (mẫu chung, đúng hành vi cũ của nút).
  const [picked, setPicked] = useState('')
  const once = useSingleFlight()

  const openChanged = useHasChanged(open)
  if (openChanged && open) setPicked('')

  const options = templates.data ?? []
  const selected = picked || String(options[0]?.id ?? '')

  const handleConfirm = () =>
    once(async () => {
      if (!selected) return
      await onConfirm(Number(selected))
      onOpenChange(false)
    })

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        //  Chưa nhập gì để mất nên đóng tự do; chỉ chặn đóng lúc đang gửi.
        if (!next && pending) return
        onOpenChange(next)
      }}
    >
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Khởi tạo báo cáo mẫu</DialogTitle>
          <DialogDescription>
            Chọn mẫu để dựng sẵn giai đoạn và bộ hồ sơ. Sau đó sửa, thêm, xóa tự do ngay trên dạng
            Bảng.
          </DialogDescription>
        </DialogHeader>

        {templates.isLoading ? (
          <p className="flex items-center gap-2 text-sm text-muted-foreground">
            <Loader2 className="size-4 animate-spin" />
            Đang tải danh sách mẫu…
          </p>
        ) : templates.isError ? (
          <p className="text-sm text-destructive">
            Không tải được danh sách mẫu. Đóng hộp rồi thử lại; nếu vẫn lỗi thì báo quản trị hệ
            thống.
          </p>
        ) : (
          <RadioGroup value={selected} onValueChange={setPicked} className="gap-2">
            {options.map((option) => {
              const id = `report-template-${option.id}`
              return (
                <Label
                  key={option.id}
                  htmlFor={id}
                  className={cn(
                    'flex cursor-pointer items-start gap-3 rounded-lg border p-3 font-normal',
                    selected === String(option.id) && 'border-primary bg-primary/5',
                  )}
                >
                  <RadioGroupItem id={id} value={String(option.id)} className="mt-0.5" />
                  <span className="space-y-1">
                    <span className="block text-sm font-semibold">{option.name}</span>
                    <span className="block text-xs text-muted-foreground">
                      {option.phase_count} giai đoạn · {option.doc_count} hồ sơ — {option.description}
                    </span>
                  </span>
                </Label>
              )
            })}
          </RadioGroup>
        )}

        <DialogFooter className="gap-2">
          <Button
            type="button"
            variant="outline"
            disabled={pending}
            onClick={() => onOpenChange(false)}
          >
            Hủy
          </Button>
          <Button
            type="button"
            disabled={pending || !selected || templates.isLoading || templates.isError}
            onClick={handleConfirm}
          >
            {pending && <Loader2 className="animate-spin" />}
            Khởi tạo
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
