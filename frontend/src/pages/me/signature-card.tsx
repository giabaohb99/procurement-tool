import { useEffect, useState } from 'react'
import { api } from '../../api/client'
import { toast } from '../../components/toast'
import { askConfirm } from '../../components/confirm'
import { prepareSignatureImage } from '../../utils/prepare-signature-image'

/**
 * Chữ ký cá nhân dạng ẢNH — người dùng tự tải lên / thay / gỡ tại Trang cá nhân.
 * Lưu ở tab_user.signature (URL trên storage), tải qua POST /api/auth/signature.
 * Ảnh luôn được THU NHỎ (và tách nền nếu bật) ngay ở trình duyệt trước khi gửi lên,
 * để ảnh 4000px vài MB từ điện thoại không chiếm dung lượng storage vô ích.
 */
export default function SignatureCard({ signature }: { signature?: string }) {
  const [src, setSrc] = useState(signature || '')
  const [busy, setBusy] = useState(false)
  // Mặc định bật: đa số người dùng chụp/scan chữ ký trên giấy trắng.
  // Tắt khi ảnh đã là PNG nền trong sẵn (xử lý lại chỉ làm nét mực bị mỏng đi).
  const [autoRemoveBg, setAutoRemoveBg] = useState(true)
  // /auth/me trả về sau khi component mount → đồng bộ lại khi dữ liệu hồ sơ vừa tới
  useEffect(() => { setSrc(signature || '') }, [signature])

  async function upload(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (!file) return
    setBusy(true)
    try {
      // Xử lý lỗi (ảnh hỏng, canvas bị chặn…) thì vẫn gửi ảnh gốc, không chặn người dùng
      let toSend = file
      try { toSend = await prepareSignatureImage(file, { removeBg: autoRemoveBg }) }
      catch { toast.error('Không xử lý được ảnh — giữ nguyên ảnh gốc') }
      const fd = new FormData()
      fd.append('file', toSend)
      const r = await api.post('/api/auth/signature', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
      setSrc(r.data.data.signature)
      toast.success('Đã cập nhật chữ ký')
    } catch (ex: any) {
      toast.error(ex?.response?.data?.error?.message || 'Không tải được ảnh chữ ký')
    } finally {
      setBusy(false)
      e.target.value = ''
    }
  }

  async function remove() {
    if (!(await askConfirm({ message: 'Gỡ ảnh chữ ký khỏi hồ sơ?' }))) return
    setBusy(true)
    try {
      await api.delete('/api/auth/signature')
      setSrc('')
      toast.success('Đã gỡ chữ ký')
    } catch {
      toast.error('Không gỡ được chữ ký')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="card">
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-signature" style={{ marginRight: 8, color: '#b6c2d9' }} />Chữ ký cá nhân
      </h3>

      {/* Khung xem trước nền ô carô để thấy rõ chữ ký PNG nền trong */}
      <div className="sign-preview">
        {src
          ? <img src={src} alt="Chữ ký cá nhân" />
          : <span className="sign-empty"><i className="ti ti-signature" />Chưa có chữ ký</span>}
      </div>

      <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, fontWeight: 500,
                      color: 'var(--muted)', margin: '12px 0 0' }}>
        <input type="checkbox" checked={autoRemoveBg} disabled={busy}
               onChange={(e) => setAutoRemoveBg(e.target.checked)} />
        Tự động xóa nền trắng của ảnh
      </label>

      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginTop: 10 }}>
        <label className="btn" style={{ cursor: busy ? 'default' : 'pointer', opacity: busy ? 0.6 : 1 }}>
          <i className={busy ? 'ti ti-loader' : 'ti ti-upload'} />
          {busy ? 'Đang xử lý…' : src ? 'Đổi chữ ký' : 'Tải chữ ký lên'}
          <input type="file" hidden accept="image/*" onChange={upload} disabled={busy} />
        </label>
        {src && (
          <button className="btn ghost" disabled={busy} onClick={remove}
                  style={{ color: 'var(--red)', borderColor: 'var(--red)' }}>
            <i className="ti ti-trash" />Gỡ chữ ký
          </button>
        )}
      </div>

      <div className="me-note">
        <i className="ti ti-info-circle" />
        <span>
          Chụp/scan chữ ký viết bằng bút đậm trên giấy trắng — hệ thống tự tách nền thành ảnh trong suốt.
          Nếu ảnh đã là PNG nền trong sẵn, hãy bỏ chọn "Tự động xóa nền".
          Ảnh lớn được tự thu nhỏ về tối đa 800×400px trước khi tải lên.
        </span>
      </div>
    </div>
  )
}
