import { Building2, Copy, Target } from 'lucide-react'
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
import { useDocumentClones } from '../hooks/use-document-clones'
import { useIssuePreview } from '../hooks/use-document-links'
import { APPLY_MODE } from '../types/document-record'
import { IssuePreflightSummary } from './issue-preflight-summary'

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
  //  Chỉ hỏi khi hộp thoại thật sự mở — đây là truy vấn nặng nhất của trang.
  const { data: preview } = useIssuePreview(documentId, open)
  const { data: clones } = useDocumentClones(open ? documentId : undefined)

  const soPhapNhanDaKhai = clones?.plan.length ?? 0

  const chonPhamVi = Number(mode) === APPLY_MODE.scope
  //  Backend sẽ từ chối những thứ này — không bày ra nút bấm sẽ hỏng.
  const biChan = (preview?.blockers.length ?? 0) > 0

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Ban hành văn bản</DialogTitle>
          <DialogDescription>
            Ban hành không lùi lại được: số hiệu cấp ra là cấp vĩnh viễn, phiên bản
            bị khóa một chiều. Xem kỹ phần dưới trước khi bấm.
          </DialogDescription>
        </DialogHeader>

        {/*  J04 — bốn thứ sắp xảy ra, đặt TRƯỚC phần chọn cơ chế: người ban hành
             cần biết mình đang ban hành cái gì trước khi chọn áp dụng ra sao. */}
        {preview && <IssuePreflightSummary preview={preview} />}

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

        {!chonPhamVi && (
          <p className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <Building2 className="mt-0.5 size-4 shrink-0 text-amber-700" />
            <span>
              Bản nháp cho pháp nhân con <b>không sinh tự động</b> khi bấm Ban hành —
              mỗi bản là một văn bản thật mang số hiệu vĩnh viễn, nên đó phải là một
              lần bấm có chủ ý. Ban hành xong, mở thẻ «Bản clone ở pháp nhân con» ở
              tab Quan hệ.
              {soPhapNhanDaKhai > 0 && (
                <>
                  {' '}
                  Kế hoạch khai lúc tạo văn bản đã có <b>{soPhapNhanDaKhai}</b> pháp
                  nhân, sẽ được tick sẵn.
                </>
              )}
            </span>
          </p>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={isPending || biChan}
            onClick={() => onConfirm(Number(mode))}
          >
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
