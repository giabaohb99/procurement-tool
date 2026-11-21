import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { api } from '../../api/client'
import { toast } from '../toast'
import { IMPORT_MODULE_PACKAGING_BOM } from '../../api/packaging-cost'
import PackagingModal from './PackagingModal'

/**
 * Nút "Nhập từ Excel" của màn Định mức bao bì: tải `DATA_CHAI.xlsx` lên Quản lý Import (module Định mức bao bì),
 * LUÔN chạy thử trước, rồi sang trang chi tiết lô để xem nhật ký từng dòng và bấm "Ghi thật".
 * Hiện khi có ĐỦ `import.create` + `import.read` (trang lô gác `import.read`) + `packaging_cost.create` — backend gác y hệt.
 */
export default function PackagingBomImportButton() {
  const { can } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)

  if (!(can('import', 'create') && can('import', 'read') && can('packaging_cost', 'create'))) return null

  function pick(f: File | null | undefined) {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.xlsx')) { toast.error('Chỉ nhận tệp .xlsx'); return }
    setFile(f)
  }

  function close() { if (!busy) { setOpen(false); setFile(null) } }

  async function submit() {
    if (!file || busy) return
    const fd = new FormData()
    fd.append('file', file)
    fd.append('module', String(IMPORT_MODULE_PACKAGING_BOM))
    fd.append('mode', '0')   // 0 = chạy thử (ImportMode.DRY_RUN)
    setBusy(true)
    try {
      const r = await api.post('/api/imports', fd)
      const id = r.data.data?.id
      toast.success('Đã nhận tệp — đang chạy thử, xem kết quả ở trang lô')
      setOpen(false); setFile(null)
      navigate(id ? `/import-batches/${id}` : '/import-batches')
    } catch { /* interceptor đã hiện thông báo lỗi */ } finally { setBusy(false) }
  }

  return (
    <>
      <button className="btn outline" onClick={() => setOpen(true)}><i className="ti ti-file-import" />Nhập từ Excel</button>
      {open && (
        <PackagingModal title="Nhập định mức bao bì" onClose={close} busy={busy} maxWidth={460}
          subtitle="Tệp DATA_CHAI.xlsx (sheet MAP_SP, hoặc data + DATA CHUNG). Hệ thống chạy thử trước — xem nhật ký từng dòng ở trang lô rồi mới bấm Ghi thật. Mã HH đã có thì cập nhật, chưa có thì tạo; dòng không có trong tệp giữ nguyên."
          footer={<>
            <button className="btn ghost" onClick={close} disabled={busy}>Hủy</button>
            <button className="btn" onClick={submit} disabled={!file || busy}>{busy ? 'Đang gửi…' : 'Chạy thử'}</button>
          </>}>
          <div className={'pkg-drop' + (file ? ' has' : '')} style={dragOver ? { borderColor: 'var(--teal)' } : undefined}
            onDragOver={(e) => { e.preventDefault(); setDragOver(true) }}
            onDragLeave={() => setDragOver(false)}
            onDrop={(e) => { e.preventDefault(); setDragOver(false); pick(e.dataTransfer.files[0]) }}
            onClick={() => inputRef.current?.click()}>
            <input ref={inputRef} type="file" accept=".xlsx" style={{ display: 'none' }} onChange={(e) => pick(e.target.files?.[0])} />
            {file ? <><i className="ti ti-file-spreadsheet" /> {file.name}</> : 'Bấm để chọn hoặc kéo thả tệp .xlsx vào đây'}
          </div>
        </PackagingModal>
      )}
    </>
  )
}
