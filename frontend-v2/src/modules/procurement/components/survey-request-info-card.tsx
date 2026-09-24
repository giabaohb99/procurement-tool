import type { Company } from '@/modules/hr/types/company'
import type { Department } from '@/modules/hr/types/department'
import type { Employee } from '@/modules/hr/types/employee'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { RequiredMark } from '@/shared/ui/required-mark'
import { SearchSelect } from '@/shared/ui/search-select'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { useDeptHeadLookup } from '../hooks/use-survey-request'
import type { SurveyRequestDetail } from '../types/survey-request-detail'
import {
  HANDLING_DEPT_HINT,
  SHARED_PURCHASING_LABEL,
  handlingDeptLabel,
  handlingDeptOptions,
} from '../utils/handling-dept-display'

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
   * NHIỀU phòng chỉ hiện một dòng (ô chọn không nhận value trùng), gom
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

  // bao-CR-480: ô «Phòng xử lý» — cùng nhãn / mục chọn với YCMH, luật ở util dùng chung.
  const handlingDeptOptionList = handlingDeptOptions(departments, data.handler_dept_id)
  const handlingDeptText = handlingDeptLabel(data.handler_dept_id, data.handler_dept_name, departments)

  //  Ô chọn có ô gõ tìm không nhận `aria-invalid` — tô đỏ viền ô gõ bên trong thay cho
  //  `aria-invalid:border-destructive` của SelectTrigger cũ (QA 29/08).
  const invalidClass = (key: string) => cn(invalid?.has(key) && '[&_input]:border-destructive')

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
          <Label htmlFor="sr-company">
            Công ty nhận hóa đơn
            <RequiredMark />
          </Label>
          {editing && companies.length ? (
            <SearchSelect
              id="sr-company"
              searchInTrigger
              className={invalidClass('company_id')}
              value={data.company_id ? String(data.company_id) : ''}
              placeholder="Chọn công ty"
              searchPlaceholder="Gõ để tìm công ty…"
              options={companies.map((company) => ({
                value: String(company.id),
                label: company.name,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng mục đang chọn thì thôi — Radix Select cũ không bắn sự kiện.
                if (value === String(data.company_id)) return
                onChange({ company_id: Number(value) })
              }}
            />
          ) : (
            <ReadOnlyValue>
              {companies.find((company) => company.id === data.company_id)?.name ||
                'Chưa chọn công ty'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5">
          <Label htmlFor="sr-requester">
            Người yêu cầu
            <RequiredMark />
          </Label>
          {editing && !lockRequester && employees.length ? (
            <SearchSelect
              id="sr-requester"
              searchInTrigger
              className={invalidClass('requester')}
              value={data.requester_id ? String(data.requester_id) : ''}
              placeholder="Chọn người yêu cầu"
              searchPlaceholder="Tìm theo mã hoặc tên nhân sự…"
              options={employees.map((employee) => ({
                value: String(employee.id),
                label: `${employee.code} - ${employee.full_name}`,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng người đang chọn thì thôi: Radix Select cũ không bắn sự kiện,
                //  còn chạy tiếp là tra lại TBP và đè mất người đã chọn tay.
                if (value === String(data.requester_id)) return
                pickEmployee(Number(value))
              }}
            />
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
          <Label htmlFor="sr-department">
            Bộ phận YC
            <RequiredMark />
          </Label>
          {editing && departments.length ? (
            //  Phiếu cũ có tên phòng nhưng chưa có id (dữ liệu trước CR-086)
            //  thì ô rỗng — mượn tên đang lưu làm gợi ý để người lập chọn lại.
            <SearchSelect
              id="sr-department"
              searchInTrigger
              value={data.department_id ? String(data.department_id) : ''}
              placeholder={data.department || 'Chọn bộ phận'}
              searchPlaceholder="Gõ để tìm bộ phận…"
              options={departments.map((department) => ({
                value: String(department.id),
                label: department.name,
              }))}
              onChange={(value) => {
                //  Chọn lại đúng phòng đang chọn thì thôi — tránh tra lại TBP vô cớ.
                if (value === String(data.department_id)) return
                pickDepartment(Number(value))
              }}
            />
          ) : (
            <ReadOnlyValue>{data.department || '—'}</ReadOnlyValue>
          )}
        </div>

        {/*
          bao-CR-414 / bao-CR-480 — «Phòng xử lý»: phòng nào sẽ đi mua cho phiếu này, cùng
          luật với YCMH (`0` = Thu mua chung, là một MỤC CHỌN ĐƯỢC).
        */}
        <div className="space-y-1.5">
          <Label htmlFor="sr-handler-dept">Phòng xử lý</Label>
          {editing && departments.length ? (
            <>
              <SearchSelect
                id="sr-handler-dept"
                searchInTrigger
                value={String(data.handler_dept_id || 0)}
                placeholder={SHARED_PURCHASING_LABEL}
                searchPlaceholder="Gõ để tìm phòng ban…"
                options={handlingDeptOptionList}
                onChange={(value) => onChange({ handler_dept_id: Number(value) || 0 })}
              />
              <p className="text-xs text-muted-foreground">{HANDLING_DEPT_HINT}</p>
            </>
          ) : (
            <ReadOnlyValue>{handlingDeptText}</ReadOnlyValue>
          )}
        </div>

        {/* Trưởng bộ phận: mặc định điền theo phòng của người YC, nhưng người lập
            ĐƯỢC chọn TBP phòng ban khác duyệt hộ (QA 29/08) — danh sách lấy từ
            người đã gán ở màn Phòng ban, không nhập tay tên lạ được. */}
        <div className="space-y-1.5">
          <Label htmlFor="sr-dept-head" className={editing ? undefined : 'text-muted-foreground'}>
            Trưởng bộ phận
          </Label>
          {editing && deptHeads.length ? (
            //  TBP đang lưu không nằm trong danh sách thì để ô rỗng, tên nằm ở placeholder —
            //  đưa id vào `value` thì ô hiện nguyên văn con số id.
            <SearchSelect
              id="sr-dept-head"
              searchInTrigger
              value={
                deptHeads.some((head) => head.id === data.head_of_dept_id)
                  ? String(data.head_of_dept_id)
                  : ''
              }
              placeholder={
                deptHeadLookup.isPending ? 'Đang tra…' : data.head_of_dept || 'Chọn Trưởng bộ phận'
              }
              searchPlaceholder="Gõ để tìm Trưởng bộ phận…"
              options={deptHeads.map((head) => ({
                value: String(head.id),
                label: `${head.name} — ${head.departments.join(', ')}`,
              }))}
              onChange={(value) => {
                if (value === String(data.head_of_dept_id)) return
                const head = deptHeads.find((option) => option.id === Number(value))
                if (head) onChange({ head_of_dept_id: head.id, head_of_dept: head.name })
              }}
            />
          ) : (
            <ReadOnlyValue>
              {deptHeadLookup.isPending ? 'Đang tra…' : data.head_of_dept || '—'}
            </ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label>
            Mục đích khảo sát
            <RequiredMark />
          </Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Nhập mục đích cần khảo sát giá..."
              value={data.purpose}
              aria-invalid={invalid?.has('purpose') || undefined}
              onChange={(event) => onChange({ purpose: event.target.value })}
            />
          ) : (
            <ReadOnlyValue multiline>{data.purpose || '—'}</ReadOnlyValue>
          )}
        </div>

        <div className="space-y-1.5 md:col-span-2">
          <Label>Ghi chú</Label>
          {editing ? (
            <Textarea
              rows={3}
              placeholder="Ghi chú thêm cho phiếu..."
              value={data.note}
              onChange={(event) => onChange({ note: event.target.value })}
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
