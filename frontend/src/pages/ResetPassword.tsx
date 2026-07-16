import { useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'
import { api } from '../api/client'

export default function ResetPassword() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const nav = useNavigate()

  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setMsg('')

    if (!token) {
      setErr('Thiếu mã xác thực (token)')
      return
    }

    if (password !== confirmPassword) {
      setErr('Mật khẩu nhập lại không khớp')
      return
    }

    setLoading(true)
    try {
      const res = await api.post('/api/auth/reset-password', { token, new_password: password })
      setMsg(res.data?.message || 'Khôi phục mật khẩu thành công')
      setTimeout(() => nav('/login'), 2000)
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Có lỗi xảy ra hoặc mã đã hết hạn')
    } finally {
      setLoading(false)
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

      {/* Bảng đặt lại mật khẩu */}
      <main className="lg-form-wrap">
        <div className="lg-form">
          <img src="/logo.svg" className="lg-logo-m" alt="DEGO Holding" />
          <h2 className="lg-title">Đặt lại mật khẩu</h2>
          <p className="lg-sub">Nhập mật khẩu mới cho tài khoản của bạn.</p>

          <form onSubmit={submit} className="lg-fields">
            <div className="lg-inp">
              <i className="ti ti-lock" />
              <input placeholder="Mật khẩu mới" type="password" autoComplete="new-password" required
                value={password} onChange={(e) => setPassword(e.target.value)} />
            </div>
            <div className="lg-inp">
              <i className="ti ti-lock-check" />
              <input placeholder="Nhập lại mật khẩu mới" type="password" autoComplete="new-password" required
                value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} />
            </div>

            {err && <div className="lg-err"><i className="ti ti-alert-circle" />{err}</div>}
            {msg && <div className="lg-ok"><i className="ti ti-circle-check" />{msg}</div>}

            <button className="lg-btn" type="submit" disabled={loading}>
              {loading ? <i className="ti ti-loader-2 lg-spin" /> : <i className="ti ti-lock-check" />}
              {loading ? 'Đang xử lý…' : 'Xác nhận đổi mật khẩu'}
            </button>
          </form>

          <div className="lg-row" style={{ justifyContent: 'center', marginTop: 16 }}>
            <Link to="/login" className="lg-link">
              <i className="ti ti-arrow-left" style={{ marginRight: 4 }} /> Quay lại đăng nhập
            </Link>
          </div>

          <p className="lg-foot-m">© {new Date().getFullYear()} DEGO Holding · Hệ thống nội bộ</p>
        </div>
      </main>
    </div>
  )
}
