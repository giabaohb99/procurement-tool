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
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand"><i className="ti ti-building-warehouse" />Thu Mua Tool</div>
        <div className="sub">Đặt lại mật khẩu mới</div>
        <form className="field" onSubmit={submit}>
          <input 
            placeholder="Mật khẩu mới" 
            type="password" 
            required
            value={password} 
            onChange={(e) => setPassword(e.target.value)} 
          />
          <input 
            placeholder="Nhập lại mật khẩu mới" 
            type="password" 
            required
            value={confirmPassword} 
            onChange={(e) => setConfirmPassword(e.target.value)} 
          />
          {err && <div className="err">{err}</div>}
          {msg && <div style={{ color: 'green', fontSize: 13, marginBottom: 10 }}>{msg}</div>}
          <button className="btn" type="submit" disabled={loading} style={{ height: 42, justifyContent: 'center' }}>
            {loading ? 'Đang xử lý...' : 'Xác nhận đổi mật khẩu'}
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
