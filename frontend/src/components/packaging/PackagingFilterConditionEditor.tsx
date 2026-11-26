import { useEffect, useRef, useState } from 'react'
import {
  ADVANCED_FILTER_PROFILES, IMPACT_FILTER_ROLES, TREND_CONDITION_VALUES, conditionLabel, rangeTextProblem, trendConditionLabel,
} from '../../utils/packaging-impact-filters'
import type {
  AdvancedFilterVariant, FilterConditionKey, ImpactAdvancedFilters, ImpactRangeKey, ImpactRangeText,
} from '../../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS } from '../../utils/packaging-overview'
import { roleLabel } from '../../utils/packaging-price'
import './packaging.css'

/** Nhịp đợi sau phím cuối trước khi gửi khoảng số lên máy chủ. */
export const RANGE_COMMIT_DELAY_MS = 400

/**
 * duoc-CR-784 — RUỘT hộp sửa một điều kiện lọc (hiện dưới chip, bản v1): xu hướng chọn MỘT, vai trò chọn NHIỀU, khoảng số
 * hai ô "từ … đến …" có đơn vị. Không có nút Áp dụng: bấm pill là lọc ngay; gõ số thì đợi 400 ms sau phím cuối mới gửi (gõ tới
 * đâu gọi tới đó thì mỗi phím một lượt tính lại). Đóng hộp giữa lúc đang đợi thì gửi luôn phần đã gõ. Cùng hành vi bản v2.
 */
export default function PackagingFilterConditionEditor({ conditionKey, variant, value, onChange, onClose }: {
  conditionKey: Exclude<FilterConditionKey, 'warningsOnly'>
  variant: AdvancedFilterVariant
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
  /** Đóng hộp (chọn xong xu hướng thì hộp tự đóng). */
  onClose: () => void
}) {
  const profile = ADVANCED_FILTER_PROFILES[variant]
  const title = conditionLabel(conditionKey, variant)

  if (conditionKey === 'trend') {
    return (
      <div className="pkg-filter-sec">
        <div className="pkg-filter-lbl">{title}</div>
        <div className="pkg-pills" role="group" aria-label={title}>
          {TREND_CONDITION_VALUES.map((trend) => (
            <button key={trend} type="button" title={OVERVIEW_TREND_CHIPS.find((c) => c.value === trend)?.title}
              className={'pkg-pill' + (value.trend === trend ? ' on' : '')} aria-pressed={value.trend === trend}
              onClick={() => { onChange({ ...value, trend }); onClose() }}>{trendConditionLabel(trend)}</button>
          ))}
        </div>
      </div>
    )
  }

  if (conditionKey === 'roles') {
    const toggle = (role: number) => onChange({
      ...value, roles: value.roles.includes(role) ? value.roles.filter((r) => r !== role) : [...value.roles, role],
    })
    return (
      <div className="pkg-filter-sec">
        <div className="pkg-filter-lbl">{title}</div>
        <div className="pkg-pills" role="group" aria-label={profile.rolesAriaLabel}>
          {IMPACT_FILTER_ROLES.map((role) => (
            <button key={role} type="button" className={'pkg-pill' + (value.roles.includes(role) ? ' on' : '')}
              aria-pressed={value.roles.includes(role)} onClick={() => toggle(role)}>{roleLabel(role)}</button>
          ))}
        </div>
        <div className="pkg-hint">{profile.rolesHint}</div>
      </div>
    )
  }

  return <RangeEditor rangeKey={conditionKey} variant={variant} value={value} onChange={onChange} />
}

function RangeEditor({ rangeKey, variant, value, onChange }: {
  rangeKey: ImpactRangeKey
  variant: AdvancedFilterVariant
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
}) {
  const label = conditionLabel(rangeKey, variant)
  const unit = ADVANCED_FILTER_PROFILES[variant].rangeFields.find((f) => f.key === rangeKey)?.unit ?? ''
  //  Ô nhập giữ DẠNG CHỮ (gõ dở "-" hay "1," không bị nuốt); chỉ ghi lên bộ lọc sau nhịp đợi.
  const [text, setText] = useState<ImpactRangeText>(value[rangeKey])
  const dirty = useRef(false)
  const latest = useRef({ text, value, onChange })
  useEffect(() => { latest.current = { text, value, onChange } })

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
  useEffect(() => () => {
    if (!dirty.current) return
    const { text: typed, value: current, onChange: apply } = latest.current
    apply({ ...current, [rangeKey]: typed })
  }, [rangeKey])

  const problem = rangeTextProblem(rangeKey, text)
  const edit = (side: 'min' | 'max', next: string) => { dirty.current = true; setText((p) => ({ ...p, [side]: next })) }

  return (
    <div className="pkg-filter-sec">
      <div className="pkg-filter-lbl">{label}</div>
      <div className="pkg-cond-range">
        {(['min', 'max'] as const).map((side) => (
          <label key={side} className="pkg-cond-side">
            <span className="pkg-muted">{side === 'min' ? 'từ' : 'đến'}</span>
            <input autoFocus={side === 'min'} inputMode="decimal" style={{ textAlign: 'right' }}
              aria-label={`${label} ${side === 'min' ? 'từ' : 'đến'}`} aria-invalid={problem != null}
              value={text[side]} onChange={(e) => edit(side, e.target.value)} />
          </label>
        ))}
        {unit && <span className="pkg-muted">{unit}</span>}
      </div>
      {problem && <div role="alert" className="pkg-err">{problem}</div>}
    </div>
  )
}
