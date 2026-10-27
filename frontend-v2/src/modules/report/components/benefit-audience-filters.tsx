import type { ReactNode } from 'react'
import { useSearchParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { EMPLOYEE_GENDER_OPTIONS } from '@/modules/hr/types/employee'
import { useUrlParamState, useSetUrlParams } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Switch } from '@/shared/ui/switch'

import { BENEFIT_MAX_AMOUNT } from '../utils/benefit-amount-param'
import {
  BENEFIT_INPUT_DEBOUNCE_MS,
  BENEFIT_MAX_AGE,
  BENEFIT_MAX_LABEL,
  BENEFIT_PARAM,
  buildOccasionDateParams,
  resolveOccasionDate,
} from '../utils/benefit-occasion-presets'
import { BenefitActiveConditions } from './benefit-active-conditions'
import { BenefitOccasionPresetChips } from './benefit-occasion-preset-chips'
import { BenefitUrlNumberInput } from './benefit-url-number-input'
import { ReportDepartmentFilter } from './report-department-filter'

/** Mốc «Mọi giới tính» — chuỗi, KHÔNG `0`: `gender=0` là nhóm «Chưa khai» thật. */
const ALL_GENDERS = 'all'

function Field({ id, label, children }: { id: string; label: string; children: ReactNode }) {
  return (
    <div className="flex min-w-0 flex-col gap-1.5">
      <Label htmlFor={id}>{label}</Label>
      {children}
    </div>
  )
}

/**
 * Ô lọc riêng của «Phúc lợi & sự kiện» (H1, duoc-CR-688, `ReportPageConfig.extraFilters`):
 * một khung đủ hàng ngang (dịp có sẵn · ngày dịp · tên dịp · giới tính · tuổi · mức quà ·
 * người đang nghỉ) rồi ô phòng ban đứng chung hàng với ô Công ty. Mọi giá trị nằm trên URL,
 * `useReportFilters().queryParams` tự gom gửi `/summary`, `/rows` và tệp ký nhận.
 *
 * Ô tuổi + dịp lọc theo ngày sinh / tuổi con khóa lại khi thiếu `employee_sensitive.read`
 * (chỉ để đỡ vướng — backend mới là chỗ chặn, trả 403 câu dễ hiểu).
 */
export function BenefitAudienceFilters() {
  const { can } = usePermission()
  const canUseSensitive = can('employee_sensitive', 'read')
  const [searchParams] = useSearchParams()
  const setParams = useSetUrlParams()
  const occasionDate = resolveOccasionDate(searchParams)
  const [gender, setGender] = useUrlParamState(BENEFIT_PARAM.gender, ALL_GENDERS)
  const [onLeave, setOnLeave] = useUrlParamState(BENEFIT_PARAM.includeOnLeave, '1')
  const label = useUrlSearchParam(BENEFIT_PARAM.occasionLabel, BENEFIT_INPUT_DEBOUNCE_MS)

  return (
    <>
      <section
        aria-label="Đối tượng nhận quà"
        className="flex basis-full flex-col gap-3 rounded-lg border bg-card p-3 sm:p-4"
      >
        <BenefitOccasionPresetChips occasionDate={occasionDate} canUseSensitive={canUseSensitive} />

        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          <Field id="benefit-occasion-date" label="Ngày dịp">
            <DatePicker
              id="benefit-occasion-date"
              value={occasionDate}
              clearable={false}
              onChange={(day) => day && setParams(buildOccasionDateParams(day, searchParams, occasionDate))}
            />
          </Field>
          <Field id="benefit-occasion-label" label="Tên dịp (tiêu đề danh sách ký nhận)">
            <Input
              id="benefit-occasion-label"
              value={label.value}
              maxLength={BENEFIT_MAX_LABEL}
              placeholder="VD: Quốc tế Phụ nữ 8/3"
              onChange={(e) => label.setValue(e.target.value)}
            />
          </Field>
          <Field id="benefit-gender" label="Giới tính">
            <Select value={gender} onValueChange={setGender}>
              <SelectTrigger id="benefit-gender" className="w-full">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value={ALL_GENDERS}>Mọi giới tính</SelectItem>
                {EMPLOYEE_GENDER_OPTIONS.map((o) => (
                  <SelectItem key={o.value} value={String(o.value)}>
                    {o.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </Field>
          <Field id="benefit-age-min" label="Tuổi tại ngày dịp (từ – đến)">
            <div className="flex items-center gap-2">
              <BenefitUrlNumberInput
                name={BENEFIT_PARAM.ageMin}
                id="benefit-age-min"
                max={BENEFIT_MAX_AGE}
                placeholder="Từ"
                disabled={!canUseSensitive}
              />
              <span className="text-muted-foreground" aria-hidden>
                –
              </span>
              <BenefitUrlNumberInput
                name={BENEFIT_PARAM.ageMax}
                id="benefit-age-max"
                max={BENEFIT_MAX_AGE}
                placeholder="Đến"
                disabled={!canUseSensitive}
              />
            </div>
          </Field>
          <Field id="benefit-amount-staff" label="Mức quà nhân viên (đ)">
            <BenefitUrlNumberInput
              name={BENEFIT_PARAM.amountStaff}
              id="benefit-amount-staff"
              max={BENEFIT_MAX_AMOUNT}
              placeholder="0"
            />
          </Field>
          <Field id="benefit-amount-manager" label="Mức quà quản lý — từ Phó phòng (đ)">
            <BenefitUrlNumberInput
              name={BENEFIT_PARAM.amountManager}
              id="benefit-amount-manager"
              max={BENEFIT_MAX_AMOUNT}
              placeholder="0"
            />
          </Field>
          <div className="flex items-center gap-2 self-end pb-2">
            <Switch
              id="benefit-include-on-leave"
              checked={onLeave !== '0'}
              onCheckedChange={(checked) => setOnLeave(checked ? '1' : '0')}
            />
            <Label htmlFor="benefit-include-on-leave">Tính người đang nghỉ</Label>
          </div>
        </div>

        <BenefitActiveConditions />
        {!canUseSensitive && (
          <p className="text-xs text-muted-foreground">
            Lọc theo tuổi, tháng sinh và tuổi con cần quyền xem ngày sinh và người thân của nhân sự.
          </p>
        )}
      </section>
      <ReportDepartmentFilter />
    </>
  )
}
