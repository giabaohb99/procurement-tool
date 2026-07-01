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
          <Link to="/forgot-password" style={{ fontSize: 13, textAlign: 'right', display: 'block', color: '#1c9cf0', textDecoration: 'none' }}>Quên mật khẩu?</Link>
          {err && <div className="err">{err}</div>}
          <button className="btn" type="submit" style={{ height: 42, justifyContent: 'center' }}>Đăng nhập</button>
        </form>
        <div style={{ margin: '20px 0', display: 'flex', alignItems: 'center', color: '#666' }}>
          <div style={{ flex: 1, height: 1, backgroundColor: '#eee' }}></div>
          <span style={{ padding: '0 10px', fontSize: 13 }}>HOẶC</span>
          <div style={{ flex: 1, height: 1, backgroundColor: '#eee' }}></div>
        </div>
        <div style={{ display: 'flex', justifyContent: 'center' }}>
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
      </div>
    </div>
  )
}
