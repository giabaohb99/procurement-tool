import { useEffect, useMemo, useRef, useState } from 'react'
import { toast } from '../toast'
import type { PackagingCodeOption } from '../../api/packaging-cost-types'
import { priceText, PACKAGING_ROLE_LABELS } from '../../utils/packaging-price'
import { buildCodeMatcher, collectSearchGroups, PACKAGING_MAX_CODES } from '../../utils/packaging-query'
import './packaging.css'

/** Số chip hiện trong ô trước khi gộp thành "+n mã" — chọn cả nhóm hàng trăm mã thì ô không phình. */
const CHIP_MAX = 12
/** Số dòng vẽ trong danh sách; "Chọn tất cả" vẫn áp cho MỌI mã khớp, kể cả phần chưa vẽ. */
const LIST_MAX = 200

/** `material` = mã vật tư bao bì (tìm theo tên nhóm, kèm số SP + giá mới); `product` = mã sản phẩm có định mức. */
export type PackagingPickerKind = 'material' | 'product'

const TEXT: Record<PackagingPickerKind, { empty: string; more: string; search: string; hint: string; summary: string }> = {
  material: {
    empty: 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng — gõ mã, tên hoặc tên nhóm',
    more: 'Thêm mã…',
    search: 'Tìm mã bao bì',
    hint: 'Vd: chai · nắp · nhãn, thùng · NAP0085',
    summary: 'mã bao bì đang dùng cho sản phẩm',
  },
  product: {
    empty: 'Chọn sản phẩm — gõ mã hoặc tên',
    more: 'Thêm sản phẩm…',
    search: 'Tìm mã sản phẩm',
    hint: 'Vd: HH0713 · tên sản phẩm',
    summary: 'sản phẩm có định mức bao bì',
  },
}

/**
 * Ô chọn NHIỀU mã bao bì (chip nằm trong ô, nút x bỏ từng mã, x cuối ô bỏ hết). Gõ TÊN NHÓM ("chai", "nắp", "nhãn, thùng")
 * là lọc cả nhóm để "Chọn tất cả" chọn đúng nhóm đó. Vượt `maxCodes` thì chặn cả lượt và báo, không cắt bớt ngầm.
 */
export default function PackagingCodePicker({
  options, value, onChange, loading, maxCodes = PACKAGING_MAX_CODES, kind = 'material', emptyPlaceholder,
}: {
  /** Danh sách đã xếp sẵn (`sortCodeOptions`). */
  options: PackagingCodeOption[]
  value: string[]
  onChange: (codes: string[]) => void
  loading?: boolean
  maxCodes?: number
  kind?: PackagingPickerKind
  emptyPlaceholder?: string
}) {
  const [open, setOpen] = useState(false)
  const [keyword, setKeyword] = useState('')
  const rootRef = useRef<HTMLDivElement>(null)
  const text = TEXT[kind]
  const material = kind === 'material'

  useEffect(() => {
    if (!open) return
    const onDown = (e: MouseEvent) => { if (!rootRef.current?.contains(e.target as Node)) setOpen(false) }
    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') setOpen(false) }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => { document.removeEventListener('mousedown', onDown); document.removeEventListener('keydown', onKey) }
  }, [open])

  //  Sản phẩm không có "nhóm": để rỗng thì từ khóa luôn rơi về tìm chữ.
  const groups = useMemo(
    () => (material ? collectSearchGroups(options, Object.values(PACKAGING_ROLE_LABELS)) : []),
    [options, material],
  )
  const filtered = useMemo(() => options.filter(buildCodeMatcher(keyword, groups)), [options, keyword, groups])
  const selected = useMemo(() => new Set(value), [value])
  const pickedInView = filtered.filter((o) => selected.has(o.code)).length

  function commit(next: string[]) {
    if (next.length > maxCodes) {
      toast.error(`Chọn tối đa ${maxCodes} mã một lần — đang chọn ${next.length} mã. Thu hẹp bộ lọc rồi chọn lại.`)
      return
    }
    onChange(next)
  }
  const toggle = (code: string) => commit(selected.has(code) ? value.filter((c) => c !== code) : [...value, code])
  const selectAllFiltered = () => commit([...value, ...filtered.map((o) => o.code).filter((c) => !selected.has(c))])
  const clearFiltered = () => {
    const dropped = new Set(filtered.map((o) => o.code))
    onChange(value.filter((c) => !dropped.has(c)))
  }

  return (
    <div className="pkg-picker" ref={rootRef}>
      <div className={'pkg-chipbox' + (open ? ' open' : '')}>
        <i className="ti ti-search" style={{ color: 'var(--muted)', margin: '0 4px' }} />
        {value.slice(0, CHIP_MAX).map((code) => (
          <span key={code} className="pkg-chip">
            {code}
            <button type="button" aria-label={`Bỏ ${code}`} onClick={() => onChange(value.filter((c) => c !== code))}>
              <i className="ti ti-x" />
            </button>
          </span>
        ))}
        {value.length > CHIP_MAX && <span className="pkg-chip-more">+{value.length - CHIP_MAX} mã</span>}
        <button type="button" className="pkg-trigger" disabled={loading} onClick={() => setOpen((v) => !v)}>
          {loading ? 'Đang nạp danh sách mã…' : value.length ? text.more : (emptyPlaceholder ?? text.empty)}
        </button>
        {value.length > 0 && (
          <button type="button" className="pkg-clear" title="Bỏ hết mã đã chọn" aria-label="Bỏ hết mã đã chọn"
            onClick={() => onChange([])}>
            <i className="ti ti-x" />
          </button>
        )}
      </div>

      {open && (
        <div className="pkg-dd">
          <div className="pkg-dd-search">
            <input autoFocus aria-label={text.search} placeholder={text.hint} value={keyword}
              onChange={(e) => setKeyword(e.target.value)} />
          </div>
          <div className="pkg-dd-bar">
            <span className="grow">{filtered.length} {text.summary}</span>
            <button type="button" disabled={!filtered.length} onClick={selectAllFiltered}>
              Chọn tất cả ({filtered.length})
            </button>
            <button type="button" disabled={!pickedInView} onClick={clearFiltered}>
              Bỏ chọn{pickedInView ? ` (${pickedInView})` : ''}
            </button>
          </div>
          <div className="pkg-dd-list" role="listbox" aria-multiselectable="true">
            {filtered.length === 0 && <div className="pkg-dd-empty">Không có mã phù hợp.</div>}
            {filtered.slice(0, LIST_MAX).map((o) => {
              const on = selected.has(o.code)
              return (
                <button key={o.code} type="button" role="option" aria-selected={on}
                  className={'pkg-opt' + (on ? ' on' : '')} onClick={() => toggle(o.code)}>
                  <i className="ti ti-check tick" />
                  <span className="c">{o.code}</span>
                  {material && <span className="g">{o.group}</span>}
                  <span className="n">{o.name}</span>
                  {material && (
                    <span className="u">{o.usage} SP{o.new != null && ` · ${priceText(o.new)}`}</span>
                  )}
                </button>
              )
            })}
            {filtered.length > LIST_MAX && (
              <div className="pkg-dd-empty">Còn {filtered.length - LIST_MAX} mã nữa — gõ để thu hẹp, hoặc bấm Chọn tất cả.</div>
            )}
          </div>
        </div>
      )}
    </div>
  )
}
