import { AlertTriangle, Building2, Copy, Target } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { RadioGroup, RadioGroupItem } from '@/shared/ui/radio-group'
import { cn } from '@/shared/utils/cn'
import { useDocumentScopes } from '../hooks/use-document-scopes'
import { APPLY_MODE } from '../types/document-record'

interface DocumentIssueDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Cơ chế đang ghi trên bản ghi — mở hộp thoại là chọn sẵn cái đó. */
  currentMode: number
  isPending?: boolean
  onConfirm: (applyMode: number) => void
}

/**
 * MÀN CHỌN CƠ CHẾ LÚC BAN HÀNH (F13).
 *
 * Hai cơ chế **không mâu thuẫn nhau** — chúng dùng cho hai tình huống khác nhau,
 * và tài liệu yêu cầu nói rõ khác nhau ở chỗ nào ngay trên màn hình, không bắt
 * người ban hành đi tra tài liệu.
 *
 * Chốt LÚC BAN HÀNH chứ không phải lúc soạn: tới đây người ban hành mới biết nội
 * dung cuối cùng có dùng chung được cho mọi pháp nhân hay không.
 */
export function DocumentIssueDialog({
  documentId,
  open,
  onOpenChange,
  currentMode,
  isPending = false,
  onConfirm,
}: DocumentIssueDialogProps) {
  const [mode, setMode] = useState(String(currentMode || APPLY_MODE.scope))
  const { data: scopes } = useDocumentScopes(documentId)

  const chonPhamVi = Number(mode) === APPLY_MODE.scope
  //  Cảnh báo đúng lúc đáng cảnh báo nhất: sắp ban hành một văn bản gắn phạm vi
  //  mà chưa khai dòng phạm vi nào — theo quy tắc của hệ thì nó không tới ai.
  const khongToiAi = chonPhamVi && scopes?.applies_to_nobody

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Ban hành văn bản</DialogTitle>
          <DialogDescription>
            Văn bản sẽ được cấp số và phiên bản hiện tại bị khóa lại. Chọn cách áp
            dụng cho các pháp nhân con.
          </DialogDescription>
        </DialogHeader>

        <RadioGroup value={mode} onValueChange={setMode} className="gap-3">
          <ModeOption
            value={String(APPLY_MODE.scope)}
            picked={chonPhamVi}
            icon={Target}
            title="Một văn bản, gắn phạm vi áp dụng"
            recommended
            when="Nội dung giống hệt cho mọi công ty con — thông báo nghỉ Tết, quy chế bảo mật thông tin."
            result="Một số hiệu, một nơi sửa. Sửa một lần là 13 công ty thấy bản mới ngay."
          />
          <ModeOption
            value={String(APPLY_MODE.clone)}
            picked={!chonPhamVi}
            icon={Copy}
            title="Clone thành bản nháp riêng cho từng pháp nhân"
            when="Pháp luật buộc pháp nhân con tự đứng tên, hoặc nội dung phải khác — hạn mức khác, ngành nghề khác."
            result="Mỗi công ty một số hiệu riêng, người ký riêng, hiệu lực riêng."
          />
        </RadioGroup>

        {khongToiAi && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Văn bản này <b>chưa khai phạm vi áp dụng nào</b> nên sẽ không hiện
              trong mục «Văn bản áp dụng cho tôi» của bất kỳ ai. Để trống không có
              nghĩa là áp cho mọi người. Vẫn ban hành được — nhưng nên khai phạm vi
              ở tab Thông tin trước.
            </span>
          </p>
        )}

        {!chonPhamVi && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <Building2 className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Lựa chọn được <b>ghi lại</b> và vào nhật ký, nhưng bản nháp cho pháp
              nhân con <b>chưa được sinh tự động</b> — phần clone (F06–F12) chưa mở,
              đang chờ chốt hai câu hỏi nghiệp vụ. Tạm thời phải tạo tay ở từng
              pháp nhân.
            </span>
          </p>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" disabled={isPending} onClick={() => onConfirm(Number(mode))}>
            Ban hành
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

interface ModeOptionProps {
  value: string
  picked: boolean
  icon: React.ComponentType<{ className?: string }>
  title: string
  when: string
  result: string
  recommended?: boolean
}

/** Một lựa chọn cơ chế — nói rõ *dùng khi nào* và *kết quả ra sao*. */
function ModeOption({
  value,
  picked,
  icon: Icon,
  title,
  when,
  result,
  recommended = false,
}: ModeOptionProps) {
  return (
    <label
      className={cn(
        'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
        picked ? 'border-primary bg-accent/40' : 'hover:bg-muted/50',
      )}
    >
      <RadioGroupItem value={value} className="mt-0.5" />
      <span className="min-w-0 flex-1">
        <span className="flex items-center gap-2 font-medium">
          <Icon className="size-4 text-muted-foreground" />
          {title}
          {recommended && (
            <span className="font-normal text-muted-foreground">— mặc định</span>
          )}
        </span>
        <span className="mt-1 block text-muted-foreground">
          <b>Dùng khi:</b> {when}
        </span>
        <span className="block text-muted-foreground">
          <b>Kết quả:</b> {result}
        </span>
      </span>
    </label>
  )
}
