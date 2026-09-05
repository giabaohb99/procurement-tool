import { Loader2, Paperclip, Send, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
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
}

/**
 * Biểu mẫu YÊU CẦU ĐÓNG DẤU dùng trên TRANG (tạo `/approval-seal/new`, sửa
 * `/approval-seal/:id/edit`).
 *
 * Khi TẠO mới, chứng từ đã ký được chọn ngay trên form và đệm lại trong state;
 * lưu xong (phiếu có id) mới tải lên rồi mới gửi duyệt — backend đòi ≥1 tệp
 * trước khi gửi duyệt. Khi SỬA, dùng thẻ đính kèm chuẩn của phân hệ Mua hàng.
 */
export function SealRequestForm({ request, duplicateFrom, title, onCancel, onSaved }: SealRequestFormProps) {
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
      const data = await createMutation.mutateAsync({ payload: body, files: pendingFiles, submit })
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

  return (
    <div className="flex w-full flex-col">
      <SealPageHeader
        title={title}
        onBack={onCancel}
        actions={
          <>
            <Button variant="outline" onClick={onCancel} disabled={pending}>
              Hủy
            </Button>
            <Button variant="outline" onClick={() => void handleSubmit(false)} disabled={pending}>
              Lưu nháp
            </Button>
            <Button onClick={() => void handleSubmit(true)} disabled={pending}>
              {pending ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
              Gửi duyệt
            </Button>
          </>
        }
      />

      <Card className="flex flex-col gap-5 p-5">
        <div className="flex flex-col gap-4">
          <SectionHeading>Thông tin yêu cầu</SectionHeading>

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
                    {approver.name}
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

            <FileDropzone
              onFiles={addFiles}
              hint="Kéo thả tệp vào đây hoặc bấm để chọn chứng từ đã ký"
            />

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
}

function SectionHeading({ children }: { children: React.ReactNode }) {
  return (
    <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
      {children}
    </h3>
  )
}

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
