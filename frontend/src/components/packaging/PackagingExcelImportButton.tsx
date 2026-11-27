import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { api } from '../../api/client'
import { toast } from '../toast'
import { PACKAGING_IMPORT_ENTITY, downloadImportTemplate } from '../../api/packaging-cost'
import PackagingModal from './PackagingModal'

interface Props {
  /** Kiểu nhập (`ImportModule`): 4 định mức · 5 báo giá VTBB · 6 sổ Misa. */
  module: number
  label: string
  title: string
  description: string
  /** Hành động đòi thêm trên khóa quyền của kiểu nhập: định mức + báo giá = 'create', sổ Misa (thay dữ liệu) = 'write'. */
  action: 'create' | 'write'
}

/**
 * Nút nhập Excel của cụm Giá bao bì: tải tệp lên Quản lý Import, LUÔN chạy thử trước, rồi sang trang chi tiết lô
 * để xem nhật ký từng dòng và bấm "Ghi thật". Trong hộp thoại có "Tải tệp mẫu" (đúng cột backend đọc).
 * Hiện khi có ĐỦ `import.create` + `import.read` (trang lô gác `import.read`) + `<khóa của kiểu nhập>.<action>` — backend gác y hệt.
 * bao-CR-792: khóa theo kiểu nhập (`PACKAGING_IMPORT_ENTITY`): định mức → `packaging_bom`, báo giá → `packaging_price_list`,
 * sổ Misa → `packaging_history`.
 */
export default function PackagingExcelImportButton({ module, label, title, description, action }: Props) {
  const { can } = useAuth()
  const navigate = useNavigate()
  const [open, setOpen] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [tplBusy, setTplBusy] = useState(false)
  const [dragOver, setDragOver] = useState(false)
  const inputRef = useRef<HTMLInputElement>(null)
  const sendingRef = useRef(false)      // chặn bấm đúp: state `busy` chỉ cập nhật sau lượt vẽ kế tiếp
  const tplRef = useRef(false)

  const entity = PACKAGING_IMPORT_ENTITY[module]
  if (!(entity && can('import', 'create') && can('import', 'read') && can(entity, action))) return null

  function pick(f: File | null | undefined) {
    if (!f) return
    if (!f.name.toLowerCase().endsWith('.xlsx')) { toast.error('Chỉ nhận tệp .xlsx'); return }
    setFile(f)
  }

  function close() { if (!busy) { setOpen(false); setFile(null) } }

  async function getTemplate() {
    if (tplRef.current) return
    tplRef.current = true
    setTplBusy(true)
    try {
      await downloadImportTemplate(module)
    } catch (e) {
      toast.error((e as Error).message)
    } finally { tplRef.current = false; setTplBusy(false) }
  }

  async function submit() {
    if (!file || sendingRef.current) return
    sendingRef.current = true
    const fd = new FormData()
    fd.append('file', file)
    fd.append('module', String(module))
    fd.append('mode', '0')   // 0 = chạy thử (ImportMode.DRY_RUN)
    setBusy(true)
    try {
      const r = await api.post('/api/imports', fd)
      const id = r.data.data?.id
      toast.success('Đã nhận tệp — đang chạy thử, xem kết quả ở trang lô')
      setOpen(false); setFile(null)
      navigate(id ? `/import-batches/${id}` : '/import-batches')
    } catch { /* interceptor đã hiện thông báo lỗi */ } finally { sendingRef.current = false; setBusy(false) }
  }

  return (
    <>
      <button className="btn outline" aria-label={label} title={title} onClick={() => setOpen(true)}><i className="ti ti-file-import" /><span className="pkg-btn-label">{label}</span></button>
      {open && (
        <PackagingModal title={title} onClose={close} busy={busy} maxWidth={460} subtitle={description}
          footer={<>
            <button className="btn ghost" onClick={close} disabled={busy}>Hủy</button>
            <button className="btn" onClick={submit} disabled={!file || busy}>{busy ? 'Đang gửi…' : 'Chạy thử'}</button>
          </>}>
          <div style={{ marginBottom: 10 }}>
            <button type="button" className="btn ghost" onClick={getTemplate} disabled={tplBusy || busy}>
              <i className="ti ti-download" />{tplBusy ? 'Đang tải…' : 'Tải tệp mẫu'}
            </button>
          </div>
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
