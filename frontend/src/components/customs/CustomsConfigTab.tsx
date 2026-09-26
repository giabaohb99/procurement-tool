// bao-CR-502 — thẻ «Cấu hình» của màn Tra cứu thị trường (bản cũ), bê từ bao-CR-501 bản v2.
// Ba danh mục nằm NGAY trong màn tra cứu, không màn / mục menu riêng (đại ca chốt 26/09:
// chức năng này càng ít màn hình càng tốt): từ khóa nhãn Thành phẩm / Nguyên liệu (bao-CR-494),
// từ đồng nghĩa tìm kiếm (bao-CR-495), danh mục hóa chất theo văn bản (bao-CR-470).
//
// Ô tìm, lọc nhanh, số trang là state cục bộ của từng khối (không đụng bộ lọc dòng hàng của màn).
// Bấm một dòng mở hộp Sửa; người thiếu quyền sửa mở ra chỉ đọc, không có nút Lưu / Xóa.
import { useCallback, useEffect, useState } from 'react'
import { api } from '../../api/client'
import { useAuth } from '../../auth/AuthContext'
import { cruds, type Column, type FieldDef } from '../../config/cruds'
import { askConfirm } from '../confirm'
import Pagination from '../Pagination'
import SearchSelect from '../SearchSelect'
import TableScroll from '../TableScroll'
import { toast } from '../toast'
import CustomsModal from './CustomsModal'

type QuickFilter = { key: string; label: string; options: { value: string; label: string }[] }

type Catalog = {
  title: string
  description: string
  entity: string
  apiPath: string
  unitLabel: string
  searchParam: string
  searchPlaceholder: string
  quickFilters: QuickFilter[]
  columns: Column[]
  fields: FieldDef[]
  itemName: (row: any) => string
  deleteWarning: string
  retag?: boolean
}

const ACTIVE_OPTIONS = [
  { value: 'true', label: 'Đang dùng' },
  { value: 'false', label: 'Ngừng dùng' },
]
// Khớp `ProductKind` backend (customs/constants.py): 1 Thành phẩm · 2 Nguyên liệu.
const KIND_OPTIONS = [
  { value: '2', label: 'Nguyên liệu (TC/TECH/TG)' },
  { value: '1', label: 'Thành phẩm' },
]
const kindLabel = (v: any) => (String(v) === '2' ? 'Nguyên liệu' : String(v) === '1' ? 'Thành phẩm' : '')
const activeBadge = (v: any) => (
  <span className={`badge ${v ? 'ok' : 'gray'}`}>{v ? 'Đang dùng' : 'Ngừng'}</span>
)

const KIND_KEYWORDS: Catalog = {
  title: 'Từ khóa Thành phẩm / Nguyên liệu',
  description: 'Bộ từ khóa để màn Tra cứu thị trường tự gắn nhãn từng dòng hàng. Tên hàng chứa từ khóa loại «Nguyên liệu» thì là nguyên liệu kỹ thuật, còn lại là thành phẩm. Sửa xong bấm «Gắn lại nhãn».',
  entity: 'customs_price',
  apiPath: '/api/customs-kind-keywords',
  unitLabel: 'từ khóa',
  searchParam: 'keyword',
  searchPlaceholder: 'Tìm từ khóa…',
  quickFilters: [
    { key: 'kind', label: 'Loại', options: KIND_OPTIONS.map((o) => ({ value: o.value, label: kindLabel(o.value) })) },
    { key: 'is_active', label: 'Trạng thái', options: ACTIVE_OPTIONS },
  ],
  columns: [
    { key: 'keyword', label: 'Từ khóa', render: (r) => <b>{r.keyword}</b> },
    { key: 'kind', label: 'Gắn nhãn', render: (r) => <span className="badge info">{kindLabel(r.kind)}</span> },
    { key: 'note', label: 'Ghi chú' },
    { key: 'is_active', label: 'Trạng thái', render: (r) => activeBadge(r.is_active) },
  ],
  fields: [
    { key: 'keyword', label: 'Từ khóa', fullWidth: true,
      hint: 'Không phân biệt hoa/thường. Từ ngắn (TC, TG…) chỉ khớp khi đứng thành một từ — «TC» không dính «ATC». Từ dài khớp cả khi nằm trong chuỗi («kỹ thuật» khớp «Thuốc kỹ thuật ATRAZINE»).' },
    { key: 'kind', label: 'Gắn nhãn', type: 'select', options: KIND_OPTIONS, default: '2',
      hint: 'Thường là «Nguyên liệu». Chọn «Thành phẩm» cho từ khóa NGOẠI LỆ muốn thắng ngược (vd tên chứa TECHNOLOGY nhưng vẫn là thành phẩm).' },
    { key: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
    { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, default: 'true',
      hint: 'Ngừng dùng thì lần gắn lại nhãn tới không còn xét từ khóa này.' },
  ],
  itemName: (r) => r.keyword,
  deleteWarning: 'Xóa từ khóa thì các dòng đang mang nhãn nhờ nó KHÔNG tự đổi — bấm «Gắn lại nhãn» sau khi xóa. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
  retag: true,
}

const SEARCH_SYNONYMS: Catalog = {
  title: 'Từ đồng nghĩa tìm kiếm',
  description: 'Các cách viết tương đương của cùng một hoạt chất / tên hàng. Ô tìm trên màn Tra cứu thị trường gõ từ nào trong nhóm cũng ra kết quả của cả nhóm. Nồng độ (3,6% · 3.6EC · 36 G/L) hệ tự quy đổi, không cần khai.',
  entity: 'customs_price',
  apiPath: '/api/customs-search-synonyms',
  unitLabel: 'nhóm từ',
  searchParam: 'term',
  searchPlaceholder: 'Tìm từ gốc…',
  quickFilters: [{ key: 'is_active', label: 'Trạng thái', options: ACTIVE_OPTIONS }],
  columns: [
    { key: 'term', label: 'Từ gốc', render: (r) => <b>{r.term}</b> },
    { key: 'synonyms', label: 'Từ đồng nghĩa', render: (r) => (
      <span style={{ display: 'flex', flexWrap: 'wrap', gap: 4 }}>
        {String(r.synonyms || '').split(';').map((s) => s.trim()).filter(Boolean)
          .map((s) => <span key={s} className="badge gray">{s}</span>)}
      </span>) },
    { key: 'note', label: 'Ghi chú' },
    { key: 'is_active', label: 'Trạng thái', render: (r) => activeBadge(r.is_active) },
  ],
  fields: [
    { key: 'term', label: 'Từ gốc', fullWidth: true, hint: 'Cách viết chính, vd «Abamectin».' },
    { key: 'synonyms', label: 'Từ đồng nghĩa', type: 'textarea', fullWidth: true,
      hint: 'Mỗi cách viết một dòng hoặc ngăn bằng «;», vd «Abamectine; Aba». Không phân biệt hoa/thường.' },
    { key: 'note', label: 'Ghi chú', type: 'textarea', fullWidth: true },
    { key: 'is_active', label: 'Trạng thái', type: 'select', options: ACTIVE_OPTIONS, default: 'true' },
  ],
  itemName: (r) => r.term,
  deleteWarning: 'Xóa nhóm thì gõ các từ trong nhóm không còn ra nhau nữa. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
}

// Danh mục hóa chất dùng lại NGUYÊN cột + ô nhập của màn CRUD cũ (config/cruds.tsx), khỏi chép hai nơi.
const REGULATION_CFG = cruds['customs-regulations']
const REGULATIONS: Catalog = {
  title: REGULATION_CFG.title,
  description: 'Hóa chất trong NĐ 24/2026, TT 75/2025, TT 01/2026 — nguồn của cảnh báo pháp lý trên màn Tra cứu thị trường.',
  entity: REGULATION_CFG.entity,
  apiPath: REGULATION_CFG.apiPath,
  unitLabel: 'hóa chất',
  searchParam: 'name',
  searchPlaceholder: 'Tìm theo tên hóa chất…',
  quickFilters: REGULATION_CFG.filters
    .filter((f: any) => f.type === 'select' && f.options)
    .map((f: any) => ({ key: f.key, label: f.label, options: f.options })),
  columns: REGULATION_CFG.columns.filter((c) => c.key !== 'updated_at'),
  fields: REGULATION_CFG.fields,
  itemName: (r) => r.name,
  deleteWarning: 'Xóa khỏi danh mục thì màn Tra cứu thị trường thôi cảnh báo cho hóa chất này. Muốn tạm tắt thì chuyển sang «Ngừng dùng».',
}

export default function CustomsConfigTab({ canConfigure, canReadRegulations }: {
  canConfigure: boolean
  canReadRegulations: boolean
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {canConfigure && <CatalogCard catalog={KIND_KEYWORDS} />}
      {canConfigure && <CatalogCard catalog={SEARCH_SYNONYMS} />}
      {canReadRegulations && <CatalogCard catalog={REGULATIONS} />}
    </div>
  )
}

function CatalogCard({ catalog }: { catalog: Catalog }) {
  const { can } = useAuth()
  const [keyword, setKeyword] = useState('')
  const [applied, setApplied] = useState('')
  const [quick, setQuick] = useState<Record<string, string>>({})
  const [page, setPage] = useState(1)
  const [pageSize, setPageSize] = useState(10)
  const [rows, setRows] = useState<any[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(false)
  // undefined = đóng · null = THÊM mới · bản ghi = SỬA
  const [editing, setEditing] = useState<any | null | undefined>(undefined)
  const [retagging, setRetagging] = useState(false)

  // Gõ xong ngưng 350ms mới tìm, cùng nhịp ô tìm của bản v2.
  useEffect(() => {
    const t = setTimeout(() => { setApplied(keyword.trim()); setPage(1) }, 350)
    return () => clearTimeout(t)
  }, [keyword])

  const load = useCallback(() => {
    const params: Record<string, any> = { page, page_size: pageSize }
    if (applied) params[catalog.searchParam] = applied
    for (const [k, v] of Object.entries(quick)) if (v) params[k] = v
    setLoading(true)
    api.get(catalog.apiPath, { params })
      .then((r) => { setRows(r.data.data.items); setTotal(r.data.data.total) })
      .finally(() => setLoading(false))
  }, [catalog, applied, quick, page, pageSize])
  useEffect(() => { load() }, [load])

  async function retag() {
    if (retagging) return
    setRetagging(true)
    try {
      const r = await api.post('/api/customs/kinds/retag')
      const d = r.data.data
      toast.success(`Đã gắn lại ${Number(d.total).toLocaleString('vi-VN')} dòng — ${Number(d.technical).toLocaleString('vi-VN')} nguyên liệu, ${(d.total - d.technical).toLocaleString('vi-VN')} thành phẩm`)
    } finally {
      setRetagging(false)
    }
  }

  const filtering = !!applied || Object.values(quick).some(Boolean)

  return (
    <div className="card" style={{ padding: 16 }}>
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8, flexWrap: 'wrap', marginBottom: 10 }}>
        <div style={{ flex: 1, minWidth: 240 }}>
          <h3 style={{ margin: 0, fontSize: 15, color: 'var(--navy)' }}>{catalog.title}</h3>
          <div style={{ fontSize: 13, color: 'var(--muted)', marginTop: 4 }}>{catalog.description}</div>
        </div>
        {catalog.retag && can(catalog.entity, 'write') && (
          <button className="btn ghost" disabled={retagging} onClick={retag}
            title="Áp bộ từ khóa hiện tại lên MỌI dòng hàng đã nạp — chạy sau khi thêm/sửa từ khóa">
            <i className="ti ti-refresh" />{retagging ? 'Đang gắn…' : 'Gắn lại nhãn'}
          </button>
        )}
        {can(catalog.entity, 'create') && (
          <button className="btn" onClick={() => setEditing(null)}><i className="ti ti-plus" />Thêm {catalog.unitLabel}</button>
        )}
      </div>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 8 }}>
        <input value={keyword} onChange={(e) => setKeyword(e.target.value)} placeholder={catalog.searchPlaceholder}
          style={{ width: 260 }} />
        {catalog.quickFilters.map((qf) => (
          <div key={qf.key} style={{ width: 200 }}>
            <SearchSelect value={quick[qf.key] || ''} placeholder={`Tất cả ${qf.label.toLowerCase()}`}
              autoSelectSingle={false} options={qf.options}
              onChange={(v) => { setQuick((s) => ({ ...s, [qf.key]: v })); setPage(1) }} />
          </div>
        ))}
        <button className="btn ghost" onClick={load} title="Tải lại"><i className="ti ti-refresh" /></button>
      </div>

      <TableScroll>
        <table>
          <thead>
            <tr>{catalog.columns.map((c) => <th key={c.key}>{c.label}</th>)}</tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.id} className="clickable" onClick={() => setEditing(r)}>
                {catalog.columns.map((c) => <td key={c.key} style={{ whiteSpace: 'normal' }}>{c.render ? c.render(r) : r[c.key]}</td>)}
              </tr>
            ))}
            {!loading && rows.length === 0 && (
              <tr><td colSpan={catalog.columns.length} className="table-empty">
                {filtering ? `Không có ${catalog.unitLabel} nào khớp bộ lọc.` : `Chưa có ${catalog.unitLabel} nào.`}
              </td></tr>
            )}
          </tbody>
        </table>
      </TableScroll>
      <div className="table-foot">
        <Pagination page={page} pageSize={pageSize} total={total} onChange={(p, s) => { setPage(p); setPageSize(s) }} />
      </div>

      {editing !== undefined && (
        <CatalogForm catalog={catalog} item={editing} onClose={() => setEditing(undefined)}
          onSaved={() => { setEditing(undefined); load() }} />
      )}
    </div>
  )
}

/** Giá trị từ API → chuỗi cho ô nhập (ô chọn so khớp bằng chuỗi: true → 'true', 2 → '2'). */
function toFormValue(f: FieldDef, v: any) {
  if (v === null || v === undefined) return ''
  if (f.type === 'number') return f.zeroAsBlank && v === 0 ? '' : String(v)
  if (f.type === 'checkbox') return !!v
  return String(v)
}

/**
 * Chuỗi của form → giá trị gửi API. Ô số để trống gửi `null` — `banned_year` đòi ≥ 1900 nên 0 bị
 * từ chối (422); riêng bản ghi vốn lưu 0 thì trả lại 0 cho khỏi đổi dữ liệu người khác không sửa.
 */
function toPayload(fields: FieldDef[], form: Record<string, any>, original: any | null) {
  const out: Record<string, any> = {}
  for (const f of fields) {
    const v = form[f.key]
    if (f.type === 'number') out[f.key] = v === '' || v == null ? (original?.[f.key] === 0 ? 0 : null) : Number(v)
    else if (f.type === 'select' && (v === 'true' || v === 'false')) out[f.key] = v === 'true'
    else if (f.type === 'select' && v !== '' && /^-?\d+$/.test(String(v))) out[f.key] = Number(v)
    else out[f.key] = v ?? ''
  }
  return out
}

function CatalogForm({ catalog, item, onClose, onSaved }: {
  catalog: Catalog
  item: any | null
  onClose: () => void
  onSaved: () => void
}) {
  const { can } = useAuth()
  const isNew = item === null
  const canSave = can(catalog.entity, isNew ? 'create' : 'write')
  const canDelete = !isNew && can(catalog.entity, 'delete')
  const [form, setForm] = useState<Record<string, any>>(() => {
    const init: Record<string, any> = {}
    for (const f of catalog.fields) init[f.key] = isNew ? toFormValue(f, f.default ?? '') : toFormValue(f, item[f.key])
    return init
  })
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  const set = (k: string, v: any) => setForm((s) => ({ ...s, [k]: v }))

  async function save() {
    if (busy) return
    setBusy(true); setErr('')
    try {
      const payload = toPayload(catalog.fields, form, item)
      if (isNew) await api.post(catalog.apiPath, payload)
      else await api.patch(`${catalog.apiPath}/${item.id}`, payload)
      toast.success(isNew ? `Đã thêm ${catalog.unitLabel}` : 'Đã lưu')
      onSaved()
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Lỗi khi lưu')
    } finally {
      setBusy(false)
    }
  }

  async function remove() {
    const ok = await askConfirm({
      title: `Xóa ${catalog.unitLabel}`,
      message: `Xóa «${catalog.itemName(item)}»? ${catalog.deleteWarning}`,
      confirmText: 'Xóa',
    })
    if (!ok) return
    try {
      await api.delete(`${catalog.apiPath}/${item.id}`)
      toast.success(`Đã xóa ${catalog.unitLabel}`)
      onSaved()
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Lỗi khi xóa')
    }
  }

  const title = isNew ? `Thêm ${catalog.unitLabel}` : canSave ? `Sửa ${catalog.unitLabel}` : `Xem ${catalog.unitLabel}`
  let lastGroup = ''
  return (
    <CustomsModal title={title} width={760} onClose={onClose} footer={
      <>
        {canDelete && (
          <button className="btn ghost" type="button" style={{ marginRight: 'auto', color: '#b91c1c' }} onClick={remove}>
            <i className="ti ti-trash" />Xóa
          </button>
        )}
        <button className="btn ghost" type="button" onClick={onClose}>{canSave ? 'Hủy' : 'Đóng'}</button>
        {canSave && (
          <button className="btn" type="button" disabled={busy} onClick={save}><i className="ti ti-device-floppy" />Lưu</button>
        )}
      </>
    }>
      <div className="form-grid">
        {catalog.fields.map((f) => {
          const newGroup = f.group && f.group !== lastGroup ? f.group : ''
          if (f.group) lastGroup = f.group
          return (
            <div key={f.key} style={{ display: 'contents' }}>
              {newGroup && <div className="form-group-title">{newGroup}</div>}
              <div className={'form-row' + (f.fullWidth ? ' full' : '')}>
                <label>{f.label}</label>
                {f.type === 'textarea' ? (
                  <textarea value={form[f.key]} disabled={!canSave} onChange={(e) => set(f.key, e.target.value)} />
                ) : f.type === 'select' ? (
                  <SearchSelect value={form[f.key]} disabled={!canSave} placeholder="Chọn…" autoSelectSingle={false}
                    colorMap={f.colorMap} options={f.options || []} onChange={(v) => set(f.key, v)} />
                ) : (
                  <input type={f.type === 'number' ? 'number' : 'text'} value={form[f.key]} disabled={!canSave}
                    onChange={(e) => set(f.key, e.target.value)} />
                )}
                {f.hint && <div style={{ fontSize: 12, color: 'var(--muted)', marginTop: 4, fontWeight: 'normal' }}>{f.hint}</div>}
              </div>
            </div>
          )
        })}
      </div>
      {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
    </CustomsModal>
  )
}
