/**
 * duoc-CR-784 — phần RUỘT của hộp sửa một điều kiện lọc (hiện ngay dưới chip): xu hướng chọn MỘT, vai trò chọn NHIỀU,
 * khoảng số hai ô "từ … đến …" có đơn vị. Không có nút Áp dụng: bấm pill là lọc ngay; gõ số thì đợi 400 ms sau phím cuối
 * mới gửi (gõ tới đâu gọi tới đó thì mỗi phím một lượt tính lại). Đóng hộp giữa lúc đang đợi thì gửi luôn phần đã gõ.
 */
import { useEffect, useRef, useState } from 'react'

import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

import {
  ADVANCED_FILTER_PROFILES,
  IMPACT_FILTER_ROLES,
  TREND_CONDITION_VALUES,
  conditionLabel,
  rangeTextProblem,
  trendConditionLabel,
  type AdvancedFilterVariant,
  type FilterConditionKey,
  type ImpactAdvancedFilters,
  type ImpactRangeKey,
  type ImpactRangeText,
} from '../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS } from '../utils/packaging-product-overview'
import { packagingRoleLabel } from '../utils/packaging-warning-text'

/** Nhịp đợi sau phím cuối trước khi gửi khoảng số lên máy chủ. */
export const RANGE_COMMIT_DELAY_MS = 400

const PILL = 'h-8 rounded-full border px-3 text-sm hover:bg-accent'
const PILL_ON = 'border-primary bg-primary text-primary-foreground hover:bg-primary/90'

interface PackagingFilterConditionEditorProps {
  conditionKey: Exclude<FilterConditionKey, 'warningsOnly'>
  variant: AdvancedFilterVariant
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
  /** Đóng hộp (chọn xong xu hướng thì hộp tự đóng). */
  onClose: () => void
}

export function PackagingFilterConditionEditor({
  conditionKey,
  variant,
  value,
  onChange,
  onClose,
}: PackagingFilterConditionEditorProps) {
  const profile = ADVANCED_FILTER_PROFILES[variant]
  const title = conditionLabel(conditionKey, variant)

  if (conditionKey === 'trend') {
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium">{title}</p>
        <div className="flex flex-wrap gap-1" role="group" aria-label={title}>
          {TREND_CONDITION_VALUES.map((trend) => (
            <button
              key={trend}
              type="button"
              title={OVERVIEW_TREND_CHIPS.find((chip) => chip.value === trend)?.title}
              aria-pressed={value.trend === trend}
              onClick={() => {
                onChange({ ...value, trend })
                onClose()
              }}
              className={cn(PILL, value.trend === trend && PILL_ON)}
            >
              {trendConditionLabel(trend)}
            </button>
          ))}
        </div>
      </div>
    )
  }

  if (conditionKey === 'roles') {
    const toggle = (role: number) =>
      onChange({
        ...value,
        roles: value.roles.includes(role) ? value.roles.filter((r) => r !== role) : [...value.roles, role],
      })
    return (
      <div className="space-y-2">
        <p className="text-sm font-medium">{title}</p>
        <div className="flex flex-wrap gap-1" role="group" aria-label={profile.rolesAriaLabel}>
          {IMPACT_FILTER_ROLES.map((role) => (
            <button
              key={role}
              type="button"
              aria-pressed={value.roles.includes(role)}
              onClick={() => toggle(role)}
              className={cn(PILL, value.roles.includes(role) && PILL_ON)}
            >
              {packagingRoleLabel(role)}
            </button>
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{profile.rolesHint}</p>
      </div>
    )
  }

  return <RangeEditor rangeKey={conditionKey} variant={variant} value={value} onChange={onChange} />
}

function RangeEditor({
  rangeKey,
  variant,
  value,
  onChange,
}: {
  rangeKey: ImpactRangeKey
  variant: AdvancedFilterVariant
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
}) {
  const label = conditionLabel(rangeKey, variant)
  const unit = ADVANCED_FILTER_PROFILES[variant].rangeFields.find((field) => field.key === rangeKey)?.unit ?? ''
  //  Ô nhập giữ DẠNG CHỮ (gõ dở "-" hay "1," không bị nuốt); chỉ ghi lên bộ lọc sau nhịp đợi.
  const [text, setText] = useState<ImpactRangeText>(value[rangeKey])
  const dirty = useRef(false)
  const latest = useRef({ text, value, onChange })
  useEffect(() => {
    latest.current = { text, value, onChange }
  })

  useEffect(() => {
    if (!dirty.current) return
    const timer = setTimeout(() => {
      dirty.current = false
      const { text: typed, value: current, onChange: apply } = latest.current
      apply({ ...current, [rangeKey]: typed })
    }, RANGE_COMMIT_DELAY_MS)
    return () => clearTimeout(timer)
  }, [text, rangeKey])

  //  Đóng hộp khi còn phần gõ chưa gửi → gửi nốt, đừng làm mất điều kiện người dùng vừa nhập.
  useEffect(
    () => () => {
      if (!dirty.current) return
      const { text: typed, value: current, onChange: apply } = latest.current
      apply({ ...current, [rangeKey]: typed })
    },
    [rangeKey],
  )

  const problem = rangeTextProblem(rangeKey, text)
  const edit = (side: 'min' | 'max', next: string) => {
    dirty.current = true
    setText((prev) => ({ ...prev, [side]: next }))
  }

  return (
    <div className="space-y-2">
      <p className="text-sm font-medium">{label}</p>
      <div className="flex items-center gap-2">
        {(['min', 'max'] as const).map((side) => (
          <div key={side} className="flex flex-1 items-center gap-1.5">
            <span className="text-sm text-muted-foreground">{side === 'min' ? 'từ' : 'đến'}</span>
            <Input
              inputMode="decimal"
              className="h-8 min-w-0 text-right"
              aria-label={`${label} ${side === 'min' ? 'từ' : 'đến'}`}
              aria-invalid={problem != null}
              value={text[side]}
              onChange={(event) => edit(side, event.target.value)}
            />
          </div>
        ))}
        {unit && <span className="text-sm text-muted-foreground">{unit}</span>}
      </div>
      {problem && (
        <p role="alert" className="text-xs text-destructive">
          {problem}
        </p>
      )}
    </div>
  )
}
