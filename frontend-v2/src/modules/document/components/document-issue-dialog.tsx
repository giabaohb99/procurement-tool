import { Building2, Target } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { cloneTargetsFromScopes } from '../helpers/clone-targets-from-scopes'
import { useIssuePreview } from '../hooks/use-document-links'
import { useDocumentScopes } from '../hooks/use-document-scopes'
import { APPLY_MODE } from '../types/document-record'
import { IssuePreflightSummary } from './issue-preflight-summary'

interface DocumentIssueDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pháp nhân ban hành — nơi bản gốc nằm, không tự clone về chính nó. */
  issuerCompanyId: number
  isPending?: boolean
  onConfirm: (applyMode: number) => void
}

/**
 * MÀN XÁC NHẬN BAN HÀNH (F13).
 *
 * **Không hỏi cơ chế áp dụng nữa** — nó suy từ phạm vi khai ở bước 2 lúc tạo văn
 * bản: có khai pháp nhân nào ngoài nơi ban hành thì pháp nhân đó nhận bản riêng,
 * không khai thì văn bản chỉ áp trong pháp nhân gốc. Hỏi lại ở đây là hỏi lần
 * thứ hai cùng một câu, mà câu trả lời sau lại đè lên phần đã khai — hai chỗ nói
 * khác nhau về cùng một văn bản (chốt 19/08/2026).
 *
 * Việc còn lại của hộp thoại này là **nói rõ cái sắp xảy ra** rồi mới cho bấm:
 * số hiệu cấp ra là vĩnh viễn, phiên bản khóa một chiều.
 */
export function DocumentIssueDialog({
  documentId,
  open,
  onOpenChange,
  issuerCompanyId,
  isPending = false,
  onConfirm,
}: DocumentIssueDialogProps) {
  //  Chỉ hỏi khi hộp thoại thật sự mở — đây là truy vấn nặng nhất của trang.
  const { data: preview } = useIssuePreview(documentId, open)
  const { data: scopes } = useDocumentScopes(open ? documentId : undefined)

  //  Đọc thẳng PHẠM VI đang lưu chứ không đọc kế hoạch clone khai lúc tạo: phạm
  //  vi còn sửa được ở tab Phạm vi sau khi tạo, lấy bản khai cũ thì hộp thoại
  //  nói một đằng mà văn bản áp một nẻo. Cùng một luật với màn tạo văn bản.
  const phapNhanNhanBanRieng = cloneTargetsFromScopes(scopes?.items ?? [], issuerCompanyId)
  const tachBanRieng = phapNhanNhanBanRieng.length > 0
  const applyMode = tachBanRieng ? APPLY_MODE.clone : APPLY_MODE.scope

  //  Gọi tên từng nơi thay vì chỉ đếm số: người ban hành phải nhận ra ngay có
  //  nơi nào lọt vào danh sách mà lẽ ra không nên có.
  const tenPhapNhan = phapNhanNhanBanRieng
    .map((id) => scopes?.items.find((row) => row.company_id === id)?.company_name)
    .filter(Boolean)
    .join(', ')

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

        {/*  J04 — bốn thứ sắp xảy ra. */}
        {preview && <IssuePreflightSummary preview={preview} />}

        {tachBanRieng ? (
          <div className="space-y-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <p className="flex items-start gap-2">
              <Building2 className="mt-0.5 size-4 shrink-0 text-amber-700" />
              <span>
                Phạm vi đang khai <b>{phapNhanNhanBanRieng.length}</b> pháp nhân ngoài
                nơi ban hành{tenPhapNhan && <> — {tenPhapNhan}</>}, nên mỗi nơi sẽ có{' '}
                <b>bản riêng</b>: số hiệu riêng, người ký riêng, hiệu lực riêng.
              </span>
            </p>
            <p className="pl-6">
              Bản nháp <b>không sinh tự động</b> khi bấm Ban hành — mỗi bản là một văn
              bản thật mang số hiệu vĩnh viễn, nên đó phải là một lần bấm có chủ ý. Ban
              hành xong, mở thẻ «Bản clone ở pháp nhân con» ở tab Quan hệ; các pháp nhân
              đã khai được tick sẵn.
            </p>
          </div>
        ) : (
          <p className="flex items-start gap-2 rounded-md border bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            <Target className="mt-0.5 size-4 shrink-0" />
            <span>
              Phạm vi không khai pháp nhân nào khác, nên văn bản áp dụng cho{' '}
              <b>toàn bộ pháp nhân ban hành</b> — mọi phòng ban, mọi nhân sự ở đó. Muốn
              nơi khác có bản riêng thì khai thêm pháp nhân ở tab Phạm vi rồi ban hành.
            </span>
          </p>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" disabled={isPending || biChan} onClick={() => onConfirm(applyMode)}>
            Ban hành
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
