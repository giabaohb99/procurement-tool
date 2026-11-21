import { useEffect, useId, useMemo, useRef, useState } from 'react'
import type { KeyboardEvent, MouseEvent } from 'react'
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

const TEXT: Record<PackagingPickerKind, { empty: string; more: string; aria: string; summary: string }> = {
  material: {
    empty: 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng — gõ mã, tên hoặc tên nhóm',
    more: 'Thêm mã… (vd: chai · nắp · nhãn, thùng · NAP0085)',
    aria: 'Chọn mã chai / nắp / nhãn / nhãn thùng / thùng',
    summary: 'mã bao bì đang dùng cho sản phẩm',
  },
  product: {
    empty: 'Chọn sản phẩm — gõ mã hoặc tên',
    more: 'Thêm sản phẩm… (vd: HH0713 · tên sản phẩm)',
    aria: 'Chọn mã sản phẩm',
    summary: 'sản phẩm có định mức bao bì',
  },
}

/**
 * Ô chọn NHIỀU mã bao bì: cả khung là một combobox (chip + ô gõ chung một hàng, không còn ô tìm thứ hai trong danh sách;
 * người chủ chốt 21/11/2026, đúng bản mẫu HTML). Nút x bỏ từng mã, x cuối ô bỏ hết. Gõ TÊN NHÓM ("chai", "nắp", "nhãn, thùng")
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
  //  -1 = chưa tô dòng nào (Enter khi đó theo luật bản mẫu: mã gõ đúng / còn đúng một kết quả).
  const [active, setActive] = useState(-1)
  const rootRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)
  const listId = useId()
  const text = TEXT[kind]
  const material = kind === 'material'

  const closeList = () => { setOpen(false); setKeyword(''); setActive(-1) }

  //  Bấm ra ngoài khung thì đóng (bấm trong khung / danh sách thì tiêu điểm vẫn ở ô gõ).
  useEffect(() => {
    if (!open) return
    const onDown = (e: globalThis.MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) { setOpen(false); setKeyword(''); setActive(-1) }
    }
    document.addEventListener('mousedown', onDown)
    return () => document.removeEventListener('mousedown', onDown)
  }, [open])

  //  Sản phẩm không có "nhóm": để rỗng thì từ khóa luôn rơi về tìm chữ.
  const groups = useMemo(
    () => (material ? collectSearchGroups(options, Object.values(PACKAGING_ROLE_LABELS)) : []),
    [options, material],
  )
  const filtered = useMemo(() => options.filter(buildCodeMatcher(keyword, groups)), [options, keyword, groups])
  const visible = useMemo(() => filtered.slice(0, LIST_MAX), [filtered])
  const selected = useMemo(() => new Set(value), [value])
  const pickedInView = filtered.filter((o) => selected.has(o.code)).length
  const activeOption = open && active >= 0 ? visible[active] : undefined
  const optId = (code: string) => `${listId}-opt-${code}`

  //  Dòng đang tô luôn nằm trong khung nhìn khi bấm mũi tên (tiêu điểm không rời ô gõ).
  useEffect(() => {
    if (activeOption) document.getElementById(optId(activeOption.code))?.scrollIntoView?.({ block: 'nearest' })
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeOption])

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

  function onKeyDown(e: KeyboardEvent<HTMLInputElement>) {
    //  Đang gõ dấu tiếng Việt (Telex / VNI): Enter / mũi tên thuộc về bộ gõ.
    if (e.nativeEvent.isComposing) return
    if (e.key === 'ArrowDown' || e.key === 'ArrowUp') {
      e.preventDefault()
      if (!open) { setOpen(true); return }
      if (!visible.length) return
      const step = e.key === 'ArrowDown' ? 1 : -1
      setActive((cur) => (cur < 0 ? (step === 1 ? 0 : visible.length - 1) : (cur + step + visible.length) % visible.length))
    } else if (e.key === 'Enter') {
      //  Luôn chặn: ô có thể nằm trong <form>, Enter không được gửi form cha.
      e.preventDefault()
      if (!open) { setOpen(true); return }
      //  Có dòng đang tô thì bật / tắt dòng đó; không thì như bản mẫu: gõ đúng một mã, hoặc bộ lọc còn đúng một mã thì thêm.
      if (activeOption) {
        toggle(activeOption.code)
      } else {
        const typed = keyword.trim().split(/\s+/)[0]?.toUpperCase() ?? ''
        const hit = options.find((o) => o.code.toUpperCase() === typed) ?? (filtered.length === 1 ? filtered[0] : undefined)
        if (!hit) return
        if (!selected.has(hit.code)) commit([...value, hit.code])
      }
      setKeyword('')
      setActive(-1)
    } else if (e.key === 'Escape') {
      if (open) { e.preventDefault(); closeList(); inputRef.current?.blur() }
    } else if (e.key === 'Tab') {
      closeList()
    } else if (e.key === 'Backspace' && !keyword && value.length > 0) {
      onChange(value.slice(0, -1))
    }
  }

  /** Bấm khoảng trống của khung (không phải chip / nút) thì đưa tiêu điểm về ô gõ. */
  function onBoxMouseDown(e: MouseEvent<HTMLDivElement>) {
    const t = e.target as HTMLElement
    if (t === inputRef.current || t.closest('button')) return
    e.preventDefault()
    inputRef.current?.focus()
    if (!loading) setOpen(true)
  }

  return (
    <div className="pkg-picker" ref={rootRef}>
      <div className={'pkg-chipbox' + (open ? ' open' : '')} onMouseDown={onBoxMouseDown}>
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
        <input
          ref={inputRef} type="text" role="combobox" className="pkg-input" autoComplete="off"
          aria-label={text.aria} aria-expanded={open} aria-controls={open ? listId : undefined}
          aria-autocomplete="list" aria-activedescendant={activeOption ? optId(activeOption.code) : undefined}
          disabled={loading} value={keyword}
          placeholder={loading ? 'Đang nạp danh sách mã…' : value.length ? text.more : (emptyPlaceholder ?? text.empty)}
          onChange={(e) => { setKeyword(e.target.value); setActive(-1); setOpen(true) }}
          onFocus={() => setOpen(true)} onClick={() => setOpen(true)} onKeyDown={onKeyDown}
        />
        {value.length > 0 && (
          <button type="button" className="pkg-clear" title="Bỏ hết mã đã chọn" aria-label="Bỏ hết mã đã chọn"
            onClick={() => onChange([])}>
            <i className="ti ti-x" />
          </button>
        )}
      </div>

      {open && (
        //  Bấm trong danh sách (kể cả Chọn tất cả) không cướp tiêu điểm của ô gõ.
        <div className="pkg-dd" onMouseDown={(e) => e.preventDefault()}>
          <div className="pkg-dd-bar">
            <span className="grow">{filtered.length} {text.summary}</span>
            <button type="button" disabled={!filtered.length} onClick={selectAllFiltered}>
              Chọn tất cả ({filtered.length})
            </button>
            <button type="button" disabled={!pickedInView} onClick={clearFiltered}>
              Bỏ chọn{pickedInView ? ` (${pickedInView})` : ''}
            </button>
          </div>
          <div id={listId} className="pkg-dd-list" role="listbox" aria-label={text.aria} aria-multiselectable="true">
            {filtered.length === 0 && <div className="pkg-dd-empty">Không có mã phù hợp.</div>}
            {visible.map((o, i) => {
              const on = selected.has(o.code)
              return (
                <div key={o.code} id={optId(o.code)} role="option" aria-selected={on}
                  className={'pkg-opt' + (on ? ' on' : '') + (i === active ? ' active' : '')}
                  onClick={() => toggle(o.code)} onMouseMove={() => active !== i && setActive(i)}>
                  <i className="ti ti-check tick" />
                  <span className="c">{o.code}</span>
                  {material && <span className="g">{o.group}</span>}
                  <span className="n">{o.name}</span>
                  {material && (
                    <span className="u">{o.usage} SP{o.new != null && ` · ${priceText(o.new)}`}</span>
                  )}
                </div>
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
