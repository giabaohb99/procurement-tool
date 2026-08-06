import { useEffect, useRef } from 'react'
import { MAX_ROWS_DEFAULT } from '../constants'
import { useFilterContext } from '../provider/filter-context'
import FilterRow from './filter-row'

/** Bảng dựng điều kiện — mở ra từ nút "Bộ lọc điều kiện".
 *  Đóng khi bấm ra ngoài hoặc Esc; Ctrl/Cmd+Enter để áp dụng nhanh. */
export default function FilterPopover({ onClose }: { onClose: () => void }) {
  const {
    config, state, addRow, setConjunction, clearAll, apply, dirty, activeCount,
  } = useFilterContext()
  const boxRef = useRef<HTMLDivElement>(null)
  const maxRows = config.maxRows || MAX_ROWS_DEFAULT

  useEffect(() => {
    function onDown(e: MouseEvent) {
      const el = boxRef.current
      if (!el || el.contains(e.target as Node)) return
      // react-select đẩy menu ra document.body qua portal → click chọn option không được coi là "ra ngoài"
      if ((e.target as HTMLElement).closest?.('.rs__menu, .cf-popover')) return
      onClose()
    }
    function onKey(e: KeyboardEvent) {
      if (e.key === 'Escape') onClose()
      if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { apply(); onClose() }
    }
    document.addEventListener('mousedown', onDown)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onDown)
      document.removeEventListener('keydown', onKey)
    }
  }, [onClose, apply])

  return (
    <div className="cf-popover" ref={boxRef}>
      <div className="cf-popover-head">
        <b>Bộ lọc điều kiện</b>
        {config.allowConjunctionToggle && state.rows.length > 1 && (
          <div className="cf-conj-toggle" role="group" aria-label="Cách nối điều kiện">
            {(['and', 'or'] as const).map((c) => (
              <button key={c} type="button" className={state.conjunction === c ? 'on' : ''}
                onClick={() => setConjunction(c)}>
                {c === 'and' ? 'Thỏa TẤT CẢ' : 'Thỏa BẤT KỲ'}
              </button>
            ))}
          </div>
        )}
        <button type="button" className="cf-close" onClick={onClose} title="Đóng">
          <i className="ti ti-x" />
        </button>
      </div>

      <div className="cf-rows">
        {state.rows.length === 0 && (
          <div className="cf-empty">Chưa có điều kiện nào. Bấm "Thêm điều kiện" để bắt đầu.</div>
        )}
        {state.rows.map((row, i) => <FilterRow key={row.id} row={row} index={i} />)}
      </div>

      <div className="cf-popover-foot">
        <button type="button" className="btn ghost" onClick={addRow} disabled={state.rows.length >= maxRows}
          title={state.rows.length >= maxRows ? `Tối đa ${maxRows} điều kiện` : undefined}>
          <i className="ti ti-plus" />Thêm điều kiện
        </button>
        <div className="cf-foot-right">
          {/* Xóa hết = bỏ mọi điều kiện và áp dụng NGAY (không còn chip bên ngoài để gỡ lẻ) */}
          {(state.rows.length > 0 || activeCount > 0) && (
            <button type="button" className="btn ghost" onClick={() => { clearAll(); onClose() }}>
              <i className="ti ti-rotate" />Xóa hết
            </button>
          )}
          <button type="button" className="btn" onClick={() => { apply(); onClose() }} disabled={!dirty}>
            <i className="ti ti-filter" />Áp dụng
          </button>
        </div>
      </div>
    </div>
  )
}
