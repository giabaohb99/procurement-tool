import { Check, LoaderCircle, Users } from 'lucide-react'
import { useState } from 'react'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { DEMO_ACCOUNTS, type DemoAccount } from './demo-accounts'

/**
 * ĐỔI TÀI KHOẢN NHANH — **chỉ có ở bản chạy DEV**, để trình diễn.
 *
 * Demo phân quyền phải cho người xem thấy CÙNG MỘT MÀN HÌNH đổi ra sao theo vai
 * trò. Đăng xuất rồi gõ lại tài khoản mật khẩu mỗi lần là mất mạch nói chuyện, mà
 * người trình bày cũng phải nhớ chín cặp tài khoản.
 *
 * ⚠️ Không bao giờ được lọt vào bản build thật: `import.meta.env.DEV` là hằng số
 * Vite thay lúc build, nên ở prod dòng dưới thành `if (true) return null` và
 * Rollup cắt luôn cả phần thân lẫn mô-đun `demo-accounts` chứa mật khẩu. Sửa
 * component này thì phải build lại và `grep` mật khẩu trong `dist/` để chắc.
 *
 * **Đứng nguyên trang** sau khi đổi, không nhảy về màn chọn phân hệ: cái đáng
 * xem là màn hình đang mở khác đi thế nào. Bộ nhớ đệm truy vấn bị `logout()`
 * xóa sạch nên mọi thứ tự hỏi lại theo quyền mới.
 */
export function DemoAccountSwitcher() {
  const { user, login, logout } = useAuth()
  const [dangDoi, setDangDoi] = useState<string | null>(null)

  if (!import.meta.env.DEV) return null

  async function doiSang(account: DemoAccount) {
    if (account.username === user?.emp_code) return
    setDangDoi(account.username)
    try {
      //  Đăng xuất trước để xóa token cũ và bộ nhớ đệm truy vấn — không thì màn
      //  hình đang mở còn hiện dữ liệu của người trước trong khoảnh khắc đầu,
      //  đúng lúc người xem đang nhìn chằm chằm vào nó.
      logout()
      await login({ username: account.username, password: account.password })
      toast.success(`Đang là ${account.label}`)
    } catch {
      toast.error(`Không đăng nhập được ${account.username} — kiểm lại dữ liệu seed`)
    } finally {
      setDangDoi(null)
    }
  }

  const nhom = [...new Set(DEMO_ACCOUNTS.map((row) => row.group))]

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="icon"
          className="relative text-muted-foreground hover:text-foreground"
          title="Đổi tài khoản nhanh (chỉ có ở bản DEV)"
        >
          {dangDoi ? (
            <LoaderCircle className="size-5 animate-spin" />
          ) : (
            <Users className="size-5" />
          )}
          {/*  Chấm vàng nhắc đây là thứ của bản DEV, không phải chức năng thật. */}
          <span className="absolute top-1 right-1 size-1.5 rounded-full bg-amber-500" />
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" sideOffset={8} className="w-72">
        <DropdownMenuLabel className="flex items-center justify-between gap-2 font-normal">
          <span className="font-semibold">Đổi tài khoản nhanh</span>
          <span className="rounded-full bg-amber-100 px-2 py-0.5 text-[11px] font-semibold text-amber-800">
            DEV
          </span>
        </DropdownMenuLabel>
        <p className="px-2 pb-1.5 text-xs text-muted-foreground">
          Đứng nguyên trang, chỉ đổi người đăng nhập.
        </p>

        {nhom.map((ten) => (
          <div key={ten}>
            <DropdownMenuSeparator />
            <DropdownMenuLabel className="py-1 text-[11px] font-semibold tracking-wider text-muted-foreground uppercase">
              {ten}
            </DropdownMenuLabel>
            {DEMO_ACCOUNTS.filter((row) => row.group === ten).map((row) => {
              const dangDung = row.username === user?.emp_code
              return (
                <DropdownMenuItem
                  key={row.username}
                  disabled={Boolean(dangDoi)}
                  onSelect={(event) => {
                    //  Giữ menu mở tới lúc đăng nhập xong thì người trình bày
                    //  thấy được vòng xoay, khỏi tưởng bấm hụt.
                    event.preventDefault()
                    void doiSang(row)
                  }}
                  className="gap-2"
                >
                  <Check className={dangDung ? 'size-4' : 'invisible size-4'} />
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-[13px] font-medium">{row.label}</span>
                    <span className="block truncate text-[11px] text-muted-foreground">
                      {row.username}
                      {row.hint && ` · ${row.hint}`}
                    </span>
                  </span>
                  {dangDoi === row.username && (
                    <LoaderCircle className="size-3.5 shrink-0 animate-spin" />
                  )}
                </DropdownMenuItem>
              )
            })}
          </div>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
