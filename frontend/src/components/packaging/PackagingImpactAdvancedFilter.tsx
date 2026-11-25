import { useLayoutEffect, useRef, useState } from 'react'
import { createPortal } from 'react-dom'
import {
  ADVANCED_FILTER_PROFILES, EMPTY_IMPACT_FILTERS, IMPACT_FILTER_ROLES, countAdvancedFilters, invalidImpactRanges,
} from '../../utils/packaging-impact-filters'
import type {
  AdvancedFilterProfile, AdvancedFilterVariant, ImpactAdvancedFilters, ImpactRangeKey,
} from '../../utils/packaging-impact-filters'
import { OVERVIEW_TREND_CHIPS } from '../../utils/packaging-overview'
import { roleLabel } from '../../utils/packaging-price'
import './packaging.css'

/** Bề rộng hộp lọc (px) — dùng để kẹp hộp trong màn khi nút nằm sát mép phải. */
const PANEL_WIDTH = 460

/**
 * duoc-CR-784 — nút + hộp LỌC NÂNG CAO của bảng sản phẩm bị ảnh hưởng (màn Tác động giá, bản v1) và của màn Tổng hợp theo
 * sản phẩm (`variant="overview"`: thêm ô CP/chai cũ + % chênh, bỏ mục xu hướng vì đã có chip riêng). Biểu mẫu nhỏ: xu hướng,
 * vai trò của mã đã chọn, bốn khoảng số, chỉ-có-cảnh-báo. Người dùng sửa trên BẢN NHÁP, bấm Áp dụng mới gửi máy chủ (gõ tới
 * đâu gọi tới đó thì mỗi phím một lượt tính lại). Nút hiện huy hiệu số nhóm điều kiện đang bật. Hộp vẽ qua portal để không bị
 * `overflow` của thẻ cắt (cùng nếp với menu chọn cột).
 */
export default function PackagingImpactAdvancedFilter({ value, onApply, variant = 'impact' }: {
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onApply: (next: ImpactAdvancedFilters) => void
  /** Màn dùng hộp lọc; mặc định Tác động giá. */
  variant?: AdvancedFilterVariant
}) {
  const [open, setOpen] = useState(false)
  const [pos, setPos] = useState({ top: 0, left: 0 })
  const btnRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLDivElement>(null)
  const profile = ADVANCED_FILTER_PROFILES[variant]
  const count = countAdvancedFilters(value, variant)

  useLayoutEffect(() => {
    if (!open) return
    function place() {
      const r = btnRef.current?.getBoundingClientRect()
      if (!r) return
      //  Hộp cao hơn chỗ trống bên dưới nút thì dời lên cho vừa màn (hộp tự cuộn nếu màn còn thấp hơn nữa).
      const height = panelRef.current?.offsetHeight ?? 0
      const top = Math.max(8, Math.min(r.bottom + 6, window.innerHeight - height - 8))
      setPos({ top, left: Math.max(8, Math.min(r.left, window.innerWidth - PANEL_WIDTH - 8)) })
    }
    place()
    function onDown(e: MouseEvent) {
      const t = e.target as Node
      if (!panelRef.current?.contains(t) && !btnRef.current?.contains(t)) setOpen(false)
    }
    function onKey(e: KeyboardEvent) { if (e.key === 'Escape') setOpen(false) }
    function onScroll(e: Event) { if (!panelRef.current?.contains(e.target as Node)) place() }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    window.addEventListener('resize', place)
    window.addEventListener('scroll', onScroll, true)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', onScroll, true)
    }
  }, [open])

  return (
    <>
      <button ref={btnRef} type="button" className={count ? 'btn secondary' : 'btn outline'} aria-label="Lọc nâng cao"
        aria-expanded={open} onClick={() => setOpen((v) => !v)}>
        <i className="ti ti-filter" />Lọc nâng cao{count > 0 && <span className="pkg-badge">{count}</span>}
      </button>
      {open && createPortal(
        <div ref={panelRef} className="pkg-filter-panel" role="dialog" aria-label="Lọc nâng cao"
          style={{ top: pos.top, left: pos.left, width: PANEL_WIDTH }}>
          {/*  Chỉ dựng khi mở → bản nháp luôn khởi tạo lại từ bộ lọc đang áp. */}
          <FilterForm initial={value} profile={profile} onApply={(next) => { onApply(next); setOpen(false) }} />
        </div>,
        document.body,
      )}
    </>
  )
}

function FilterForm({ initial, profile, onApply }: {
  initial: ImpactAdvancedFilters; profile: AdvancedFilterProfile; onApply: (next: ImpactAdvancedFilters) => void
}) {
  const [draft, setDraft] = useState<ImpactAdvancedFilters>(initial)
  const bad = invalidImpactRanges(draft, profile.rangeFields)

  const toggleRole = (role: number) =>
    setDraft((p) => ({ ...p, roles: p.roles.includes(role) ? p.roles.filter((r) => r !== role) : [...p.roles, role] }))
  const setRange = (key: ImpactRangeKey, side: 'min' | 'max', text: string) =>
    setDraft((p) => ({ ...p, [key]: { ...p[key], [side]: text } }))

  return (
    <>
      {profile.showTrend && (
        <div className="pkg-filter-sec">
          <div className="pkg-filter-lbl">Xu hướng chi phí</div>
          <div className="pkg-pills" role="group" aria-label="Xu hướng chi phí">
            {OVERVIEW_TREND_CHIPS.map((c) => (
              <button key={c.value} type="button" title={c.title} className={'pkg-pill' + (draft.trend === c.value ? ' on' : '')}
                aria-pressed={draft.trend === c.value} onClick={() => setDraft((p) => ({ ...p, trend: c.value }))}>{c.label}</button>
            ))}
          </div>
        </div>
      )}

      <div className="pkg-filter-sec">
        <div className="pkg-filter-lbl">{profile.rolesLabel}</div>
        <div className="pkg-pills" role="group" aria-label={profile.rolesAriaLabel}>
          {IMPACT_FILTER_ROLES.map((role) => (
            <button key={role} type="button" className={'pkg-pill' + (draft.roles.includes(role) ? ' on' : '')}
              aria-pressed={draft.roles.includes(role)} onClick={() => toggleRole(role)}>{roleLabel(role)}</button>
          ))}
        </div>
        <div className="pkg-hint">{profile.rolesHint}</div>
      </div>

      <div className="pkg-filter-sec">
        {profile.rangeFields.map(({ key, label, unit }) => (
          <div key={key} className="pkg-filter-range">
            <span className="pkg-filter-lbl">{label}{unit && <span className="pkg-muted"> ({unit})</span>}</span>
            {(['min', 'max'] as const).map((side) => (
              <input key={side} inputMode="decimal" style={{ textAlign: 'right' }} aria-label={`${label} ${side === 'min' ? 'từ' : 'đến'}`}
                aria-invalid={bad.includes(key)} placeholder={side === 'min' ? 'Từ' : 'Đến'} value={draft[key][side]}
                onChange={(e) => setRange(key, side, e.target.value)} />
            ))}
            {bad.includes(key) && (
              <div role="alert" className="pkg-err pkg-filter-err">&quot;Từ&quot; không được lớn hơn &quot;Đến&quot; — điều kiện này chưa được áp dụng.</div>
            )}
          </div>
        ))}
      </div>

      <label className="pkg-switch" style={{ alignItems: 'flex-start', whiteSpace: 'normal' }}>
        <input type="checkbox" checked={draft.warningsOnly} onChange={(e) => setDraft((p) => ({ ...p, warningsOnly: e.target.checked }))} />
        <span>
          Chỉ sản phẩm có cảnh báo
          <span className="pkg-hint" style={{ display: 'block' }}>
            Thiếu giá / mã thành phần, thiếu quy cách thùng, lệch ĐVT, dưới sàn hoặc vượt trần.
          </span>
        </span>
      </label>

      <div className="pkg-filter-foot">
        <button type="button" className="btn ghost" onClick={() => setDraft(EMPTY_IMPACT_FILTERS)}>Xóa lọc</button>
        <button type="button" className="btn" onClick={() => onApply(draft)}>Áp dụng</button>
      </div>
    </>
  )
}
