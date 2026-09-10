import { Loader2, Paperclip, Send, Stamp, X } from 'lucide-react'
import { forwardRef, useEffect, useImperativeHandle, useMemo, useRef, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { useDocumentTypes } from '@/modules/procurement/hooks/use-purchase-request-support'
import { withOtherType } from '@/modules/procurement/utils/document-attachment-groups'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { FileDropzone } from '@/shared/ui/file-dropzone'
import { Label } from '@/shared/ui/label'
import { MultiPicker } from '@/shared/ui/multi-picker'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatFileSize } from '@/shared/utils/format-file-size'
import { useCreateSealRequest, useSealApprovers, useUpdateSealRequest } from '../hooks/use-seal-requests'
import {
  EDITABLE_SEAL_STATUSES,
  type SealRequest,
  type SealRequestPayload,
} from '../types/seal-request'
import { SealPageHeader } from './seal-page-header'

interface SealRequestFormProps {
  /** Có = SỬA phiếu này. Bỏ trống = TẠO mới. */
  request?: SealRequest
  /** NHÂN BẢN: tạo mới, chép nội dung từ phiếu này (KHÔNG chép mã/trạng thái/đính kèm). */
  duplicateFrom?: SealRequest
  title: string
  /** Hủy / back — điều hướng đi (page tự quyết). */
  onCancel: () => void
  /** Sau khi lưu/gửi duyệt thành công — page tự điều hướng theo id + đã gửi duyệt hay chưa. */
  onSaved: (result: SealRequest, submitted: boolean) => void
  /**
   * NHÚNG vào trang chi tiết: bỏ `SealPageHeader` (trang đã có thanh tiêu đề riêng).
   */
  embedded?: boolean
  /** Ẩn hàng nút Lưu nháp / Gửi duyệt của form — khi trang cha tự bày chúng (qua `ref`). */
  hideActions?: boolean
  /** Báo trạng thái đang lưu ra ngoài để trang cha khóa nút Lưu nháp / Gửi duyệt của nó. */
  onPendingChange?: (pending: boolean) => void
}

/** Điều khiển form từ trang cha (bấm Lưu nháp / Gửi duyệt đặt ở thanh công cụ trên). */
export interface SealFormHandle {
  save: (submit: boolean) => void
}

/**
 * Biểu mẫu YÊU CẦU ĐÓNG DẤU dùng trên TRANG (tạo `/approval-seal/new`, sửa
 * `/approval-seal/:id/edit`).
 *
 * Khi TẠO mới, chứng từ đã ký được chọn ngay trên form và đệm lại trong state;
 * lưu xong (phiếu có id) mới tải lên rồi mới gửi duyệt — backend đòi ≥1 tệp
 * trước khi gửi duyệt. Khi SỬA, dùng thẻ đính kèm chuẩn của phân hệ Mua hàng.
 */
export const SealRequestForm = forwardRef<SealFormHandle, SealRequestFormProps>(function SealRequestForm(
  { request, duplicateFrom, title, onCancel, onSaved, embedded = false, hideActions = false, onPendingChange },
  ref,
) {
  const isEdit = Boolean(request)
  //  Nguồn điền sẵn: SỬA thì từ chính phiếu, NHÂN BẢN thì từ phiếu nguồn.
  const source = request ?? duplicateFrom
  const { can } = usePermission()
  const createMutation = useCreateSealRequest()
  const updateMutation = useUpdateSealRequest()
  const pending = createMutation.isPending || updateMutation.isPending

  //  Danh mục mượn của phân hệ khác — tắt lời gọi khi thiếu quyền để tránh toast 403.
  const { data: companyData } = useCompanies({ page_size: 200 }, { enabled: can('company', 'read') })
  const { data: approversResult } = useSealApprovers()

  const companies = useMemo(() => companyData?.items ?? [], [companyData])

  const [purpose, setPurpose] = useState(source?.purpose ?? '')
  const [companyIds, setCompanyIds] = useState<number[]>(source?.company_ids ?? [])
  //  `null` = người dùng chưa tự chọn: khi tạo mới thì lùi về TBP mặc định (trưởng
  //  bộ phận của người tạo) ngay khi danh sách người duyệt về — tính lúc render nên
  //  không cần effect + setState (tránh cảnh báo cascading renders).
  const [approverPick, setApproverPick] = useState<number | null>(source?.first_approver_id ?? null)
  const [note, setNote] = useState(source?.note ?? '')
  //  Chứng từ đã ký chọn trên form TẠO mới — đệm lại, tải lên sau khi có id.
  const [pendingFiles, setPendingFiles] = useState<File[]>([])
  //  Thư mục (loại chứng từ) lưu các tệp đệm — MẶC ĐỊNH "Chứng từ đã ký" (`signed_doc`).
  const [attachDocType, setAttachDocType] = useState('signed_doc')
  const { data: docTypeData } = useDocumentTypes()
  const docTypeOptions = useMemo(() => withOtherType(docTypeData ?? []), [docTypeData])

  const approverId = approverPick ?? approversResult?.default_id ?? 0

  //  Ô chọn công ty: logo trước tên, MST sau tên. Gộp thêm pháp nhân đã chọn của
  //  phiếu nguồn phòng khi nó nằm ngoài trang danh sách (đã tắt / quá 200 dòng).
  const companyOptions = useMemo(() => {
    const map = new Map<number, { id: number; label: string; hint: string; avatar: string }>()
    for (const c of companies) {
      map.set(c.id, { id: c.id, label: c.name, hint: c.tax_code, avatar: c.logo })
    }
    for (const c of source?.companies ?? []) {
      if (!map.has(c.id)) {
        map.set(c.id, { id: c.id, label: c.name, hint: c.tax_code, avatar: c.logo })
      }
    }
    return Array.from(map.values())
  }, [companies, source?.companies])

  const approvers = approversResult?.items ?? []

  const canManageFiles = !isEdit
    ? false
    : can('seal_request', 'write') && EDITABLE_SEAL_STATUSES.has(request!.status)

  function buildPayload(): SealRequestPayload {
    const approver = approvers.find((a) => a.id === approverId)
    return {
      purpose: purpose.trim(),
      company_ids: companyIds,
      //  Bộ phận phê duyệt suy từ người duyệt được chọn (nếu có).
      department_id: approver?.department_id || source?.department_id || 0,
      first_approver_id: approverId,
      note: note.trim(),
    }
  }

  function validate(submit: boolean): string {
    if (!purpose.trim()) return 'Vui lòng nhập mục đích sử dụng.'
    if (companyIds.length === 0) return 'Vui lòng chọn ít nhất một công ty cần đóng dấu.'
    if (!approverId) return 'Vui lòng chọn trưởng bộ phận phê duyệt.'
    //  Gửi duyệt phiếu MỚI đòi ≥1 chứng từ đã ký — chặn sớm ở đây thay vì để
    //  backend trả lỗi sau khi đã lỡ lưu nháp.
    if (submit && !isEdit && pendingFiles.length === 0) {
      return 'Vui lòng đính kèm ít nhất một chứng từ đã ký trước khi gửi duyệt.'
    }
    return ''
  }

  async function handleSubmit(submit: boolean) {
    const msg = validate(submit)
    if (msg) {
      toast.error(msg)
      return
    }
    const body = buildPayload()
    try {
      if (isEdit && request) {
        const data = await updateMutation.mutateAsync({ id: request.id, payload: body, submit })
        onSaved(data, submit)
        return
      }
      const data = await createMutation.mutateAsync({
        payload: body,
        files: pendingFiles,
        docType: attachDocType,
        submit,
      })
      onSaved(data, submit)
    } catch {
      //  Lỗi đã được http-client / mutation bắn toast; ở đây chỉ chặn điều hướng.
    }
  }

  function addFiles(selected: File[]) {
    setPendingFiles((current) => [...current, ...selected])
  }

  function removeFile(index: number) {
    setPendingFiles((current) => current.filter((_, i) => i !== index))
  }

  //  Cho trang cha bấm Lưu nháp / Gửi duyệt từ thanh công cụ trên: giữ handler mới nhất
  //  trong ref (cập nhật trong effect, không đọc/ghi ref lúc render) rồi lộ qua `ref`.
  const submitRef = useRef<(submit: boolean) => void>(() => {})
  useEffect(() => {
    submitRef.current = (submit) => void handleSubmit(submit)
  })
  useImperativeHandle(ref, () => ({ save: (submit) => submitRef.current(submit) }), [])
  //  Báo trạng thái "đang lưu" ra ngoài để trang cha khóa nút của nó.
  useEffect(() => {
    onPendingChange?.(pending)
  }, [pending, onPendingChange])

  //  Hàng nút Lưu nháp / Gửi duyệt — dùng cho cả bản NHÚNG lẫn `SealPageHeader`.
  const actionButtons = (
    <>
      {!embedded && (
        <Button variant="outline" onClick={onCancel} disabled={pending}>
          Hủy
        </Button>
      )}
      <Button variant="outline" onClick={() => void handleSubmit(false)} disabled={pending}>
        Lưu nháp
      </Button>
      <Button onClick={() => void handleSubmit(true)} disabled={pending}>
        {pending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
        Gửi duyệt
      </Button>
    </>
  )

  return (
    <div className="flex w-full flex-col">
      {!embedded && <SealPageHeader title={title} onBack={onCancel} actions={actionButtons} />}
      {/*  Nhúng: mặc định vẫn có hàng nút; `hideActions` khi trang cha bày nút ở thanh trên. */}
      {embedded && !hideActions && (
        <div className="mb-4 flex flex-wrap items-center justify-end gap-2">{actionButtons}</div>
      )}

      <Card className="flex flex-col gap-5 p-5">
        <div className="flex flex-col gap-4">
          {/*  C-03: tiêu đề block = icon + nhãn, gạch dưới KÉO HẾT bề ngang thẻ. */}
          <div className="-mx-5 -mt-1 flex items-center justify-between border-b px-5 pb-3">
            <span className="inline-flex items-center gap-2 font-medium">
              <Stamp className="size-5 text-rose-600 dark:text-rose-400" />
              Thông tin yêu cầu
            </span>
          </div>

          <Field label="Mục đích sử dụng" required>
            <Textarea
              rows={3}
              value={purpose}
              placeholder="VD: Đóng dấu hợp đồng mua bán với NCC A"
              onChange={(e) => setPurpose(e.target.value)}
            />
          </Field>

          <Field label="Công ty cần đóng dấu" required>
            <MultiPicker
              value={companyIds}
              onChange={setCompanyIds}
              options={companyOptions}
              placeholder="Chọn công ty cần đóng dấu"
              searchPlaceholder="Tìm theo tên hoặc mã số thuế…"
              emptyMessage="Không tìm thấy công ty nào."
              //  Nới rộng để hiện đủ tên công ty + MST; hiện chip công ty đã chọn NGAY
              //  trong khung (không "Đã chọn N"); nút Bỏ hết là dấu X trong khung.
              contentClassName="w-[min(34rem,92vw)]"
              clearInTrigger
              chipsInTrigger
            />
          </Field>

          <Field label="Trưởng bộ phận phê duyệt" required>
            <Select
              value={approverId ? String(approverId) : undefined}
              onValueChange={(value) => setApproverPick(Number(value))}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn người phê duyệt" />
              </SelectTrigger>
              <SelectContent>
                {approvers.map((approver) => (
                  <SelectItem key={approver.id} value={String(approver.id)}>
                    <span className="flex items-center gap-2">
                      <Avatar size="sm" className="size-6">
                        {approver.avatar && <AvatarImage src={approver.avatar} alt="" />}
                        <AvatarFallback className="text-[10px]">
                          {approver.name.trim()[0]?.toUpperCase() || '?'}
                        </AvatarFallback>
                      </Avatar>
                      <span>{approver.name}</span>
                      {approver.is_dept_head && (
                        <span className="text-xs text-muted-foreground">· Trưởng bộ phận</span>
                      )}
                    </span>
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>

          <Field label="Ghi chú">
            <Textarea
              rows={2}
              value={note}
              placeholder="Ghi chú thêm cho người duyệt / văn thư."
              onChange={(e) => setNote(e.target.value)}
            />
          </Field>
        </div>
      </Card>

      {/* Chứng từ đã ký. SỬA: thẻ đính kèm chuẩn (tải thẳng lên phiếu đã có id).
          TẠO mới: chọn trước, đệm lại rồi tải lên sau khi lưu — backend đòi ≥1
          tệp trước khi gửi duyệt. */}
      <div className="mt-5">
        {isEdit ? (
          <DocumentAttachmentsCard
            entity="seal_request"
            entityId={request?.id ?? 0}
            canManage={canManageFiles}
            maxSizeMb={50}
            defaultDocType="signed_doc"
            hideUploadButton
          />
        ) : (
          <Card className="flex flex-col gap-3 p-5">
            <div className="flex items-center gap-2">
              <Paperclip className="size-4 text-primary" />
              <h3 className="text-base font-medium text-navy dark:text-foreground">
                Chứng từ đã ký
              </h3>
              <span className="rounded-full bg-muted px-2 py-0.5 text-xs text-muted-foreground">
                {pendingFiles.length} tệp
              </span>
            </div>

            {/*  Cùng FORMAT với ô kéo-thả ở trang sửa (DocumentAttachmentsCard): ô chọn
                "Lưu vào mục" nằm NGAY TRONG khung kéo-thả (`data-dropzone-ignore`). */}
            <FileDropzone onFiles={addFiles} hint="Kéo thả tệp vào đây hoặc bấm để chọn tệp">
              <span className="text-xs text-muted-foreground">Lưu vào mục</span>
              <Select value={attachDocType} onValueChange={setAttachDocType}>
                <SelectTrigger size="sm" className="w-56 bg-background">
                  <SelectValue placeholder="Chọn loại chứng từ" />
                </SelectTrigger>
                <SelectContent>
                  {docTypeOptions.map((opt) => (
                    <SelectItem key={opt.value} value={opt.value}>
                      {opt.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </FileDropzone>

            {pendingFiles.length > 0 && (
              <ul className="divide-y rounded-lg border">
                {pendingFiles.map((file, index) => (
                  <li
                    key={`${file.name}-${index}`}
                    className="flex min-h-11 items-center gap-3 px-3 py-2"
                  >
                    <Paperclip className="size-4 shrink-0 text-muted-foreground" />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-sm font-medium text-navy dark:text-foreground">
                        {file.name}
                      </p>
                      <p className="text-xs text-muted-foreground">{formatFileSize(file.size)}</p>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon-sm"
                      aria-label={`Bỏ tệp ${file.name}`}
                      onClick={() => removeFile(index)}
                    >
                      <X className="size-4" />
                    </Button>
                  </li>
                ))}
              </ul>
            )}

            <p className="text-xs text-muted-foreground">
              Tệp sẽ được tải lên sau khi lưu phiếu. Gửi duyệt cần ít nhất một chứng từ đã ký.
            </p>
          </Card>
        )}
      </div>
    </div>
  )
})


function Field({ label, required, children }: { label: string; required?: boolean; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-1.5">
      <Label>
        {label}
        {required && <RequiredMark />}
      </Label>
      {children}
    </div>
  )
}
