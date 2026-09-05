import { Loader2, Send } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { useCreateSealRequest, useUpdateSealRequest } from '../hooks/use-seal-requests'
import { useSealTypes } from '../hooks/use-seal-types'
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
 * `/approval-seal/:id/edit`). Chứng từ đã ký đính kèm hiện ngay dưới form khi
 * phiếu đã có id — backend đòi ≥1 tệp trước khi gửi duyệt.
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
  const { data: sealTypeData } = useSealTypes({}, { enabled: can('seal_type', 'read') })
  const { data: companyData } = useCompanies({ page_size: 200 }, { enabled: can('company', 'read') })
  const { data: employeeData } = useEmployees({ page_size: 200 }, { enabled: can('employee', 'read') })

  //  Loại con dấu chỉ hiện cái đang bật; giữ lại cái đã chọn dù bị ẩn để không mất giá trị cũ.
  const sealTypes = useMemo(() => {
    const items = sealTypeData?.items ?? []
    return items.filter((t) => t.is_active || t.id === source?.seal_type_id)
  }, [sealTypeData, source?.seal_type_id])
  const companies = companyData?.items ?? []
  const employees = employeeData?.items ?? []

  const [purpose, setPurpose] = useState(source?.purpose ?? '')
  const [docTitle, setDocTitle] = useState(source?.title ?? '')
  const [sealTypeId, setSealTypeId] = useState(source?.seal_type_id ?? 0)
  const [companyId, setCompanyId] = useState(source?.company_id ?? 0)
  const [copies, setCopies] = useState(source?.copies ?? 1)
  const [approverId, setApproverId] = useState(source?.first_approver_id ?? 0)
  const [note, setNote] = useState(source?.note ?? '')

  const selectedCompany = companies.find((c) => c.id === companyId)
  //  MST hiển thị: ưu tiên công ty vừa chọn, lùi về giá trị backend đã lưu.
  const taxCode = selectedCompany?.tax_code || source?.company_tax_code || ''

  const canManageFiles = !isEdit
    ? false
    : can('seal_request', 'write') && EDITABLE_SEAL_STATUSES.has(request!.status)

  function buildPayload(): SealRequestPayload {
    const employee = employees.find((e) => e.id === approverId)
    return {
      purpose: purpose.trim(),
      title: docTitle.trim(),
      seal_type_id: sealTypeId,
      company_id: companyId,
      //  Bộ phận phê duyệt suy từ hồ sơ nhân sự người được chọn (nếu có).
      department_id: employee?.department_id || source?.department_id || 0,
      copies,
      first_approver_id: approverId,
      note: note.trim(),
    }
  }

  function validate(): string {
    if (!purpose.trim()) return 'Vui lòng nhập mục đích sử dụng.'
    if (!sealTypeId) return 'Vui lòng chọn loại con dấu.'
    if (!companyId) return 'Vui lòng chọn công ty cần đóng dấu.'
    if (!copies || copies < 1) return 'Số bản phải từ 1 trở lên.'
    return ''
  }

  function handleSubmit(submit: boolean) {
    if (submit) {
      const msg = validate()
      if (msg) {
        toast.error(msg)
        return
      }
    }
    const body = buildPayload()
    if (isEdit && request) {
      updateMutation.mutate(
        { id: request.id, payload: body, submit },
        { onSuccess: (data) => onSaved(data, submit) },
      )
    } else {
      createMutation.mutate(
        { payload: body, submit },
        { onSuccess: (data) => onSaved(data, submit) },
      )
    }
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
            <Button variant="outline" onClick={() => handleSubmit(false)} disabled={pending}>
              Lưu nháp
            </Button>
            <Button onClick={() => handleSubmit(true)} disabled={pending}>
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

          <Field label="Tên chứng từ">
            <Input
              value={docTitle}
              placeholder="VD: Hợp đồng nguyên tắc số 2026/HĐ-DEGO"
              onChange={(e) => setDocTitle(e.target.value)}
            />
          </Field>

          <div className="grid gap-4 sm:grid-cols-2">
            <Field label="Loại con dấu" required>
              <Select
                value={sealTypeId ? String(sealTypeId) : undefined}
                onValueChange={(value) => setSealTypeId(Number(value))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn loại con dấu" />
                </SelectTrigger>
                <SelectContent>
                  {sealTypes.map((type) => (
                    <SelectItem key={type.id} value={String(type.id)}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Số bản" required>
              <Input
                type="number"
                min={1}
                value={copies}
                onChange={(e) => setCopies(Math.max(1, Number(e.target.value) || 1))}
              />
            </Field>

            <Field label="Công ty cần đóng dấu" required>
              <Select
                value={companyId ? String(companyId) : undefined}
                onValueChange={(value) => setCompanyId(Number(value))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn công ty" />
                </SelectTrigger>
                <SelectContent>
                  {companies.map((company) => (
                    <SelectItem key={company.id} value={String(company.id)}>
                      {company.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>

            <Field label="Mã số thuế">
              <ReadOnlyValue>{taxCode || '—'}</ReadOnlyValue>
            </Field>

            <Field label="Trưởng bộ phận phê duyệt">
              <Select
                value={approverId ? String(approverId) : undefined}
                onValueChange={(value) => setApproverId(Number(value))}
              >
                <SelectTrigger className="w-full">
                  <SelectValue placeholder="Chọn người phê duyệt" />
                </SelectTrigger>
                <SelectContent>
                  {employees.map((employee) => (
                    <SelectItem key={employee.id} value={String(employee.id)}>
                      {employee.code} - {employee.full_name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </Field>
          </div>

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

      {/* Chứng từ đã ký — hiện khi phiếu đã có id (edit). Tạo mới thì thẻ tự nhắc
          lưu phiếu trước (entityId = 0). Gửi duyệt đòi ≥1 tệp ở backend. */}
      <div className="mt-5">
        <DocumentAttachmentsCard
          entity="seal_request"
          entityId={request?.id ?? 0}
          canManage={canManageFiles}
          maxSizeMb={50}
        />
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
