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
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand"><i className="ti ti-building-warehouse" />Thu Mua Tool</div>
        <div className="sub">Khôi phục mật khẩu</div>
        <form className="field" onSubmit={submit}>
          <input 
            placeholder="Nhập địa chỉ email của bạn" 
            type="email" 
            required
            value={email} 
            onChange={(e) => setEmail(e.target.value)} 
          />
          {err && <div className="err">{err}</div>}
          {msg && <div style={{ color: 'green', fontSize: 13, marginBottom: 10 }}>{msg}</div>}
          <button className="btn" type="submit" disabled={loading} style={{ height: 42, justifyContent: 'center' }}>
            {loading ? 'Đang gửi...' : 'Gửi yêu cầu'}
          </button>
        </form>
        <div style={{ marginTop: 20, textAlign: 'center' }}>
          <Link to="/login" style={{ fontSize: 13, color: '#1c9cf0', textDecoration: 'none' }}>
            <i className="ti ti-arrow-left" style={{ marginRight: 4 }} /> Quay lại đăng nhập
          </Link>
        </div>
      </div>
    </div>
  )
}
