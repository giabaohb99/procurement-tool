// duoc-CR-490 — nạp lại danh mục thuốc BVTV từ tệp bản cào danhmuc.thuocbvtv.com
// (thuoc-bvtv.json / .xlsx). THAY TOÀN BỘ thuốc LẤY TỪ NGUỒN — thuốc tự thêm trên màn
// (`is_manual`) được GIỮ NGUYÊN. Hộp nói rõ số thuốc sắp bị thay trước khi cho bấm.
//
// Nút Nạp chặn bấm đúp bằng `useRef` ngay trong lượt bấm (`disabled` chỉ đổi ở lượt vẽ sau).
// Đang nạp thì KHÔNG cho đóng hộp: đóng là mất cờ chặn, mở lại bấm tiếp là hai lượt thay toàn
// bộ chạy song song (backend có khóa chặn trả 409, đây là để người dùng khỏi ăn lỗi đó).
import { useRef, useState } from 'react'
import { api } from '../../api/client'
import { toast } from '../toast'
import { fmtDateTime } from '../../utils/datetime'
import { extractPesticideErrorMessage } from '../../utils/customs-pesticide'
import CustomsModal from './CustomsModal'

const ACCEPT = '.json,.xlsx'
const MAX_MB = 30

export default function CustomsPesticideImportDialog({ options, onClose, onApplied }: {
  /** Dữ liệu `/api/customs/pesticides/options` đã tải ở màn cha — khỏi gọi lại. */
  options: any
  onClose: () => void
  onApplied: () => void
}) {
  const [file, setFile] = useState<File | null>(null)
  const [uploading, setUploading] = useState(false)
  const [err, setErr] = useState('')
  const busy = useRef(false)

  const catalogTotal = options?.total ?? 0
  const manualCount = options?.manual_count ?? 0
  const sourceCount = Math.max(0, catalogTotal - manualCount)

  function close() {
    if (!uploading) onClose()
  }

  async function upload() {
    if (busy.current || !file) return
    busy.current = true
    setUploading(true)
    setErr('')
    try {
      const fd = new FormData()
      fd.append('file', file)
      const r = await api.post('/api/customs/pesticides/import', fd)
      const d = r.data.data
      toast.success(`Đã nạp ${Number(d.pesticides).toLocaleString('vi-VN')} thuốc, `
        + `${Number(d.uses).toLocaleString('vi-VN')} dòng phạm vi sử dụng`
        + (d.kept_manual ? `, giữ ${Number(d.kept_manual).toLocaleString('vi-VN')} thuốc tự thêm` : '')
        + (d.dropped ? `, bỏ ${Number(d.dropped).toLocaleString('vi-VN')} thuốc không còn trong tệp` : ''))
      onApplied()
    } catch (e: any) {
      setErr(extractPesticideErrorMessage(e, 'Không nạp được tệp'))
    } finally {
      busy.current = false
      setUploading(false)
    }
  }

  return (
    <CustomsModal title="Nạp danh mục thuốc BVTV" width={640} onClose={close}
      footer={<>
        <button className="btn ghost" type="button" disabled={uploading} onClick={close}>Hủy</button>
        <button className="btn" type="button" disabled={!file || uploading} onClick={upload}>
          <i className="ti ti-upload" />{uploading ? 'Đang nạp…' : 'Nạp danh mục'}
        </button>
      </>}>
      <p style={{ marginTop: 0, fontSize: 13 }}>
        Tệp <b>thuoc-bvtv.json</b> hoặc <b>thuoc-bvtv.xlsx</b> của bản cào danh mục thuốc BVTV
        (danhmuc.thuocbvtv.com — dữ liệu EcoFarm của Cục BVTV). Tối đa {MAX_MB} MB.
      </p>
      <input type="file" accept={ACCEPT} disabled={uploading}
        onChange={(e) => setFile(e.target.files?.[0] || null)} />
      {file && <div style={{ fontSize: 13, marginTop: 8 }}>{file.name} — {(file.size / 1024 / 1024).toFixed(1)} MB</div>}
      {catalogTotal > 0 && (
        <div style={{ marginTop: 12, border: '1px solid #f5c26b', background: '#fff8e8', color: '#8a5a00',
          borderRadius: 8, padding: '8px 12px', fontSize: 13 }}>
          <i className="ti ti-alert-triangle" /> Nạp tệp sẽ <b>thay toàn bộ {sourceCount.toLocaleString('vi-VN')} thuốc</b> lấy
          từ nguồn đang có{options?.last_loaded_at ? ` (nạp lần cuối ${fmtDateTime(options.last_loaded_at)})` : ''}; thuốc nguồn
          nào đã sửa tay cũng bị ghi đè theo nguồn mới. Thuốc vẫn còn trong tệp mới giữ nguyên tệp đính kèm;
          thuốc <b>không còn</b> trong tệp mới bị xóa cùng tệp đính kèm của nó.
          {manualCount > 0 && <> {manualCount.toLocaleString('vi-VN')} thuốc tự thêm được giữ nguyên.</>}
        </div>
      )}
      {err && <div className="err" style={{ marginTop: 12 }}>{err}</div>}
    </CustomsModal>
  )
}
