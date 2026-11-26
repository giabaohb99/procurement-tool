import { useRef, useState, type ReactNode } from 'react'
import {
  ADVANCED_FILTER_PROFILES, WARNINGS_ONLY_HINT, clearCondition, conditionLabel, isConditionActive, summarizeCondition,
} from '../../utils/packaging-impact-filters'
import type { AdvancedFilterVariant, FilterConditionKey, ImpactAdvancedFilters } from '../../utils/packaging-impact-filters'
import PackagingAnchoredPanel from './PackagingAnchoredPanel'
import PackagingFilterConditionEditor from './PackagingFilterConditionEditor'
import './packaging.css'

/**
 * duoc-CR-784 — THANH LỌC DẠNG CHIP của hai màn Tác động giá bao bì và Tổng hợp theo sản phẩm (bản v1; thay hộp "Lọc nâng cao",
 * người chủ chốt 26/11/2026: "cái bộ lọc khó xài quá"). Hàng một: ô tìm + nút "Thêm điều kiện" (menu các trường chưa bật) +
 * phần riêng của màn (`children`: chip xu hướng kèm số đếm / dòng "Đang lọc"). Hàng hai chỉ hiện khi có điều kiện: mỗi điều
 * kiện đang bật là một chip ghi câu tóm tắt; bấm chip = sửa ngay tại chỗ, nút x = bỏ.
 *
 * Lọc NGAY (không có nút Áp dụng); khoảng số đợi 400 ms sau phím cuối. Trạng thái vẫn là `ImpactAdvancedFilters` nên thân
 * `POST /impact`, tham số `GET /product-overview` và bản in không đổi. Đặt làm con của `TableToolbar`: hàng chip dùng
 * `order: 1; flex-basis: 100%` (xem `.pkg-chips`) nên nằm DƯỚI hàng một và nhóm nút Cột / Tải lại của bảng.
 */
export default function PackagingFilterChipBar({ variant, value, onChange, keyword, onKeyword, children }: {
  variant: AdvancedFilterVariant
  /** Bộ lọc đang áp. */
  value: ImpactAdvancedFilters
  onChange: (next: ImpactAdvancedFilters) => void
  keyword: string
  onKeyword: (v: string) => void
  /** Phần riêng của màn, đứng sau nút "Thêm điều kiện" trên hàng một. */
  children?: ReactNode
}) {
  //  Điều kiện vừa thêm / đang sửa. Chưa nhập gì thì vẫn hiện chip (để hộp sửa neo vào), đóng hộp mà còn trống thì chip biến mất.
  const [editing, setEditing] = useState<FilterConditionKey | null>(null)
  const [menuOpen, setMenuOpen] = useState(false)
  const addRef = useRef<HTMLButtonElement>(null)
  const order = ADVANCED_FILTER_PROFILES[variant].conditionOrder
  const chips = order.filter((key) => isConditionActive(value, key) || key === editing)
  const addable = order.filter((key) => !chips.includes(key))

  const addCondition = (key: FilterConditionKey) => {
    setMenuOpen(false)
    //  Cờ bật/tắt không cần chỗ nhập: thêm là lọc luôn.
    if (key === 'warningsOnly') onChange({ ...value, warningsOnly: true })
    else setEditing(key)
  }
  const removeCondition = (key: FilterConditionKey) => {
    if (editing === key) setEditing(null)
    onChange(clearCondition(value, key))
  }

  return (
    <>
      <div className="pkg-row" style={{ flex: '1 1 320px', minWidth: 0 }}>
        <div className="pkg-search">
          <input aria-label="Tìm sản phẩm" placeholder="Tìm mã HH, tên, mã thành phần…" value={keyword}
            onChange={(e) => onKeyword(e.target.value)} />
        </div>
        <button ref={addRef} type="button" className="btn ghost" aria-haspopup="menu" aria-expanded={menuOpen}
          disabled={addable.length === 0} onClick={() => setMenuOpen((v) => !v)}>
          <i className="ti ti-plus" />Thêm điều kiện<i className="ti ti-chevron-down" />
        </button>
        {children}
      </div>
      {menuOpen && (
        <PackagingAnchoredPanel anchorRef={addRef} width={280} label="Thêm điều kiện" onClose={() => setMenuOpen(false)}>
          <div className="pkg-menu" role="menu">
            {addable.map((key) => (
              <button key={key} type="button" role="menuitem" className="pkg-menu-item" onClick={() => addCondition(key)}>
                {conditionLabel(key, variant)}
                {key === 'warningsOnly' && <span className="pkg-hint">{WARNINGS_ONLY_HINT}</span>}
              </button>
            ))}
          </div>
        </PackagingAnchoredPanel>
      )}
      {chips.length > 0 && (
        <div className="pkg-chips" role="group" aria-label="Điều kiện lọc đang bật">
          {chips.map((key) => (
            <ConditionChip key={key} conditionKey={key} variant={variant} value={value} open={editing === key}
              onToggle={() => setEditing((cur) => (cur === key ? null : key))} onClose={() => setEditing(null)}
              onChange={onChange} onRemove={() => removeCondition(key)} />
          ))}
        </div>
      )}
    </>
  )
}

function ConditionChip({ conditionKey, variant, value, open, onToggle, onClose, onChange, onRemove }: {
  conditionKey: FilterConditionKey
  variant: AdvancedFilterVariant
  value: ImpactAdvancedFilters
  open: boolean
  onToggle: () => void
  onClose: () => void
  onChange: (next: ImpactAdvancedFilters) => void
  onRemove: () => void
}) {
  const anchorRef = useRef<HTMLSpanElement>(null)
  const label = conditionLabel(conditionKey, variant)
  const text = summarizeCondition(value, conditionKey)
  const removeButton = (
    <button type="button" className="pkg-chip-x" aria-label={`Bỏ điều kiện ${label}`} title="Bỏ điều kiện" onClick={onRemove}>
      <i className="ti ti-x" />
    </button>
  )

  //  Cờ cảnh báo không có gì để sửa: chip chỉ là nhãn + nút bỏ.
  if (conditionKey === 'warningsOnly') {
    return <span className="pkg-chip" title={WARNINGS_ONLY_HINT}><span className="pkg-chip-body static">{text}</span>{removeButton}</span>
  }
  return (
    <>
      <span ref={anchorRef} className={'pkg-chip' + (open ? ' open' : '')}>
        <button type="button" className="pkg-chip-body" aria-label={`Sửa điều kiện: ${text}`} aria-expanded={open} onClick={onToggle}>{text}</button>
        {removeButton}
      </span>
      {open && (
        <PackagingAnchoredPanel anchorRef={anchorRef} width={320} label={label} onClose={onClose}>
          <PackagingFilterConditionEditor conditionKey={conditionKey} variant={variant} value={value} onChange={onChange} onClose={onClose} />
        </PackagingAnchoredPanel>
      )}
    </>
  )
}
