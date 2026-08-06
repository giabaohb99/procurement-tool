import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../../api/client'
import { toast } from '../../components/toast'
import { useAuth } from '../../auth/AuthContext'

/** Đổi mật khẩu của chính mình. Đổi xong buộc đăng nhập lại bằng mật khẩu mới. */
export default function ChangePasswordCard() {
  const { logout } = useAuth()
  const nav = useNavigate()
  const [oldP, setOldP] = useState('')
  const [newP, setNewP] = useState('')
  const [conf, setConf] = useState('')
  const [show, setShow] = useState(false)
  const [busy, setBusy] = useState(false)

  // Cảnh báo ngay khi gõ, không đợi bấm nút mới báo lỗi
  const tooShort = newP.length > 0 && newP.length < 6
  const mismatch = conf.length > 0 && newP !== conf
  const ready = oldP.length > 0 && newP.length >= 6 && newP === conf

  async function submit() {
    if (!ready) return
    setBusy(true)
    try {
      await api.post('/api/auth/change-password', { old_password: oldP, new_password: newP })
      setOldP(''); setNewP(''); setConf('')
      toast.success('Đã đổi mật khẩu — vui lòng đăng nhập lại')
      setTimeout(() => { logout(); nav('/login') }, 1000)
    } catch (e: any) {
      toast.error(e?.response?.data?.error?.message || 'Lỗi đổi mật khẩu')
      setBusy(false)
    }
  }

  const type = show ? 'text' : 'password'
  return (
    <div className="card">
      <h3 className="sec-title" style={{ marginTop: 0 }}>
        <i className="ti ti-lock" style={{ marginRight: 8, color: '#b6c2d9' }} />Đổi mật khẩu
      </h3>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <div>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Mật khẩu hiện tại</label>
          <input type={type} value={oldP} autoComplete="current-password" onChange={(e) => setOldP(e.target.value)} />
        </div>
        <div>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Mật khẩu mới</label>
          <input type={type} value={newP} autoComplete="new-password" onChange={(e) => setNewP(e.target.value)} />
          <div style={{ fontSize: 12, marginTop: 4, color: tooShort ? 'var(--red)' : 'var(--muted)' }}>
            Tối thiểu 6 ký tự.
          </div>
        </div>
        <div>
          <label style={{ fontSize: 12, color: 'var(--muted)' }}>Xác nhận mật khẩu mới</label>
          <input type={type} value={conf} autoComplete="new-password" onChange={(e) => setConf(e.target.value)} />
          {mismatch && (
            <div style={{ fontSize: 12, marginTop: 4, color: 'var(--red)' }}>Hai mật khẩu chưa khớp.</div>
          )}
        </div>
        <label style={{ display: 'flex', alignItems: 'center', gap: 8, fontSize: 12.5, fontWeight: 500, color: 'var(--muted)', margin: 0 }}>
          <input type="checkbox" checked={show} onChange={(e) => setShow(e.target.checked)} />
          Hiện mật khẩu
        </label>
        <button className="btn" disabled={busy || !ready} onClick={submit} style={{ alignSelf: 'flex-start' }}>
          <i className="ti ti-lock" />{busy ? 'Đang đổi…' : 'Đổi mật khẩu'}
        </button>
      </div>
      <div className="me-note">
        <i className="ti ti-info-circle" />
        <span>Sau khi đổi mật khẩu, hệ thống sẽ đăng xuất để bạn đăng nhập lại bằng mật khẩu mới.</span>
      </div>
    </div>
  )
}
