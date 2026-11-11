import { usePermission } from '@/core/authorization/use-permission'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Checkbox } from '@/shared/ui/checkbox'
import { DatePicker } from '@/shared/ui/date-picker'
import { HelpHint } from '@/shared/ui/help-hint'
import { Label } from '@/shared/ui/label'
import { RequiredMark } from '@/shared/ui/required-mark'
import { LeavePolicySelect } from './leave-policy-select'
import { EmployeeFilterSelect } from './employee-filter-select'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useActiveLeavePolicies } from '../hooks/use-leave-policy'
import { EMPLOYMENT_TYPE_FILTER_OPTIONS, JOB_LEVEL_FILTER_OPTIONS } from '../types/employee-codes'
import type { BulkSettings } from '../utils/leave-policy-bulk'
import { LEAVE_POLICY_FROM_DATE_HINT, LEAVE_POLICY_TO_DATE_HINT } from '../utils/leave-policy-date-hints'

interface LeavePolicyBulkSettingsFormProps {
  value: BulkSettings
  onChange: (next: BulkSettings) => void
}

function TickRow({ checked, onChange, title, hint }: { checked: boolean; onChange: (v: boolean) => void; title: string; hint: string }) {
  return (
    <label className="flex items-start gap-2 text-sm">
      <Checkbox checked={checked} onCheckedChange={(v) => onChange(v === true)} className="mt-0.5" />
      <span>
        {title}
        <span className="block text-xs text-muted-foreground">{hint}</span>
      </span>
    </label>
  )
}

/**
 * Hai khối đầu của trang Phân bổ hàng loạt (duoc-CR-717): (1) chính sách + khoảng ngày + hai ô tick,
 * (2) lọc nhân sự. Ô lọc pháp nhân / phòng ban chỉ dựng khi đọc được danh mục đó (mount là gọi API).
 */
export function LeavePolicyBulkSettingsForm({ value, onChange }: LeavePolicyBulkSettingsFormProps) {
  const { can } = usePermission()
  const canReadCompany = can('company', 'read')
  const canReadDepartment = can('department', 'read')
  const set = <K extends keyof BulkSettings>(key: K, v: BulkSettings[K]) => onChange({ ...value, [key]: v })

  const { data: policyData, isLoading: policiesLoading } = useActiveLeavePolicies()
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: canReadCompany })
  //  ⚠️ Phòng ban KHÔNG lọc theo pháp nhân (review M5): phòng ban dùng chung (`company_id = 0`, không có dòng
  //  `tab_department_company`) nên `?company_id=` trả rỗng. Backend tự giao hai ô lọc lúc xem trước.
  const { data: departments } = useDepartments({ page_size: 500, is_active: true }, { enabled: canReadDepartment })
  const rangeError = value.to && value.from && value.to < value.from

  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <Card className="gap-4">
        <CardHeader>
          <CardTitle className="text-base">1. Chính sách và thời gian</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-1.5 sm:col-span-2">
            <Label htmlFor="bulk-policy">
              Chính sách
              <RequiredMark />
            </Label>
            <LeavePolicySelect
              id="bulk-policy"
              policies={policyData?.items ?? []}
              isLoading={policiesLoading}
              value={value.policyId}
              onChange={(id) => set('policyId', id)}
            />
          </div>
          <div className="space-y-1.5">
            <Label>
              Từ ngày
              <RequiredMark />
              <HelpHint label="Giải thích Từ ngày">{LEAVE_POLICY_FROM_DATE_HINT}</HelpHint>
            </Label>
            <DatePicker value={value.from} onChange={(v) => set('from', v)} clearable={false} />
          </div>
          <div className="space-y-1.5">
            <Label>
              Đến ngày
              <HelpHint label="Giải thích Đến ngày">{LEAVE_POLICY_TO_DATE_HINT}</HelpHint>
            </Label>
            <DatePicker value={value.to} onChange={(v) => set('to', v)} placeholder="Không thời hạn" />
            {rangeError && (
              <p className="text-xs text-destructive">
                <strong>Đến ngày</strong> không được trước <strong>Từ ngày</strong>.
              </p>
            )}
          </div>
          <div className="space-y-3 sm:col-span-2">
            <TickRow
              checked={value.recalc}
              onChange={(v) => set('recalc', v)}
              title="Tính lại hạn mức năm nay cho quỹ đã cấp"
              hint="Bỏ tick thì quỹ năm nay đã cấp giữ nguyên, chính sách chỉ áp cho lần cấp quỹ sau."
            />
            <TickRow
              checked={value.closePrevious}
              onChange={(v) => set('closePrevious', v)}
              title="Kết thúc chính sách đang hiệu lực"
              hint="Người đang có chính sách khác chồng ngày: đặt ngày kết thúc lượt cũ = ngày bắt đầu mới trừ 1."
            />
          </div>
        </CardContent>
      </Card>

      <Card className="gap-4">
        <CardHeader>
          <CardTitle className="text-base">2. Chọn nhân sự</CardTitle>
        </CardHeader>
        <CardContent className="grid gap-4 sm:grid-cols-2">
          {canReadCompany && (
            <EmployeeFilterSelect
              id="bulk-company"
              label="Pháp nhân"
              value={value.companyId}
              onChange={(v) => set('companyId', v)}
              anyLabel="Mọi pháp nhân"
              options={(companies?.items ?? []).map((c) => ({ value: c.id, label: c.name }))}
            />
          )}
          {canReadDepartment && (
            <EmployeeFilterSelect
              id="bulk-department"
              label="Phòng ban"
              value={value.departmentId}
              onChange={(v) => set('departmentId', v)}
              anyLabel="Mọi phòng ban"
              options={(departments?.items ?? []).map((d) => ({ value: d.id, label: d.name }))}
            />
          )}
          <EmployeeFilterSelect
            id="bulk-employment-type"
            label="Hình thức nhân viên"
            value={value.employmentType}
            onChange={(v) => set('employmentType', v)}
            anyLabel="Mọi hình thức"
            options={EMPLOYMENT_TYPE_FILTER_OPTIONS}
          />
          <EmployeeFilterSelect
            id="bulk-job-level"
            label="Cấp bậc"
            value={value.jobLevel}
            onChange={(v) => set('jobLevel', v)}
            anyLabel="Mọi cấp bậc"
            options={JOB_LEVEL_FILTER_OPTIONS}
          />
          <div className="sm:col-span-2">
            <TickRow
              checked={value.onlyWithoutActive}
              onChange={(v) => set('onlyWithoutActive', v)}
              title="Chỉ người chưa có chính sách hiệu lực hôm nay"
              hint='Bỏ tick để thấy cả người đang có chính sách (họ sẽ báo chồng ngày nếu không tick "Kết thúc…").'
            />
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
