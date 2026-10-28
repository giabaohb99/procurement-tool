import { ReadOnlyValue } from '@/shared/ui/read-only-value'
import { SearchSelect } from '@/shared/ui/search-select'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { PLAN_PERIOD_TYPE, labelOf } from '@/shared/constants/statuses'
import { buildPeriodNoOptions, formatPeriodLabel } from '../utils/headcount-plan-periods'
import type { HeadcountPlanDraft } from '../utils/headcount-plan-draft'
import { PlanLabeledField } from './plan-labeled-field'

interface Option {
  value: string
  label: string
}

function OptionSelect({
  id,
  value,
  options,
  placeholder,
  onChange,
}: {
  id: string
  value: string
  options: readonly Option[]
  placeholder?: string
  onChange: (value: string) => void
}) {
  return (
    <Select value={value} onValueChange={onChange}>
      <SelectTrigger id={id} className="w-full">
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {options.map((o) => (
          <SelectItem key={o.value} value={o.value}>
            {o.label}
          </SelectItem>
        ))}
      </SelectContent>
    </Select>
  )
}

interface HeadcountPlanPeriodFieldsProps {
  draft: HeadcountPlanDraft
  isNew: boolean
  readOnly: boolean
  yearOptions: readonly Option[]
  companyOptions: readonly Option[]
  departmentOptions: readonly Option[]
  templateOptions: readonly Option[]
  /** Tên pháp nhân · phòng do API trả sẵn — người không đọc được danh mục vẫn thấy tên, không phải «#id». */
  savedNames?: { company?: string; department?: string }
  onPatch: (patch: Partial<HeadcountPlanDraft>) => void
  onPeriodChange: (change: { period_type?: number; period_no?: number }) => void
  onTemplateChange: (templateId: number) => void
}

/**
 * Nửa đầu khối 1 — KỲ (loại kỳ → ô kỳ đổi theo), pháp nhân, phòng, mẫu khoản chi phí.
 *
 * ⚠️ Năm · loại kỳ · kỳ · pháp nhân · phòng là KHÓA của kế hoạch (backend UNIQUE) nên khóa lại khi
 * sửa: đổi khóa của một kế hoạch đã duyệt là chuyển nó sang kỳ khác mà lịch sử vẫn ghi «sửa». Muốn
 * điều chỉnh giữa năm thì lập kế hoạch kỳ hẹp hơn (tài liệu 06 §3). Ô «Mẫu» chỉ có lúc TẠO.
 */
export function HeadcountPlanPeriodFields({
  draft,
  isNew,
  readOnly,
  yearOptions,
  companyOptions,
  departmentOptions,
  templateOptions,
  savedNames,
  onPatch,
  onPeriodChange,
  onTemplateChange,
}: HeadcountPlanPeriodFieldsProps) {
  const locked = !isNew || readOnly
  const findLabel = (options: readonly Option[], value: number) =>
    options.find((o) => o.value === String(value))?.label ?? (value ? `#${value}` : '')

  if (locked) {
    return (
      <>
        <PlanLabeledField label="Kỳ kế hoạch">
          <ReadOnlyValue>
            {formatPeriodLabel(draft.period_type, draft.period_no, draft.year)} ·{' '}
            {labelOf(PLAN_PERIOD_TYPE, String(draft.period_type))}
          </ReadOnlyValue>
        </PlanLabeledField>
        <PlanLabeledField label="Pháp nhân · Phòng ban">
          <ReadOnlyValue>
            {savedNames?.company || findLabel(companyOptions, draft.company_id)} ·{' '}
            {savedNames?.department || findLabel(departmentOptions, draft.department_id)}
          </ReadOnlyValue>
        </PlanLabeledField>
      </>
    )
  }

  return (
    <>
      <PlanLabeledField label="Năm" htmlFor="hp-year" required>
        <OptionSelect
          id="hp-year"
          value={String(draft.year)}
          options={yearOptions}
          onChange={(v) => onPatch({ year: Number(v) })}
        />
      </PlanLabeledField>
      <PlanLabeledField label="Loại kỳ" htmlFor="hp-period-type" required>
        <OptionSelect
          id="hp-period-type"
          value={String(draft.period_type)}
          options={PLAN_PERIOD_TYPE}
          onChange={(v) => onPeriodChange({ period_type: Number(v) })}
        />
      </PlanLabeledField>
      <PlanLabeledField
        label="Kỳ"
        htmlFor="hp-period-no"
        required
        hint={`Kế hoạch: ${formatPeriodLabel(draft.period_type, draft.period_no, draft.year)}`}
      >
        <OptionSelect
          id="hp-period-no"
          value={String(draft.period_no)}
          options={buildPeriodNoOptions(draft.period_type)}
          onChange={(v) => onPeriodChange({ period_no: Number(v) })}
        />
      </PlanLabeledField>
      <PlanLabeledField label="Pháp nhân" htmlFor="hp-company" required>
        <SearchSelect
          id="hp-company"
          value={draft.company_id ? String(draft.company_id) : ''}
          options={[...companyOptions]}
          placeholder="Chọn pháp nhân"
          searchPlaceholder="Tìm pháp nhân…"
          onChange={(v) => onPatch({ company_id: Number(v) || 0 })}
        />
      </PlanLabeledField>
      <PlanLabeledField
        label="Phòng ban"
        htmlFor="hp-department"
        required
        hint="«Toàn pháp nhân» = kế hoạch của cả pháp nhân. Phòng ban dùng chung cho mọi pháp nhân."
      >
        <SearchSelect
          id="hp-department"
          value={String(draft.department_id)}
          options={[...departmentOptions]}
          searchPlaceholder="Tìm phòng ban…"
          onChange={(v) => onPatch({ department_id: Number(v) || 0 })}
        />
      </PlanLabeledField>
      <PlanLabeledField
        label="Mẫu khoản chi phí"
        htmlFor="hp-template"
        required
        hint="Hệ thống CHÉP bộ khoản của mẫu vào kế hoạch này. Sửa mẫu về sau không làm đổi kế hoạch đã lập."
      >
        <OptionSelect
          id="hp-template"
          value={draft.template_id ? String(draft.template_id) : ''}
          options={templateOptions}
          placeholder={templateOptions.length ? 'Chọn mẫu' : 'Chưa có mẫu nào đang dùng'}
          onChange={(v) => onTemplateChange(Number(v))}
        />
      </PlanLabeledField>
    </>
  )
}
