import { useMemo, useRef, useState, type KeyboardEvent } from 'react'
import { fetchCodeOptions, fetchFgOptions } from '../../api/packaging-cost'
import './packaging.css'

/**
 * duoc-CR-784 — ô tìm CÓ GỢI Ý của thanh lọc chip (Tổng hợp theo sản phẩm, bảng sản phẩm của Tác động giá; 27/11/2026),
 * cùng hành vi bản `frontend-v2`: gõ chữ vẫn lọc như cũ, đồng thời sổ ra gợi ý SẢN PHẨM (mã HH + tên) và MÃ THÀNH PHẦN
 * (mã VTBB + tên), mỗi loại tối đa 6 dòng; bấm / Enter một dòng = điền đúng mã đó vào ô. Hai danh sách nạp MỘT lần cho cả
 * phiên (lần đầu bấm vào ô), lọc tại trình duyệt, không dấu, mọi từ phải có mặt trong mã hoặc tên.
 */

const SUGGEST_MAX = 6

interface Suggestion { kind: 'product' | 'component'; code: string; name: string }
type Item = { code: string; name: string }

const fold = (s: string) =>
  s.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase().trim()

//  Nạp một lần cho cả phiên: hai màn dùng chung, mở / đóng ô nhiều lần không gọi lại.
let cache: Promise<{ products: Item[]; components: Item[] }> | null = null
function loadSuggestionSources() {
  cache ??= Promise.all([fetchFgOptions(), fetchCodeOptions()])
    .then(([products, components]) => ({ products, components }))
    .catch(() => { cache = null; return { products: [], components: [] } })
  return cache
}

export function pickSuggestions(keyword: string, products: readonly Item[], components: readonly Item[]): Suggestion[] {
  const terms = fold(keyword).split(/\s+/).filter(Boolean)
  if (terms.length === 0) return []
  const match = (it: Item) => { const hay = fold(`${it.code} ${it.name}`); return terms.every((t) => hay.includes(t)) }
  const take = (items: readonly Item[], kind: Suggestion['kind']) =>
    items.filter(match).slice(0, SUGGEST_MAX).map((it) => ({ kind, code: it.code, name: it.name }))
  return [...take(products, 'product'), ...take(components, 'component')]
}

export default function PackagingKeywordSuggestInput({ value, onChange }: { value: string; onChange: (v: string) => void }) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(-1)
  const [sources, setSources] = useState<{ products: Item[]; components: Item[] }>({ products: [], components: [] })
  const loaded = useRef(false)
  const suggestions = useMemo(() => pickSuggestions(value, sources.products, sources.components), [value, sources])
  const showList = open && suggestions.length > 0

  const ensureLoaded = () => {
    if (loaded.current) return
    loaded.current = true
    loadSuggestionSources().then(setSources)
  }
  const choose = (it: Suggestion) => { onChange(it.code); setOpen(false); setActive(-1) }
  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (!showList) return
    if (e.key === 'ArrowDown') { e.preventDefault(); setActive((i) => Math.min(i + 1, suggestions.length - 1)) }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setActive((i) => Math.max(i - 1, -1)) }
    else if (e.key === 'Enter' && active >= 0) { e.preventDefault(); choose(suggestions[active]) }
    else if (e.key === 'Escape') setOpen(false)
  }

  return (
    <div className="pkg-search pkg-suggest">
      <input aria-label="Tìm sản phẩm" placeholder="Tìm mã HH, tên, mã thành phần…" value={value} autoComplete="off"
        //  KHÔNG gắn role="combobox": `index.css` gỡ hết khung / nền của mọi `input[role="combobox"]` (chữa ô tìm của react-select).
        aria-autocomplete="list"
        onFocus={() => { ensureLoaded(); setOpen(true) }} onBlur={() => setOpen(false)}
        onChange={(e) => { onChange(e.target.value); setActive(-1); setOpen(true) }} onKeyDown={onKeyDown} />
      {showList && (
        <ul className="pkg-suggest-list" role="listbox" aria-label="Gợi ý">
          {suggestions.map((it, i) => (
            //  `onMouseDown` + preventDefault: chọn trước khi ô gõ mất tiêu điểm (blur đóng danh sách).
            <li key={`${it.kind}-${it.code}`} role="option" aria-selected={i === active}
              className={'pkg-suggest-item' + (i === active ? ' on' : '')}
              onMouseDown={(e) => { e.preventDefault(); choose(it) }} onMouseEnter={() => setActive(i)}>
              <span className="pkg-suggest-code">{it.code}</span>
              <span className="pkg-suggest-name" title={it.name}>{it.name}</span>
              <span className="pkg-suggest-kind">{it.kind === 'product' ? 'Sản phẩm' : 'Thành phần'}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
