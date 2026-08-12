import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate, formatDateTime } from '@/shared/utils/format-date'
import type { Company } from '@/modules/hr/types/company'
import type { Employee } from '@/modules/hr/types/employee'
import type { PurchaseRequestDetail } from '../types/purchase-request-detail'

interface InfoCardProps {
  data: PurchaseRequestDetail
  editing: boolean
  /** Sau khi phiếu duyệt, quản lý vẫn được đổi cờ Gấp và backend đồng bộ sang ĐMH. */
  urgentEditable?: boolean
  onUrgentChange?: (checked: boolean) => void
  companies?: Company[]
  employees?: Employee[]
  onChange: (changes: Partial<PurchaseRequestDetail>) => void
}

/**
 * Thẻ "Thông tin chung" — GIỮ NGUYÊN thứ tự và tên nhãn của bản `frontend` cũ
 * (`PurchaseRequestDetail.tsx`) để người dùng không phải học lại màn hình.
 *
 * Bộ phận YC và Trưởng bộ phận luôn khóa: backend tự điền theo hồ sơ nhân sự
 * của người yêu cầu / theo phòng ban, sửa tay ở đây là sai nguồn dữ liệu.
 */
export function PurchaseRequestInfoCard({
  data,
  editing,
  urgentEditable,
  onUrgentChange,
  companies = [],
  employees = [],
  onChange,
}: InfoCardProps) {
  return (
    <Card className="gap-4 py-4">
      <CardHeader className="border-b px-4 pb-3">
        <CardTitle className="text-base text-navy dark:text-foreground">
          Thông tin chung
        </CardTitle>
      </CardHeader>

      <CardContent className="grid gap-x-4 gap-y-3 px-4 md:grid-cols-2">
        <Field label="Mã phiếu yêu cầu">{data.code || '— (phiếu nháp)'}</Field>
        <Field label="Ngày tạo">{formatDateTime(data.created_at) || '—'}</Field>

        <div className="space-y-1.5">
          <Label>
            Ngày tiếp nhận <span className="text-destructive">*</span>
          </Label>
          {editing ? (
            <Input
              type="date"
              value={data.request_date || ''}
              onChange={(e) => onChange({ request_date: e.target.value })}
            />
          ) : (
            <ReadOnlyValue>{formatDate(data.request_date) || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Công ty nhận hóa đơn <span className="text-destructive">*</span>
          </Label>
          {editing && companies.length ? (
            <Select
              value={data.company_id ? String(data.company_id) : undefined}
              onValueChange={(value) => {
                const company = companies.find((option) => option.id === Number(value))
                onChange({ company_id: Number(value), company_name: company?.name ?? '' })
              }}
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
          ) : (
            <ReadOnlyValue>{data.company_name || 'Chưa chọn công ty'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Nhân sự YC <span className="text-destructive">*</span>
          </Label>
          {editing && employees.length ? (
            <Select
              value={data.requester_id ? String(data.requester_id) : undefined}
              onValueChange={(value) => {
                const employee = employees.find((option) => option.id === Number(value))
                if (!employee) return
                onChange({
                  requester_id: employee.id,
                  requester: employee.full_name,
                  requester_position: employee.position || '',
                  department: employee.department_name || '',
                  head_of_dept: employee.manager_name || '',
                  company_id: employee.company_id || data.company_id,
                  company_name:
                    companies.find((company) => company.id === employee.company_id)?.name ||
                    data.company_name,
                })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder="Chọn nhân sự yêu cầu" />
              </SelectTrigger>
              <SelectContent>
                {employees.map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.code} - {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : editing ? (
            <Input
              value={data.requester}
              placeholder="Nhập nhân sự yêu cầu"
              onChange={(event) => onChange({ requester: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.requester || 'Chưa chọn nhân sự'}</ReadOnlyValue>
          )}
        </div>
        <Field label="Bộ phận YC *">{data.department}</Field>

        <div className="space-y-1.5">
          <Label>Chức vụ (Nếu có)</Label>
          {editing ? (
            <Input
              value={data.requester_position}
              placeholder="Tự động theo Nhân sự"
              onChange={(e) => onChange({ requester_position: e.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.requester_position || '—'}</ReadOnlyValue>
          )}
        </div>

        <Field label="Trưởng bộ phận (TBP) / Người liên hệ">{data.head_of_dept}</Field>

        <div className="space-y-1.5">
          <Label>Tùy chọn phiếu</Label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-destructive">
            <Checkbox
              checked={data.is_urgent}
              disabled={!editing && !urgentEditable}
              onCheckedChange={(checked) => {
                const next = checked === true
                onChange({ is_urgent: next })
                if (!editing) onUrgentChange?.(next)
              }}
            />
            Đơn gấp
          </label>
        </div>

        <div className="space-y-1.5">
          <Label>
            Mục đích mua hàng <span className="text-destructive">*</span>
          </Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập mục đích mua hàng/dịch vụ..."
              value={data.purpose}
              onChange={(e) => onChange({ purpose: e.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.purpose || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Nội dung mua hàng</Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập nội dung chi tiết..."
              value={data.note}
              onChange={(e) => onChange({ note: e.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.note || '—'}</ReadOnlyValue>
          )}
        </div>
      </CardContent>
    </Card>
  )
}

/** Ô chỉ đọc: dữ liệu do backend gán, màn này không cho sửa. */
function Field({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="space-y-1.5">
      <Label className="text-muted-foreground">{label}</Label>
      <ReadOnlyValue>{children || '—'}</ReadOnlyValue>
    </div>
  )
}

function ReadOnlyValue({
  children,
  multiline = false,
}: {
  children: React.ReactNode
  multiline?: boolean
}) {
  return (
    <div
      className={
        multiline
          ? 'min-h-20 whitespace-pre-wrap rounded-lg border bg-muted/35 px-3 py-2.5 text-sm font-medium'
          : 'flex min-h-9 items-center rounded-lg border bg-muted/35 px-3 py-2 text-sm font-medium'
      }
    >
      {children}
    </div>
  )
}
