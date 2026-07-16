import { useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api/client'

export default function ForgotPassword() {
  const [email, setEmail] = useState('')
  const [msg, setMsg] = useState('')
  const [err, setErr] = useState('')
  const [loading, setLoading] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setMsg('')
    setLoading(true)
    try {
      const res = await api.post('/api/auth/forgot-password', { email })
      setMsg(res.data?.message || 'Đã gửi yêu cầu khôi phục mật khẩu')
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Có lỗi xảy ra')
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

      {/* Bảng khôi phục mật khẩu */}
      <main className="lg-form-wrap">
        <div className="lg-form">
          <img src="/logo.svg" className="lg-logo-m" alt="DEGO Holding" />
          <h2 className="lg-title">Khôi phục mật khẩu</h2>
          <p className="lg-sub">Nhập email để nhận hướng dẫn đặt lại mật khẩu.</p>

          <form onSubmit={submit} className="lg-fields">
            <div className="lg-inp">
              <i className="ti ti-mail" />
              <input placeholder="Địa chỉ email" type="email" autoComplete="email" required
                value={email} onChange={(e) => setEmail(e.target.value)} />
            </div>

            {err && <div className="lg-err"><i className="ti ti-alert-circle" />{err}</div>}
            {msg && <div className="lg-ok"><i className="ti ti-circle-check" />{msg}</div>}

            <button className="lg-btn" type="submit" disabled={loading}>
              {loading ? <i className="ti ti-loader-2 lg-spin" /> : <i className="ti ti-send" />}
              {loading ? 'Đang gửi…' : 'Gửi yêu cầu'}
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
