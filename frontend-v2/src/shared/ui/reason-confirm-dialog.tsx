import { Loader2 } from 'lucide-react'
import { useId, useState } from 'react'

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
import { Textarea } from '@/shared/ui/textarea'

interface ReasonConfirmDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  title: string
  /** Câu giải thích hậu quả của thao tác — người bấm cần biết trước khi gõ lý do. */
  description?: string
  /** Nhãn ô nhập; mặc định "Lý do". */
  label?: string
  placeholder?: string
  confirmText: string
  /** Việc không hoàn tác được thì nút xác nhận tô đỏ. */
  destructive?: boolean
  pending?: boolean
  onConfirm: (reason: string) => void
}

/**
 * Hộp xác nhận có Ô NHẬP LÝ DO — dùng cho những thao tác mà lý do được ghi vào
 * nhật ký và người khác sẽ đọc lại (bãi bỏ văn bản, trả lại bản nháp…).
 *
 * Có mặt để thay `window.prompt`: hộp của trình duyệt không theo giao diện hệ
 * thống, không nhập được nhiều dòng, không chặn được lý do bỏ trống, và trên
 * một số trình duyệt còn bị chặn thẳng.
 *
 * Chỉ là hộp thoại, KHÔNG kèm nút mở: nút mở nằm ở trang gọi vì mỗi chỗ một
 * nhãn, một biểu tượng và một lớp kiểm quyền riêng.
 */
export function ReasonConfirmDialog({
  open,
  onOpenChange,
  title,
  description,
  label = 'Lý do',
  placeholder,
  confirmText,
  destructive = false,
  pending = false,
  onConfirm,
}: ReasonConfirmDialogProps) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          {description && <DialogDescription>{description}</DialogDescription>}
        </DialogHeader>

        <ReasonField
          label={label}
          placeholder={placeholder}
          confirmText={confirmText}
          destructive={destructive}
          pending={pending}
          onCancel={() => onOpenChange(false)}
          onConfirm={onConfirm}
        />
      </DialogContent>
    </Dialog>
  )
}

type ReasonFieldProps = Pick<
  ReasonConfirmDialogProps,
  'placeholder' | 'confirmText' | 'destructive' | 'pending' | 'onConfirm'
> & { label: string; onCancel: () => void }

/**
 * Ô nhập + hai nút, tách riêng để chữ đã gõ **tự mất khi hộp đóng**: hộp đóng
 * là nhánh này rời khỏi cây, mở lại là dựng mới. Giữ chung một chỗ với hộp thì
 * phải tự dọn bằng effect, mà lý do của lần hỏi trước còn nằm đó là dễ gửi
 * nhầm cho văn bản khác.
 */
function ReasonField({
  label,
  placeholder,
  confirmText,
  destructive = false,
  pending = false,
  onCancel,
  onConfirm,
}: ReasonFieldProps) {
  const fieldId = useId()
  const [reason, setReason] = useState('')
  const ready = reason.trim().length > 0 && !pending

  return (
    <>
      <div className="space-y-2">
        <Label htmlFor={fieldId}>{label}</Label>
        <Textarea
          id={fieldId}
          autoFocus
          rows={3}
          maxLength={1000}
          value={reason}
          placeholder={placeholder}
          onChange={(event) => setReason(event.target.value)}
          // Ctrl/⌘ + Enter để gửi: ô nhiều dòng thì Enter phải là xuống dòng.
          onKeyDown={(event) => {
            if (event.key === 'Enter' && (event.metaKey || event.ctrlKey) && ready) {
              event.preventDefault()
              onConfirm(reason.trim())
            }
          }}
        />
      </div>

      <DialogFooter>
        <Button type="button" variant="outline" onClick={onCancel}>
          Hủy
        </Button>
        <Button
          type="button"
          variant={destructive ? 'destructive' : 'default'}
          disabled={!ready}
          onClick={() => onConfirm(reason.trim())}
        >
          {pending && <Loader2 className="size-4 animate-spin" />}
          {confirmText}
        </Button>
      </DialogFooter>
    </>
  )
}
