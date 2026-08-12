import { BarChart3, CheckCheck, ShieldCheck } from 'lucide-react'
import { Navigate, Outlet } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { appRoutes } from '@/shared/constants/app-routes'

/** Điểm mạnh hiển thị ở bảng thương hiệu. */
const HIGHLIGHTS = [
  { icon: CheckCheck, text: 'Liên thông nghiệp vụ trên một nền dữ liệu' },
  { icon: ShieldCheck, text: 'Phân quyền chặt theo vai trò' },
  { icon: BarChart3, text: 'Báo cáo điều hành thời gian thực' },
]

/**
 * Khung cho mọi màn công khai (đăng nhập, quên mật khẩu…): bảng thương hiệu bên
 * trái + form bên phải. Bảng thương hiệu ẩn trên màn hẹp, khi đó form chiếm hết
 * chiều ngang và hiện logo + dòng bản quyền phiên bản rút gọn.
 */
export function AuthLayout() {
  const { isAuthenticated } = useAuth()
  const year = new Date().getFullYear()

  // Đã đăng nhập mà mở /login thì đưa thẳng vào trong, không bắt đăng nhập lại.
  if (isAuthenticated) return <Navigate to={appRoutes.launcher} replace />

  return (
    <div className="grid min-h-dvh bg-background lg:grid-cols-[1.05fr_0.95fr]">
      <aside
        aria-hidden="true"
        className="auth-brand relative hidden flex-col justify-between overflow-hidden px-13 py-11.5 text-white lg:flex"
      >
        {/* z-10 để nội dung nổi trên lớp lưới chấm (::after của .auth-brand). */}
        <img
          src="/logo.svg"
          alt="DEGO Holding"
          className="relative z-10 h-11 w-auto drop-shadow-[0_2px_8px_rgba(0,0,0,0.25)]"
        />

        <div className="relative z-10 max-w-[460px]">
          <h1 className="mb-3.5 text-[34px] leading-[1.12] font-extrabold tracking-[-0.6px]">
            Hệ thống Quản trị Doanh nghiệp
          </h1>
          <p className="mb-6.5 max-w-[42ch] text-[15.5px] leading-relaxed text-white/75">
            Nền tảng ERP nội bộ của DEGO Holding — bán hàng, kho, mua hàng, tài chính và
            nhân sự, gọn trong một chỗ.
          </p>

          <ul className="flex flex-col gap-3.5">
            {HIGHLIGHTS.map(({ icon: Icon, text }) => (
              <li key={text} className="flex items-center gap-3 text-[14.5px] text-white/85">
                <span className="grid size-6.5 shrink-0 place-items-center rounded-lg bg-sky-soft/12">
                  <Icon className="size-[19px] text-sky-soft" />
                </span>
                {text}
              </li>
            ))}
          </ul>
        </div>

        <p className="relative z-10 text-[12.5px] text-white/50">© {year} DEGO Holding</p>
      </aside>

      <main className="flex items-center justify-center px-6 py-10">
        <div className="auth-rise w-full max-w-[372px]">
          <img
            src="/logo.svg"
            alt="DEGO Holding"
            className="mx-auto mb-5 h-[38px] w-auto lg:hidden"
          />

          <Outlet />

          <p className="mt-5.5 text-center text-xs text-muted-foreground lg:hidden">
            © {year} DEGO Holding · Hệ thống nội bộ
          </p>
        </div>
      </main>
    </div>
  )
}
