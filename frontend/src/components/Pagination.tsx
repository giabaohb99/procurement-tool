export default function Pagination({
  page, pageSize, total, onChange,
}: {
  page: number
  pageSize: number
  total: number
  onChange: (page: number, pageSize: number) => void
}) {
  const pages = Math.max(1, Math.ceil(total / pageSize))
  const from = total === 0 ? 0 : (page - 1) * pageSize + 1
  const to = Math.min(page * pageSize, total)

  return (
    <div className="pager">
      <span>Hiển thị {from}–{to} / {total}</span>
      <span style={{ flex: 1 }} />
      <select value={pageSize} onChange={(e) => onChange(1, Number(e.target.value))}>
        {[10, 20, 50, 100].map((s) => <option key={s} value={s}>{s}/trang</option>)}
      </select>
      <button className="btn ghost" disabled={page <= 1} onClick={() => onChange(page - 1, pageSize)}>
        <i className="ti ti-chevron-left" />
      </button>
      <span>Trang {page}/{pages}</span>
      <button className="btn ghost" disabled={page >= pages} onClick={() => onChange(page + 1, pageSize)}>
        <i className="ti ti-chevron-right" />
      </button>
    </div>
  )
}
