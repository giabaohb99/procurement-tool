import { AlertTriangle } from 'lucide-react'
import { useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
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
import { CHANGE_KIND } from '../types/document-record'

interface DocumentVersionDialogProps {
  documentId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Một lựa chọn mức sửa.
 *
 * Số bản mới TÍNH RA từ bản đang dùng chứ không ghi cứng — xem `soBanKeTiep`.
 * Đây là câu trả lời trực tiếp cho "chọn cái này thì được gì", nên để ngay cạnh
 * tên chứ không giấu dưới dòng mô tả.
 */
function EditLevel({
  value,
  selection,
  ten,
  newVersion,
  moTa,
}: {
  value: string
  selection: boolean
  ten: string
  newVersion: string | null
  moTa: string
}) {
  return (
    <label
      className={cn(
        'flex cursor-pointer items-start gap-3 rounded-md border p-3 text-sm transition-colors',
        selection ? 'border-primary bg-primary/5' : 'hover:bg-muted/50',
      )}
    >
      <RadioGroupItem value={value} className="mt-0.5" />
      <span>
        <span className="font-medium">{ten}</span>
        {newVersion && <span className="text-muted-foreground"> — bản mới sẽ là {newVersion}</span>}
        <span className="block text-muted-foreground">{moTa}</span>
      </span>
    </label>
  )
}

/**
 * MỞ PHIÊN BẢN MỚI — bắt khai lý do và phân loại mức sửa (C05, C13, C15).
 *
 * Hai ô này không phải thủ tục:
 *  - **lý do** là thứ duy nhất trả lời được câu "ba tháng trước vì sao có bản
 *    2.0" — không bắt khai thì không ai tự viết;
 *  - **mức sửa** quyết định số bản (2.0 hay 1.1) và quyết định người đã đọc bản
 *    cũ có phải xác nhận đã đọc lại hay không.
 *
 * Bản cũ **không bị đè**: mở bản mới là thêm một dòng, bản cũ ở lại nguyên vẹn.
 */
export function DocumentVersionDialog({
  documentId,
  open,
  onOpenChange,
}: DocumentVersionDialogProps) {
  const [changeKind, setChangeKind] = useState(String(CHANGE_KIND.major))
  const [summary, setSummary] = useState('')
  const [reason, setReason] = useState('')
  const [effectiveFrom, setEffectiveFrom] = useState('')

  const openVersion = useOpenVersion(documentId)

  //  CẢ danh sách phiên bản, vì số bản mới tính từ số CAO NHẤT đã từng dùng chứ
  //  không từ bản đang dùng (xem `soBanKeTiep`). Danh sách đã nằm sẵn trong cache
  //  của tab Phiên bản nên đây không phải một lượt gọi thêm.
  const { data: versions = [] } = useDocumentVersions(documentId)

  function handleSubmit() {
    openVersion.mutate(
      {
        change_kind: Number(changeKind),
        change_summary: summary.trim(),
        change_reason: reason.trim(),
        effective_from: effectiveFrom || null,
      },
      {
        onSuccess: () => {
          handleOpenChange(false)
          setSummary('')
          setReason('')
          setEffectiveFrom('')
        },
      },
    )
  }

  //  Đóng hộp thoại thì xóa luôn câu báo lỗi cũ — mở lại mà vẫn thấy "người
  //  khác đang giữ" trong khi bản nháp đó đã chốt xong là báo sai.
  function handleOpenChange(next: boolean) {
    if (!next) openVersion.reset()
    onOpenChange(next)
  }

  return (
    <Dialog open={open} onOpenChange={handleOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Mở phiên bản mới</DialogTitle>
          <DialogDescription>
            Bản đang dùng vẫn giữ nguyên và vẫn có hiệu lực cho tới khi bản mới
            được duyệt.
          </DialogDescription>
        </DialogHeader>

        {/*  Thua đường đua thì backend trả 409 kèm TÊN người đang giữ bản nháp.
             Đặt câu đó ở lại ngay trong hộp thoại, chỗ người dùng vừa bấm —
             toast bay mất trước khi đọc xong tên (C14). */}
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
          <div className="space-y-2">
            <Label>Mức sửa</Label>
            {/*  Viền theo lựa chọn đang chọn: hai ô cùng viền xám thì nhìn không
                 ra mình đang chọn cái nào, chỉ có cái chấm radio 16px nói. */}
            <RadioGroup value={changeKind} onValueChange={setChangeKind}>
              <EditLevel
                value={String(CHANGE_KIND.major)}
                selection={changeKind === String(CHANGE_KIND.major)}
                ten="Sửa lớn"
                newVersion={nextVersionNo(versions, CHANGE_KIND.major)}
                moTa="Đổi nội dung có ảnh hưởng tới người thực hiện; người đã đọc bản cũ phải xác nhận đã đọc lại."
              />
              <EditLevel
                value={String(CHANGE_KIND.minor)}
                selection={changeKind === String(CHANGE_KIND.minor)}
                ten="Sửa nhỏ"
                newVersion={nextVersionNo(versions, CHANGE_KIND.minor)}
                moTa="Sửa lỗi chính tả, đổi số điện thoại — không đổi cách làm việc, không bắt ai đọc lại."
              />
            </RadioGroup>
          </div>

          <div className="space-y-2">
            <Label htmlFor="change-summary">
              Sửa gì<span className="text-destructive"> *</span>
            </Label>
            <Textarea
              id="change-summary"
              rows={2}
              placeholder="VD: Bổ sung Điều 5 về mức phụ cấp ca đêm"
              value={summary}
              onChange={(event) => setSummary(event.target.value)}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="change-reason">Vì sao sửa</Label>
            <Textarea
              id="change-reason"
              rows={2}
              placeholder="VD: Theo kết luận họp Ban điều hành ngày 10/8/2026"
              value={reason}
              onChange={(event) => setReason(event.target.value)}
            />
            <p className="text-xs text-muted-foreground">
              Hiện ngay trên dòng phiên bản — đây là thứ trả lời được «vì sao có bản này»
              khi ai đó tra lại sau vài tháng.
            </p>
          </div>

          <div className="space-y-2">
            <Label>Ngày hiệu lực của bản mới</Label>
            <DatePicker value={effectiveFrom} onChange={setEffectiveFrom} />
            <p className="text-xs text-muted-foreground">
              Để trống = áp dụng ngay khi được duyệt. Đặt ngày trong tương lai
              thì bản cũ vẫn chạy cho tới ngày đó.
            </p>
          </div>
        </div>

        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => handleOpenChange(false)}>
            Hủy
          </Button>
          <Button
            type="button"
            onClick={handleSubmit}
            disabled={!summary.trim() || openVersion.isPending}
          >
            Mở phiên bản
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
