import { Component, type ErrorInfo, type ReactNode } from 'react'
import { AlertTriangle } from 'lucide-react'

import { Button } from '@/components/ui/button'

// Lưới an toàn cuối cùng: lỗi render ở bất kỳ đâu trong app cũng phải ra MỘT THÔNG BÁO ĐỌC ĐƯỢC,
// không để trang trắng. React chỉ bắt được lỗi render qua class component nên chỗ này buộc dùng class.
// Lỗi gọi API đã có interceptor toast riêng (api/client.ts) — chỗ này lo phần còn lại.

interface State {
  error: Error | null
}

export default class AppErrorBoundary extends Component<{ children: ReactNode }, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // Giữ log ở console để còn lần được vết khi người dùng báo lỗi
    console.error('[HelpCenter] Lỗi không bắt được:', error, info.componentStack)
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="flex min-h-screen items-center justify-center bg-background px-6">
        <div className="w-full max-w-lg rounded-xl border p-8 text-center">
          <span className="mx-auto mb-4 grid size-12 place-items-center rounded-xl bg-destructive/10 text-destructive">
            <AlertTriangle className="size-6" />
          </span>

          <h1 className="text-lg font-bold text-ink">Trang gặp sự cố</h1>
          <p className="mt-2 text-sm leading-relaxed text-ink-muted">
            Đã có lỗi khiến trang không hiển thị được. Bạn thử tải lại; nếu vẫn lỗi thì báo
            quản trị viên kèm nội dung bên dưới.
          </p>

          {/* Thông điệp lỗi để người dùng chụp màn hình gửi lại — không đổ nguyên stack ra ngoài */}
          <pre className="mt-4 overflow-x-auto rounded-md bg-muted p-3 text-left text-xs text-ink-muted">
            {error.message || String(error)}
          </pre>

          <div className="mt-6 flex justify-center gap-3">
            <Button onClick={() => window.location.reload()}>Tải lại trang</Button>
            <Button variant="outline" onClick={() => { window.location.href = '/' }}>
              Về trang chủ
            </Button>
          </div>
        </div>
      </div>
    )
  }
}
