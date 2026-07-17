import { useEffect, useState } from 'react'
import { api } from '../api/client'
import { toast } from './toast'
import FileDropzone from './FileDropzone'
import { fmtSize, fileIcon } from '../utils/file-type'

// Popup upload chứng từ theo LOẠI cho 1 record (đơn mua hàng...).
// Nhiều dòng: mỗi dòng = 1 loại (BẮT BUỘC) + nhiều file (kéo-thả hoặc bấm chọn). Lưu 1 lần.
type DocType = { value: string; label: string }
type Row = { doc_type: string; files: File[] }
type Props = {
  entity: string
  entityId: number
  purchaseOrderId?: number
  onClose: () => void
  onDone: () => void
}

// cache doc-types 1 lần cho cả app
let _docTypesCache: DocType[] | null = null

export default function DocumentUploadModal({ entity, entityId, purchaseOrderId, onClose, onDone }: Props) {
  const [docTypes, setDocTypes] = useState<DocType[]>(_docTypesCache || [])
  const [rows, setRows] = useState<Row[]>([{ doc_type: '', files: [] }])
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (_docTypesCache) return
    api.get('/api/attachments/doc-types')
      .then((r) => { _docTypesCache = r.data.data || []; setDocTypes(_docTypesCache!) })
      .catch(() => {})
  }, [])

  const setRow = (i: number, patch: Partial<Row>) =>
    setRows((rs) => rs.map((r, k) => (k === i ? { ...r, ...patch } : r)))
  const addRow = () => setRows((rs) => [...rs, { doc_type: '', files: [] }])
  const delRow = (i: number) => setRows((rs) => (rs.length === 1 ? rs : rs.filter((_, k) => k !== i)))

  // Gộp file mới vào dòng, chống trùng theo tên+size
  const addFiles = (i: number, list: FileList | null) => {
    if (!list?.length) return
    setRows((rs) => rs.map((r, k) => {
      if (k !== i) return r
      const seen = new Set(r.files.map((f) => f.name + f.size))
      const merged = [...r.files, ...Array.from(list).filter((f) => !seen.has(f.name + f.size))]
      return { ...r, files: merged }
    }))
  }
  const removeFile = (i: number, fi: number) =>
    setRows((rs) => rs.map((r, k) => (k === i ? { ...r, files: r.files.filter((_, x) => x !== fi) } : r)))

  async function submit() {
    // Dòng có file BẮT BUỘC chọn loại; dòng rỗng (không file) → bỏ qua.
    const active = rows.filter((r) => r.files.length)
    if (!active.length) { toast.error('Chưa chọn file nào'); return }
    if (active.some((r) => !r.doc_type)) { toast.error('Mỗi dòng có file phải chọn loại chứng từ'); return }

    setSaving(true)
    try {
      for (const r of active) {
        const fd = new FormData()
        fd.append('entity', entity)
        fd.append('entity_id', String(entityId))
        fd.append('doc_type', r.doc_type)
        if (purchaseOrderId) fd.append('purchase_order_id', String(purchaseOrderId))
        r.files.forEach((f) => fd.append('files', f))
        await api.post('/api/attachments', fd)
      }
      toast.success('Đã tải lên chứng từ')
      onDone()
      onClose()
    } catch {
      // interceptor đã toast lỗi
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{ position: 'fixed', inset: 0, background: 'rgba(15,23,42,.45)', zIndex: 120, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 12 }} onClick={onClose}>
      <div className="modal-card" style={{ width: 640, maxWidth: '96vw', background: '#fff', borderRadius: 12, boxShadow: '0 20px 25px -5px rgba(0,0,0,.15)', display: 'flex', flexDirection: 'column', maxHeight: '90vh', overflow: 'hidden' }} onClick={(e) => e.stopPropagation()}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '14px 18px', borderBottom: '1px solid var(--border)' }}>
          <h3 style={{ margin: 0, fontSize: 16, color: 'var(--navy)' }}><i className="ti ti-upload" /> Upload chứng từ</h3>
          <button className="icon-btn" onClick={onClose}><i className="ti ti-x" style={{ fontSize: 18 }} /></button>
        </div>

        <div style={{ padding: '16px 18px', overflowY: 'auto', flex: 1 }}>
          {rows.map((r, i) => {
            return (
              <div key={i} style={{ display: 'flex', alignItems: 'flex-start', gap: 8, marginBottom: 14, paddingBottom: 14, borderBottom: i < rows.length - 1 ? '1px dashed var(--border)' : 'none' }}>
                <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 8, minWidth: 0 }}>
                  <select value={r.doc_type} onChange={(e) => setRow(i, { doc_type: e.target.value })}
                    style={{ padding: '8px 10px', borderRadius: 8, border: '1px solid var(--border)', fontSize: 13.5 }}>
                    <option value="">-- Chọn loại chứng từ --</option>
                    {docTypes.map((t) => <option key={t.value} value={t.value}>{t.label}</option>)}
                  </select>

                  <FileDropzone hint="PDF, ảnh, Excel, Word…" onFiles={(list) => addFiles(i, list)} />

                  {/* Danh sách file đã chọn */}
                  {r.files.length > 0 && (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {r.files.map((f, fi) => {
                        const ic = fileIcon(f.name, f.type)
                        return (
                        <div key={fi} style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, background: '#f5f7fa', borderRadius: 6, padding: '5px 8px' }}>
                          <i className={'ti ' + ic.icon} style={{ color: ic.color }} />
                          <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f.name}</span>
                          <span style={{ color: 'var(--muted)' }}>{fmtSize(f.size)}</span>
                          <button className="icon-btn" title="Bỏ file" onClick={(e) => { e.stopPropagation(); removeFile(i, fi) }}>
                            <i className="ti ti-x" style={{ fontSize: 14, color: 'var(--red)' }} />
                          </button>
                        </div>
                      )})}
                    </div>
                  )}
                </div>
                <button className="icon-btn" title="Xóa dòng" onClick={() => delRow(i)} disabled={rows.length === 1}>
                  <i className="ti ti-trash" style={{ color: rows.length === 1 ? '#ccc' : 'var(--red)' }} />
                </button>
              </div>
            )
          })}
          <button className="btn ghost" onClick={addRow}><i className="ti ti-plus" /> Thêm loại chứng từ</button>
        </div>

        <div style={{ display: 'flex', justifyContent: 'flex-end', gap: 8, padding: '12px 18px', borderTop: '1px solid var(--border)' }}>
          <button className="btn ghost" onClick={onClose} disabled={saving}>Hủy</button>
          <button className="btn" onClick={submit} disabled={saving}>{saving ? 'Đang lưu…' : 'Lưu chứng từ'}</button>
        </div>
      </div>
    </div>
  )
}
