import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
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
import type {
  DeptHeadCandidate,
  PurchaseRequestDetail,
} from '../types/purchase-request-detail'

interface InfoCardProps {
  data: PurchaseRequestDetail
  editing: boolean
  /** Sau khi phiếu duyệt, quản lý vẫn được đổi cờ Gấp và backend đồng bộ sang ĐMH. */
  urgentEditable?: boolean
  onUrgentChange?: (checked: boolean) => void
  companies?: Company[]
  employees?: Employee[]
  /** CR-071 — ứng viên đứng tên TBP trên phiếu; rỗng thì ô về dạng chữ như cũ. */
  deptHeadCandidates?: DeptHeadCandidate[]
  onChange: (changes: Partial<PurchaseRequestDetail>) => void
}

/**
 * Thẻ "Thông tin chung" — GIỮ NGUYÊN thứ tự và tên nhãn của bản `frontend` cũ
 * (`PurchaseRequestDetail.tsx`) để người dùng không phải học lại màn hình.
 *
 * Bộ phận YC luôn khóa: backend tự điền theo hồ sơ nhân sự của người yêu cầu,
 * sửa tay ở đây là sai nguồn dữ liệu.
 *
 * Trưởng bộ phận thì KHÁC (CR-071): chọn được trong số những người duyệt được
 * phiếu này — nhưng CHỈ để lưu + in, không khóa quyền duyệt của ai.
 */
export function PurchaseRequestInfoCard({
  data,
  editing,
  urgentEditable,
  onUrgentChange,
  companies = [],
  employees = [],
  deptHeadCandidates = [],
  onChange,
}: InfoCardProps) {
  return (
    <Card className="gap-4 py-4">
      {/* Cùng một khuôn với các thẻ khác trên trang — xem ghi chú `pb-3!` ở
          `purchase-request-attachments-card.tsx`. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
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
            <DatePicker
              value={data.request_date || ''}
              onChange={(value) => onChange({ request_date: value })}
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
                const nextDepartment = employee.department_name || ''
                onChange({
                  requester_id: employee.id,
                  requester: employee.full_name,
                  requester_position: employee.position || '',
                  department: nextDepartment,
                  head_of_dept: employee.manager_name || '',
                  // Đổi sang phòng khác thì TBP đã chọn không còn đúng phòng nữa
                  // -> bỏ đi, người lập chọn lại (CR-071).
                  ...(nextDepartment !== data.department ? { head_of_dept_id: 0 } : {}),
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

        {/*
          CR-071 — phòng có nhiều người ký được (phó phòng, quyền trưởng phòng),
          trước đây ô này khóa cứng theo `Department.manager_id` nên in ra sai tên.
          Người được chọn CHỈ để lưu + in — luật duyệt giữ nguyên, ai có quyền trên
          phiếu vẫn bấm Duyệt được. Danh sách do backend lọc theo đúng luật phạm vi,
          rỗng thì để dạng chữ như cũ.
        */}
        <div className="space-y-1.5">
          <Label className={editing && deptHeadCandidates.length ? '' : 'text-muted-foreground'}>
            Trưởng bộ phận (TBP) / Người liên hệ
          </Label>
          {editing && deptHeadCandidates.length ? (
            <Select
              value={data.head_of_dept_id ? String(data.head_of_dept_id) : undefined}
              onValueChange={(value) => {
                const candidate = deptHeadCandidates.find(
                  (option) => option.employee_id === Number(value),
                )
                if (!candidate) return
                onChange({ head_of_dept_id: candidate.employee_id, head_of_dept: candidate.name })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue placeholder={data.head_of_dept || 'Chọn Trưởng bộ phận'} />
              </SelectTrigger>
              <SelectContent>
                {deptHeadCandidates.map((candidate) => (
                  <SelectItem key={candidate.employee_id} value={String(candidate.employee_id)}>
                    {candidate.name}
                    {candidate.position ? ` - ${candidate.position}` : ''}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.head_of_dept || '—'}</ReadOnlyValue>
          )}
        </div>

        {/*
          Ô "Đơn gấp" chiếm trọn một hàng để hai ô chữ dài bên dưới đứng CẠNH
          NHAU: xếp một ô ngắn cạnh một textarea cao sẽ hở một mảng trống lớn.
        */}
        <div className="space-y-1.5 md:col-span-2">
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
      <ReadOnlyValue>{children}</ReadOnlyValue>
    </div>
  )
}
