import { AlertTriangle, ExternalLink } from 'lucide-react'
import { useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { nextVersionNo } from '../helpers/next-version-no'
import { useDocumentVersions, useOpenVersion } from '../hooks/use-document-versions'
import { useDocumentWorkflow } from '../hooks/use-documents'
import { CHANGE_KIND } from '../types/document-record'

/** Hai kết luận có thể có sau khi rà. */
const RESULTS = { giuNguyen: 'giu-nguyen', suaTheo: 'sua-theo' } as const

interface DocumentReviewDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Câu backend ghi lúc bật cờ — "Bản gốc đã lên phiên bản mới ngày…". */
  note?: string
  /** Bản gốc để đối chiếu (có với bản riêng của pháp nhân con). */
  sourceDocumentId?: number | null
}

/**
 * RÀ VĂN BẢN theo bản gốc — và mở luôn phiên bản mới nếu rà ra là phải sửa.
 *
 * Ca dùng: pháp nhân mẹ ban hành phiên bản mới, mọi bản riêng ở pháp nhân con bị
 * đánh dấu «cần rà lại» (`clone_service.mark_clones_for_review`). Người phụ trách
 * bản riêng mở bản gốc ra đối chiếu rồi kết luận **một trong hai**:
 *
 *  - **Giữ nguyên** — phần của pháp nhân mình không đụng tới chỗ vừa sửa. Chỉ gỡ
 *    dấu và ghi kết luận vào nhật ký.
 *  - **Sửa theo bản gốc** — gỡ dấu VÀ mở ngay một phiên bản mới của bản riêng để
 *    ngồi sửa.
 *
 * Trước đây chỗ này chỉ có một hộp hỏi lý do rồi gỡ dấu. Rà ra là phải sửa thì
 * người dùng còn phải tự sang tab «Phiên bản», tự bấm «Mở phiên bản mới», rồi gõ
 * lại y nguyên câu vừa gõ vào ô «Sửa gì» — mà đó lại là ca THƯỜNG GẶP nhất, vì
 * bản gốc có sửa thì mới có cái để rà.
 *
 * ⚠️ Thứ tự chạy: **mở phiên bản trước, gỡ dấu sau.** Mở phiên bản là việc hay
 * hỏng nhất (409 khi người khác đang giữ bản nháp, 400 khi bản đang dùng chưa
 * duyệt xong). Gỡ dấu trước rồi mở hỏng thì văn bản mất dấu «cần rà lại» mà chưa
 * ai sửa gì — cái dấu đó là thứ duy nhất nhắc còn việc.
 *
 * Hệ thống **không bao giờ tự chép nội dung** từ bản gốc sang bản riêng: nó chỉ
 * mở một bản nháp trống-y-như-bản-cũ để người rà tự sửa (F11 —
 * `doc/erp/van-thu/05-vong-doi-phien-ban.md`).
 */
export function DocumentReviewDialog({
  documentId,
  open,
  onOpenChange,
  note,
  sourceDocumentId,
}: DocumentReviewDialogProps) {
  const [ketQua, setKetQua] = useState<string>(RESULTS.suaTheo)
  const [ketLuan, setKetLuan] = useState('')
  const [changeKind, setChangeKind] = useState(String(CHANGE_KIND.major))

  const { confirmReviewed } = useDocumentWorkflow(documentId)
  const openVersion = useOpenVersion(documentId)

  //  Danh sách phiên bản đã nằm sẵn trong cache của trang chi tiết — đây không
  //  phải một lượt gọi thêm.
  const { data: versions = [] } = useDocumentVersions(documentId)
  const openDraft = versions.find((version) => !version.is_locked)

  //  Cùng điều kiện backend kiểm (`version_service.open_new_version`), nói
  //  TRƯỚC cho đỡ bấm vào rồi nhận lỗi.
  const canOpenNewVersion =
    !openDraft && versions.some((version) => version.is_current && version.is_locked)
  const blockedReason = openDraft
    ? 'Đang có bản nháp mở — sửa tiếp vào bản nháp đó, không mở thêm được bản nữa.'
    : 'Chỉ mở phiên bản mới từ một bản ĐÃ DUYỆT. Bản đang dùng của văn bản này chưa duyệt xong.'

  const openNewVersion = ketQua === RESULTS.suaTheo && canOpenNewVersion
  const isRunning = openVersion.isPending || confirmReviewed.isPending

  async function handleSubmit() {
    const summaryText = ketLuan.trim()
    try {
      if (openNewVersion) {
        await openVersion.mutateAsync({
          change_kind: Number(changeKind),
          //  Kết luận rà CHÍNH LÀ câu "sửa gì" của phiên bản mới — bắt gõ lại
          //  lần nữa thì người ta gõ "sửa theo bản gốc" cho xong việc.
          change_summary: summaryText,
          change_reason: note || 'Rà lại theo phiên bản mới của bản gốc',
          effective_from: null,
        })
      }
      await confirmReviewed.mutateAsync(summaryText)
      handleOpenChange(false)
    } catch {
      //  Câu lỗi thật đã nằm trong `openVersion.error` (hiện ngay trong hộp
      //  thoại) hoặc đã bay lên toast của `confirmReviewed`. Nuốt ở đây để hộp
      //  thoại Ở LẠI với nội dung người dùng vừa gõ.
    }
  }

  function handleOpenChange(next: boolean) {
    if (!next) {
      openVersion.reset()
      setKetLuan('')
      setKetQua(RESULTS.suaTheo)
      setChangeKind(String(CHANGE_KIND.major))
    }
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Rà lại theo bản gốc</DialogTitle>
          <DialogDescription>
            {note || 'Đối chiếu bản này với bản gốc rồi cho biết kết luận.'}
          </DialogDescription>
        </DialogHeader>

        {/*  409 «người khác đang giữ bản nháp» phải Ở LẠI trong hộp thoại kèm
             tên người đó — toast bay mất trước khi đọc xong (C14). */}
        {openVersion.isError && (
          <p
            role="alert"
            className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
          >
            <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
            {extractErrorMessage(openVersion.error)}
          </p>
        )}

        <div className="space-y-4">
          {sourceDocumentId && (
            //  Mở TAB MỚI: người rà cần đặt hai bản cạnh nhau mà đọc.
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="w-full"
              onClick={() =>
                window.open(
                  appRoutes.document.documentDetail(sourceDocumentId),
                  '_blank',
                  'noopener',
                )
              }
            >
              <ExternalLink className="size-4" />
              Mở bản gốc để đối chiếu
            </Button>
          )}

          <div className="space-y-2">
            <Label>Rà xong, kết luận là</Label>
            <RadioGroup value={ketQua} onValueChange={setKetQua}>
              <label
                className={cn(
                  'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
                  ketQua === RESULTS.suaTheo ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
                )}
              >
                <RadioGroupItem value={RESULTS.suaTheo} className="mt-0.5" />
                <span>
                  <span className="font-medium">Phải sửa theo bản gốc</span>
                  <span className="block text-muted-foreground">
                    Gỡ dấu và mở luôn một phiên bản mới của bản này để sửa.
                  </span>
                </span>
              </label>

              <label
                className={cn(
                  'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
                  ketQua === RESULTS.giuNguyen ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
                )}
              >
                <RadioGroupItem value={RESULTS.giuNguyen} className="mt-0.5" />
                <span>
                  <span className="font-medium">Giữ nguyên, không phải sửa</span>
                  <span className="block text-muted-foreground">
                    Chỉ gỡ dấu «cần rà lại» và ghi kết luận vào nhật ký.
                  </span>
                </span>
              </label>
            </RadioGroup>
          </div>

          {/*  Chọn "phải sửa" mà văn bản đang kẹt (còn bản nháp mở / bản đang
               dùng chưa duyệt) thì nói thẳng ra ở đây: vẫn cho ghi kết luận, chỉ
               là không mở bản mới. Giấu đi rồi âm thầm không mở mới là tệ. */}
          {ketQua === RESULTS.suaTheo && !canOpenNewVersion && (
            <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">
              Lần này chỉ ghi kết luận, chưa mở phiên bản mới được: {blockedReason}
            </p>
          )}

          {openNewVersion && (
            <div className="space-y-2">
              <Label>Mức sửa</Label>
              <RadioGroup value={changeKind} onValueChange={setChangeKind}>
                {[
                  {
                    value: CHANGE_KIND.major,
                    ten: 'Sửa lớn',
                    description: 'Đổi cách làm việc; người đã đọc bản cũ phải xác nhận đã đọc lại.',
                  },
                  {
                    value: CHANGE_KIND.minor,
                    ten: 'Sửa nhỏ',
                    description: 'Sửa câu chữ, số liệu lặt vặt — không bắt ai đọc lại.',
                  },
                ].map((muc) => {
                  const selection = changeKind === String(muc.value)
                  const newVersion = nextVersionNo(versions, muc.value)
                  return (
                    <label
                      key={muc.value}
                      className={cn(
                        'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
                        selection ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
                      )}
                    >
                      <RadioGroupItem value={String(muc.value)} className="mt-0.5" />
                      <span>
                        <span className="font-medium">{muc.ten}</span>
                        {newVersion && (
                          <span className="text-muted-foreground"> — bản mới sẽ là {newVersion}</span>
                        )}
                        <span className="block text-muted-foreground">{muc.description}</span>
                      </span>
                    </label>
                  )
                })}
              </RadioGroup>
            </div>
          )}

          <div className="space-y-2">
            <Label htmlFor="review-conclusion">
              Kết luận rà<span className="text-destructive"> *</span>
            </Label>
            <Textarea
              id="review-conclusion"
              rows={3}
              placeholder={
                openNewVersion
                  ? 'Ví dụ: bản gốc bổ sung Điều 5 về phụ cấp ca đêm, bản của mình phải sửa theo'
                  : 'Ví dụ: đã đối chiếu bản 2.0, phần của pháp nhân mình vẫn đúng, không phải sửa'
              }
              value={ketLuan}
              onChange={(event) => setKetLuan(event.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              {openNewVersion
                ? 'Câu này vào nhật ký rà soát và làm luôn dòng «sửa gì» của phiên bản mới.'
                : 'Câu này vào nhật ký thao tác — người sau đọc lại phải biết bạn đã đối chiếu ra điều gì.'}
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            //  Backend đòi kết luận từ 3 ký tự (`schema.ReviewedIn`) — chặn ngay
            //  ở nút thay vì để người dùng bấm rồi ăn 422.
            disabled={ketLuan.trim().length < 3 || isRunning}
            onClick={() => void handleSubmit()}
          >
            {openNewVersion ? 'Rà xong và mở phiên bản mới' : 'Rà xong'}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
