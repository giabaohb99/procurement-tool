import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '../auth/AuthContext'

export default function Login() {
  const { login } = useAuth()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    try {
      await login(username, password)
      nav('/')
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Đăng nhập thất bại')
    }
  }

  return (
    <div className="login-wrap">
      <div className="login-card">
        <div className="brand"><i className="ti ti-building-warehouse" />Thu Mua Tool</div>
        <div className="sub">Đăng nhập hệ thống nội bộ</div>
        <form className="field" onSubmit={submit}>
          <input placeholder="Mã nhân viên" value={username} onChange={(e) => setUsername(e.target.value)} />
          <input placeholder="Mật khẩu" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
          {err && <div className="err">{err}</div>}
          <button className="btn" type="submit" style={{ height: 42, justifyContent: 'center' }}>Đăng nhập</button>
        </form>
      </div>
    </div>
  )
}
