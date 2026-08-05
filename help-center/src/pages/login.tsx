import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { AlertCircle, BookOpen, IdCard, Images, Loader2, LogIn, Lock, Search } from 'lucide-react'

import { useAuth } from '@/auth/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

// Đăng nhập riêng cho Trung tâm Hướng dẫn sử dụng — dùng tài khoản nội bộ chung với app Thu mua.

const HIGHLIGHTS = [
  { Icon: BookOpen, text: 'Tài liệu theo từng bước của quy trình' },
  { Icon: Images, text: 'Hướng dẫn kèm ảnh minh họa' },
  { Icon: Search, text: 'Tìm kiếm nhanh theo tiêu đề & nội dung' },
]

export default function Login() {
  const { login, can } = useAuth()
  const nav = useNavigate()
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setErr('')
    setBusy(true)
    try {
      const u = await login(username, password)
      // Khu người dùng vốn công khai → người có quyền quản trị vào thẳng khu quản trị
      nav(u?.permissions?.help_article?.write ? '/admin' : '/')
    } catch (ex: any) {
      setErr(ex?.response?.data?.error?.message || 'Đăng nhập thất bại')
      setBusy(false)
    }
  }

  return (
    <div className="grid min-h-screen lg:grid-cols-[1.05fr_0.95fr]">
      {/* Bảng thương hiệu (ẩn trên mobile) */}
      <aside
        aria-hidden
        className="relative hidden flex-col justify-between overflow-hidden bg-[radial-gradient(1100px_520px_at_12%_8%,rgba(0,174,239,0.28),transparent_60%),radial-gradient(900px_600px_at_100%_100%,rgba(0,174,239,0.2),transparent_55%),linear-gradient(155deg,#14224f_0%,#1b2559_42%,#0f2b52_100%)] p-12 text-white lg:flex"
      >
        {/* self-start: aside là flex-col nên mặc định con bị kéo rộng hết cột, logo trông như căn giữa */}
        <img src="/logo.svg" alt="DEGO Holding" className="relative z-10 h-11 w-auto self-start drop-shadow-lg" />

        <div className="relative z-10 max-w-md">
          <h1 className="mb-3.5 text-4xl font-extrabold leading-tight tracking-tight">
            Trung tâm Hướng dẫn Sử dụng
          </h1>
          <p className="mb-7 text-white/75">
            Toàn bộ tài liệu, quy trình và giải đáp thắc mắc về hệ thống Quản lý Thu Mua của DEGO Holding.
          </p>
          <ul className="space-y-3">
            {HIGHLIGHTS.map(({ Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-white/85">
                <span className="grid size-7 shrink-0 place-items-center rounded-lg bg-sky-400/15 text-sky-300">
                  <Icon className="size-4" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>

        <div className="relative z-10 text-xs text-white/50">© {new Date().getFullYear()} DEGO Holding</div>
      </aside>

      {/* Bảng đăng nhập */}
      <main className="flex items-center justify-center px-6 py-10">
        <div className="w-full max-w-sm">
          <img src="/logo.svg" alt="DEGO Holding" className="mx-auto mb-5 h-9 w-auto lg:hidden" />

          <h2 className="mb-1.5 text-2xl font-extrabold tracking-tight text-navy">Đăng nhập</h2>
          <p className="mb-7 text-sm text-muted-foreground">
            Dùng mã nhân viên nội bộ để xem tài liệu hướng dẫn.
          </p>

          <form onSubmit={submit} className="space-y-3.5">
            <div className="relative">
              <IdCard className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Mã nhân viên"
                autoComplete="username"
                className="h-12 pl-10"
              />
            </div>

            <div className="relative">
              <Lock className="pointer-events-none absolute left-3.5 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Mật khẩu"
                autoComplete="current-password"
                className="h-12 pl-10"
              />
            </div>

            {err && (
              <div className="flex items-center gap-2 rounded-lg border border-destructive/25 bg-destructive/10 px-3 py-2.5 text-sm text-destructive">
                <AlertCircle className="size-4 shrink-0" />
                {err}
              </div>
            )}

            <Button type="submit" disabled={busy} size="lg" className="h-12 w-full text-base">
              {busy ? <Loader2 className="animate-spin" /> : <LogIn />}
              {busy ? 'Đang đăng nhập…' : 'Đăng nhập'}
            </Button>
          </form>

          <p className="mt-6 text-center text-xs text-muted-foreground lg:hidden">
            © {new Date().getFullYear()} DEGO Holding · Hệ thống nội bộ
          </p>
        </div>
      </main>
    </div>
  )
}
