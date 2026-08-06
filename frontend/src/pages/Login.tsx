import { useState } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'
import { GoogleLogin } from '@react-oauth/google'

export default function Login() {
  const { login, loginGoogle } = useAuth()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)
  // Máy local không có VITE_GOOGLE_CLIENT_ID -> GSI bắn liên tục "Missing required parameter:
  // client_id", nút Google trả 400 và One Tap gọi initialize() lặp, làm console đầy lỗi giả.
  const coGoogle = !!import.meta.env.VITE_GOOGLE_CLIENT_ID

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr(''); setBusy(true)
    try {
      await login(username, password)
      nav('/')
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Đăng nhập thất bại')
      setBusy(false)
    }
  }

  return (
    <div className="lg-page">
      {/* Bảng thương hiệu (ẩn trên mobile) */}
      <aside className="lg-brand" aria-hidden="true">
        <div className="lg-brand-top">
          <img src="/logo.svg" className="lg-logo" alt="DEGO Holding" />
        </div>
        <div className="lg-brand-body">
          <h1 className="lg-brand-title">Hệ thống Quản lý Thu Mua</h1>
          <p className="lg-brand-sub">
            Nền tảng nội bộ của DEGO Holding — yêu cầu, khảo sát, đơn mua hàng và công nợ, gọn trong một chỗ.
          </p>
          <ul className="lg-brand-list">
            <li><i className="ti ti-checks" /> Quy trình duyệt &amp; khảo sát minh bạch</li>
            <li><i className="ti ti-shield-lock" /> Phân quyền chặt theo vai trò</li>
            <li><i className="ti ti-chart-histogram" /> Báo cáo chi tiêu thời gian thực</li>
          </ul>
        </div>
        <div className="lg-brand-foot">© {new Date().getFullYear()} DEGO Holding</div>
      </aside>

      {/* Bảng đăng nhập */}
      <main className="lg-form-wrap">
        <div className="lg-form">
          <img src="/logo.svg" className="lg-logo-m" alt="DEGO Holding" />
          <h2 className="lg-title">Đăng nhập</h2>
          <p className="lg-sub">Dùng mã nhân viên nội bộ để tiếp tục.</p>

          <form onSubmit={submit} className="lg-fields">
            <div className="lg-inp">
              <i className="ti ti-id-badge-2" />
              <input placeholder="Mã nhân viên" autoComplete="username" value={username}
                onChange={(e) => setUsername(e.target.value)} />
            </div>
            <div className="lg-inp">
              <i className="ti ti-lock" />
              <input placeholder="Mật khẩu" type="password" autoComplete="current-password" value={password}
                onChange={(e) => setPassword(e.target.value)} />
            </div>

            <div className="lg-row">
              <Link to="/forgot-password" className="lg-link">Quên mật khẩu?</Link>
            </div>

            {err && <div className="lg-err"><i className="ti ti-alert-circle" />{err}</div>}

            <button className="lg-btn" type="submit" disabled={busy}>
              {busy ? <i className="ti ti-loader-2 lg-spin" /> : <i className="ti ti-login-2" />}
              {busy ? 'Đang đăng nhập…' : 'Đăng nhập'}
            </button>
          </form>

          {coGoogle && <>
          <div className="lg-or"><span>HOẶC</span></div>

          <div className="lg-google">
            <GoogleLogin
              onSuccess={async (credentialResponse) => {
                if (credentialResponse.credential) {
                  setErr('')
                  try {
                    await loginGoogle(credentialResponse.credential)
                    nav('/')
                  } catch (ex: any) {
                    setErr(ex?.response?.data?.error?.message || 'Đăng nhập Google thất bại')
                  }
                }
              }}
              onError={() => setErr('Đăng nhập Google bị lỗi hoặc bị hủy')}
              useOneTap
            />
          </div>
          </>}

          <p className="lg-foot-m">© {new Date().getFullYear()} DEGO Holding · Hệ thống nội bộ</p>
        </div>
      </main>
    </div>
  )
}
