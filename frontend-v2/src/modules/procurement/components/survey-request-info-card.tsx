import type { Company } from '@/modules/hr/types/company'
import type { Department } from '@/modules/hr/types/department'
import type { Employee } from '@/modules/hr/types/employee'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
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
import { formatDateTime } from '@/shared/utils/format-date'
import { useDeptHeadLookup } from '../hooks/use-survey-request'
import type { SurveyRequestDetail } from '../types/survey-request-detail'

interface SurveyRequestInfoCardProps {
  data: SurveyRequestDetail
  editing: boolean
  isNew: boolean
  companies?: Company[]
  employees?: Employee[]
  departments?: Department[]
  /**
   * Người yêu cầu thường KHÔNG xem được danh mục Nhân sự nên không đứng tên hộ
   * ai được — ô Người yêu cầu khóa lại, giữ đúng người đang đăng nhập.
   */
  lockRequester?: boolean
  /**
   * Ô đầu phiếu đang thiếu sau lần bấm Gửi duyệt gần nhất — khóa là tên trường
   * (`company_id` · `requester` · `purpose`, xem `invalidSurveyRequestKeys`).
   * Tô đỏ để khoanh vùng đúng chỗ thay vì chỉ toast (QA 29/08).
   */
  invalid?: Set<string>
  onChange: (changes: Partial<SurveyRequestDetail>) => void
}

/**
 * Thẻ "Thông tin chung" của phiếu Yêu cầu báo giá — giữ nguyên thứ tự và tên
 * nhãn của bản `frontend` cũ (`SurveyRequestDetail.tsx`).
 *
 * CR-086/089 — Bộ phận lưu bằng **id**, tên chỉ đi kèm để in. Đổi phòng thì tra
 * lại Trưởng bộ phận theo id: hai phòng trùng tên ở hai pháp nhân tra theo tên
 * sẽ ra nhầm người ký.
 */
export function SurveyRequestInfoCard({
  data,
  editing,
  isNew,
  companies = [],
  employees = [],
  departments = [],
  lockRequester = false,
  invalid,
  onChange,
}: SurveyRequestInfoCardProps) {
  const deptHeadLookup = useDeptHeadLookup()

  /**
   * Danh sách TBP chọn được = trưởng đã gán ở màn Phòng ban. Một người trưởng
   * NHIỀU phòng chỉ hiện một dòng (Radix Select không nhận value trùng), gom
   * tên các phòng vào cùng nhãn cho dễ nhận.
   */
  const deptHeads = (() => {
    const byId = new Map<number, { id: number; name: string; departments: string[] }>()
    for (const department of departments) {
      if (!department.manager_id || !department.manager_name) continue
      const entry = byId.get(department.manager_id) ?? {
        id: department.manager_id,
        name: department.manager_name,
        departments: [],
      }
      entry.departments.push(department.name)
      byId.set(department.manager_id, entry)
    }
    return Array.from(byId.values())
  })()

  /** Điền lại ô Trưởng bộ phận theo phòng vừa chọn. Tra hụt thì để trống. */
  async function fillDeptHead(departmentId: number, department: string) {
    if (!departmentId && !department) {
      onChange({ head_of_dept: '', head_of_dept_id: 0 })
      return
    }
    const found = await deptHeadLookup.mutateAsync({ department, departmentId })
    onChange({
      head_of_dept: found?.head_of_dept ?? '',
      head_of_dept_id: found?.head_of_dept_id ?? 0,
    })
  }

  function pickEmployee(employeeId: number) {
    const employee = employees.find((option) => option.id === employeeId)
    if (!employee) return
    const departmentId = employee.department_id || 0
    const department = employee.department_name || ''
    onChange({
      requester_id: employee.id,
      requester: employee.full_name,
      requester_position: employee.position || '',
      department_id: departmentId,
      department,
      company_id: employee.company_id || data.company_id,
    })
    void fillDeptHead(departmentId, department)
  }

  function pickDepartment(departmentId: number) {
    const department = departments.find((option) => option.id === departmentId)
    if (!department) return
    onChange({ department_id: department.id, department: department.name })
    void fillDeptHead(department.id, department.name)
  }

  return (
    <Card className="gap-4 py-4">
      {/* Cùng khuôn với các thẻ khác của phân hệ — `pb-3!` là bắt buộc vì
          shadcn đặt `[.border-b]:pb-6` cho CardHeader. */}
      <CardHeader className="min-h-9 flex flex-row items-center gap-3 border-b px-4 pb-3!">
        <CardTitle className="text-base text-navy dark:text-foreground">Thông tin chung</CardTitle>
      </CardHeader>

      <CardContent className="grid gap-x-4 gap-y-3 px-4 md:grid-cols-2">
        {!isNew && <Field label="Mã phiếu">{data.code || '— (phiếu nháp)'}</Field>}

        <div className="space-y-1.5">
          <Label>Ngày tạo</Label>
          {isNew ? (
            <DatePicker
              value={data.request_date || ''}
              onChange={(value) => onChange({ request_date: value })}
            />
          ) : (
            <ReadOnlyValue>{formatDateTime(data.created_at) || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Công ty nhận hóa đơn
            <RequiredMark />
          </Label>
          {editing && companies.length ? (
            <Select
              value={data.company_id ? String(data.company_id) : undefined}
              onValueChange={(value) => onChange({ company_id: Number(value) })}
            >
              <SelectTrigger className="w-full" aria-invalid={invalid?.has('company_id') || undefined}>
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
            <ReadOnlyValue>
              {companies.find((company) => company.id === data.company_id)?.name ||
                'Chưa chọn công ty'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Người yêu cầu
            <RequiredMark />
          </Label>
          {editing && !lockRequester && employees.length ? (
            <Select
              value={data.requester_id ? String(data.requester_id) : undefined}
              onValueChange={(value) => pickEmployee(Number(value))}
            >
              <SelectTrigger className="w-full" aria-invalid={invalid?.has('requester') || undefined}>
                <SelectValue placeholder="Chọn người yêu cầu" />
              </SelectTrigger>
              <SelectContent>
                {employees.map((employee) => (
                  <SelectItem key={employee.id} value={String(employee.id)}>
                    {employee.code} - {employee.full_name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.requester || 'Chưa chọn người yêu cầu'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>Chức vụ</Label>
          {editing ? (
            <Input
              value={data.requester_position}
              placeholder="Tự động theo Nhân sự"
              onChange={(event) => onChange({ requester_position: event.target.value })}
            />
          ) : (
            <ReadOnlyValue>{data.requester_position || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label>
            Bộ phận YC
            <RequiredMark />
          </Label>
          {editing && departments.length ? (
            <Select
              value={data.department_id ? String(data.department_id) : undefined}
              onValueChange={(value) => pickDepartment(Number(value))}
            >
              {/* Phiếu cũ có tên phòng nhưng chưa có id (dữ liệu trước CR-086)
                  thì ô rỗng — mượn tên đang lưu làm gợi ý để người lập chọn lại. */}
              <SelectTrigger className="w-full">
                <SelectValue placeholder={data.department || 'Chọn bộ phận'} />
              </SelectTrigger>
              <SelectContent>
                {departments.map((department) => (
                  <SelectItem key={department.id} value={String(department.id)}>
                    {department.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>{data.department || '—'}</ReadOnlyValue>
          )}
        </div>

        {/* Trưởng bộ phận: mặc định điền theo phòng của người YC, nhưng người lập
            ĐƯỢC chọn TBP phòng ban khác duyệt hộ (QA 29/08) — danh sách lấy từ
            người đã gán ở màn Phòng ban, không nhập tay tên lạ được. */}
        <div className="space-y-1.5">
          <Label className={editing ? undefined : 'text-muted-foreground'}>Trưởng bộ phận</Label>
          {editing && deptHeads.length ? (
            <Select
              value={
                deptHeads.some((head) => head.id === data.head_of_dept_id)
                  ? String(data.head_of_dept_id)
                  : undefined
              }
              onValueChange={(value) => {
                const head = deptHeads.find((option) => option.id === Number(value))
                if (head) onChange({ head_of_dept_id: head.id, head_of_dept: head.name })
              }}
            >
              <SelectTrigger className="w-full">
                <SelectValue
                  placeholder={
                    deptHeadLookup.isPending ? 'Đang tra…' : data.head_of_dept || 'Chọn Trưởng bộ phận'
                  }
                />
              </SelectTrigger>
              <SelectContent>
                {deptHeads.map((head) => (
                  <SelectItem key={head.id} value={String(head.id)}>
                    {head.name} — {head.departments.join(', ')}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          ) : (
            <ReadOnlyValue>
              {deptHeadLookup.isPending ? 'Đang tra…' : data.head_of_dept || '—'}
            </ReadOnlyValue>
          )}
        </div>

        {/* bao-CR-289: cờ Đơn gấp — mirror khối "Tùy chọn phiếu" của YCMH. */}
        <div className="space-y-1.5 md:col-span-2">
          <Label>Tùy chọn phiếu</Label>
          <label className="flex cursor-pointer items-center gap-2 text-sm text-destructive">
            <Checkbox
              checked={data.is_urgent}
              disabled={!editing}
              onCheckedChange={(checked) => onChange({ is_urgent: checked === true })}
            />
            Đơn gấp
          </label>
        </div>

        {/* bao-CR-289: phiếu gộp là Yêu cầu mua hàng nên nhãn đổi theo YCMH cũ —
            "Mục đích mua hàng" / "Nội dung mua hàng" (trước là Mục đích khảo sát / Ghi chú). */}
        <div className="space-y-1.5 md:col-span-2">
          <Label>
            Mục đích mua hàng
            <RequiredMark />
          </Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập mục đích mua hàng..."
              value={data.purpose}
              aria-invalid={invalid?.has('purpose') || undefined}
              onChange={(event) => onChange({ purpose: event.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.purpose || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label>Nội dung mua hàng</Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nội dung mua hàng / ghi chú thêm cho phiếu..."
              value={data.note}
              onChange={(event) => onChange({ note: event.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.note || '—'}</ReadOnlyValue>
          )}
        </div>

        {/* P6-9 (bao-CR-287) chuyển đi: cụm NCC đề xuất nay nằm ở thẻ "Nhà cung cấp"
            riêng (`survey-request-supplier-card.tsx`, bao-CR-289) cho khớp YCMH. */}
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
