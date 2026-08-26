import { useState } from 'react'
import { AtSign, Building2, Target, TriangleAlert } from 'lucide-react'

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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { cloneTargetsFromScopes } from '../helpers/clone-targets-from-scopes'
import { useIssueMailboxes, useIssuePreview } from '../hooks/use-document-links'
import { useDocumentScopes } from '../hooks/use-document-scopes'
import { APPLY_MODE } from '../types/document-record'
import { IssuePreflightSummary } from './issue-preflight-summary'

/** Giá trị của dòng «Địa chỉ mặc định của hệ thống» trong ô chọn hộp thư. */
const SYSTEM_MAILBOX = '0'

interface DocumentIssueDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pháp nhân ban hành — nơi bản gốc nằm, không tự clone về chính nó. */
  issuerCompanyId: number
  isPending?: boolean
  /** `mailboxId` rỗng = gửi bằng địa chỉ hệ thống, y như trước 26/08/2026. */
  onConfirm: (applyMode: number, mailboxId?: number) => void
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
  const { data: mailboxes } = useIssueMailboxes(documentId, open)

  const [mailboxValue, setMailboxValue] = useState(SYSTEM_MAILBOX)

  //  Đóng hộp thoại là quên lựa chọn. Làm ở ĐƯỜNG ĐÓNG chứ không bằng `useEffect`
  //  theo dõi `open`: đặt state trong effect gây render dây chuyền (đúng cảnh báo
  //  `react-hooks/set-state-in-effect`), mà ở đây không cần — mọi đường người
  //  dùng đóng hộp thoại đều đi qua đúng hàm này.
  const closeAndReset = (next: boolean) => {
    if (!next) setMailboxValue(SYSTEM_MAILBOX)
    onOpenChange(next)
  }

  const usableMailboxes = (mailboxes ?? []).filter((row) => row.ready)
  const unusableCount = (mailboxes ?? []).length - usableMailboxes.length

  //  Đọc thẳng PHẠM VI đang lưu chứ không đọc kế hoạch clone khai lúc tạo: phạm
  //  vi còn sửa được ở tab Phạm vi sau khi tạo, lấy bản khai cũ thì hộp thoại
  //  nói một đằng mà văn bản áp một nẻo. Cùng một luật với màn tạo văn bản.
  const companiesGettingCopy = cloneTargetsFromScopes(scopes?.items ?? [], issuerCompanyId)
  const splitPrivateCopy = companiesGettingCopy.length > 0
  const applyMode = splitPrivateCopy ? APPLY_MODE.clone : APPLY_MODE.scope

  //  Gọi tên từng nơi thay vì chỉ đếm số: người ban hành phải nhận ra ngay có
  //  nơi nào lọt vào danh sách mà lẽ ra không nên có.
  const companyName = companiesGettingCopy
    .map((id) => scopes?.items.find((row) => row.company_id === id)?.company_name)
    .filter(Boolean)
    .join(', ')

  //  Backend sẽ từ chối những thứ này — không bày ra nút bấm sẽ hỏng.
  const blocked = (preview?.blockers.length ?? 0) > 0

  return (
    <Dialog open={open} onOpenChange={closeAndReset}>
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

        {splitPrivateCopy ? (
          <div className="space-y-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
            <p className="flex items-start gap-2">
              <Building2 className="mt-0.5 size-4 shrink-0 text-amber-700" />
              <span>
                Phạm vi đang khai <b>{companiesGettingCopy.length}</b> pháp nhân ngoài
                nơi ban hành{companyName && <> — {companyName}</>}, nên mỗi nơi sẽ có{' '}
                <b>bản riêng</b>: số hiệu riêng, người ký riêng, hiệu lực riêng.
              </span>
            </p>
            {/*  Chốt 20/08/2026: clone SINH TỰ ĐỘNG lúc ban hành. Trước đó phải
                 vào thẻ Quan hệ bấm tay. Vì mỗi bản là một văn bản thật mang số
                 hiệu vĩnh viễn, chỗ chặn nhầm lẫn dời về đây — gọi tên từng pháp
                 nhân ở trên trước khi cho bấm. */}
            <p className="pl-6">
              Bấm Ban hành là <b>{companiesGettingCopy.length} bản nháp sinh ra ngay</b> ở
              các pháp nhân trên, mỗi nơi một bản để họ sửa cho đúng công ty mình rồi tự
              ban hành. Danh sách này lấy từ tab <b>Phạm vi</b> — sai chỗ nào thì thoát ra
              sửa ở đó trước, vì số hiệu cấp ra là cấp vĩnh viễn.
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

        {/*  HỘP THƯ GỬI THÔNG BÁO (26/08/2026). Chỉ bày ra khi người đang đăng
             nhập thật sự được cấp hộp thư nào đó — không ai được cấp thì thêm
             một ô chọn có đúng một dòng chỉ làm rối màn hình. */}
        {(mailboxes?.length ?? 0) > 0 && (
          <div className="space-y-1.5">
            <Label htmlFor="issue-mailbox" className="flex items-center gap-2">
              <AtSign className="size-4 text-muted-foreground" />
              Gửi thông báo danh nghĩa
            </Label>
            <Select value={mailboxValue} onValueChange={setMailboxValue}>
              <SelectTrigger id="issue-mailbox">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={SYSTEM_MAILBOX}>Địa chỉ mặc định của hệ thống</SelectItem>
                {usableMailboxes.map((row) => (
                  <SelectItem key={row.id} value={String(row.id)}>
                    {row.display_name} &lt;{row.email}&gt;
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <p className="text-xs text-muted-foreground">
              Người nhận sẽ thấy thư đến từ địa chỉ này. Chọn đúng phòng ban đứng tên
              phát hành, thay vì để thư mang địa chỉ cá nhân của bạn.
            </p>
            {/*  Hộp thư thiếu SMTP vẫn phải NÓI RA. Lặng lẽ bỏ khỏi danh sách thì
                 người được cấp mở ra không thấy hộp thư của mình và không hiểu
                 vì sao — rồi đi hỏi vòng quanh. */}
            {unusableCount > 0 && (
              <p className="flex items-start gap-2 text-xs text-amber-700">
                <TriangleAlert className="mt-0.5 size-3.5 shrink-0" />
                <span>
                  Có <b>{unusableCount}</b> hộp thư bạn được cấp nhưng chưa khai đủ máy
                  chủ gửi nên chưa chọn được. Báo quản trị bổ sung ở màn Hộp thư gửi.
                </span>
              </p>
            )}
          </div>
        )}

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => closeAndReset(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            disabled={isPending || blocked}
            onClick={() =>
              onConfirm(
                applyMode,
                mailboxValue === SYSTEM_MAILBOX ? undefined : Number(mailboxValue),
              )
            }
          >
            Ban hành
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
