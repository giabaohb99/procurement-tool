import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  CircleAlert,
  CircleCheck,
  Loader2,
  Lock,
  LockKeyhole,
} from 'lucide-react'
import { useEffect, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useSearchParams } from 'react-router-dom'

import { extractErrorMessage, httpClient } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form, FormControl, FormField, FormItem, FormMessage } from '@/shared/ui/form'
import { IconInput } from '@/shared/ui/icon-input'
import {
  resetPasswordSchema,
  type ResetPasswordFormValues,
} from '../reset-password-schema'

/** Chuyển về màn đăng nhập sau khi đổi xong — đủ lâu để đọc hết dòng báo thành công. */
const REDIRECT_MS = 2000

/**
 * Đặt lại mật khẩu bằng đường dẫn trong email khôi phục (`?token=`).
 *
 * Màn CÔNG KHAI, đứng cạnh Đăng nhập và Quên mật khẩu trong `AuthLayout`. Không
 * có nó thì luồng quên mật khẩu đứt ở giữa: thư gửi đi được, bấm vào link thì
 * rơi vào 404.
 *
 * Token do backend dựng từ `FRONTEND_URL` — ngày `frontend-v2` thay bản cũ thì
 * phải đổi biến đó ở `.env` của prod lẫn dev, nếu không thư vẫn dẫn về giao diện cũ.
 */
export function ResetPasswordPage() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const token = searchParams.get('token') ?? ''

  const [successMessage, setSuccessMessage] = useState('')

  const form = useForm<ResetPasswordFormValues>({
    resolver: zodResolver(resetPasswordSchema),
    defaultValues: { password: '', confirmPassword: '' },
  })

  // Đổi xong thì tự về màn đăng nhập. Dọn timer khi rời trang để tránh điều
  // hướng "ma" nếu người dùng tự bấm đi chỗ khác trước.
  useEffect(() => {
    if (!successMessage) return
    const timer = setTimeout(() => navigate(appRoutes.login, { replace: true }), REDIRECT_MS)
    return () => clearTimeout(timer)
  }, [successMessage, navigate])

  async function onSubmit(values: ResetPasswordFormValues) {
    // Thiếu token thì KHÔNG gọi API: đằng nào backend cũng từ chối, gọi lên chỉ
    // tốn một nhịp chờ rồi trả về đúng câu này.
    if (!token) {
      form.setError('root', { message: 'Thiếu mã xác thực. Hãy mở lại đường dẫn trong email.' })
      return
    }

    setSuccessMessage('')
    try {
      // Cần `message` của phong bì (không phải `data`) nên gọi httpClient trực tiếp.
      const res = await httpClient.post(
        '/api/auth/reset-password',
        { token, new_password: values.password },
        { _silent: true } as never,
      )
      setSuccessMessage(res.data?.message || 'Đặt lại mật khẩu thành công.')
      form.reset()
    } catch (error) {
      form.setError('root', { message: extractErrorMessage(error) })
    }
  }

  const { isSubmitting } = form.formState

  return (
    <>
      <h2 className="mb-1.5 text-[26px] font-extrabold tracking-[-0.4px] text-navy">
        Đặt lại mật khẩu
      </h2>
      <p className="mb-6.5 text-sm text-muted-foreground">
        Nhập mật khẩu mới cho tài khoản của bạn.
      </p>

      {/* Báo THIẾU TOKEN ngay khi mở trang, không đợi bấm gửi mới nói. */}
      {!token && (
        <div className="mb-4 flex items-start gap-2 rounded-[10px] border border-amber-200 bg-amber-50 px-3 py-2.5 text-[13px] text-amber-700">
          <CircleAlert className="mt-0.5 size-4 shrink-0" />
          <span>
            Đường dẫn thiếu mã xác thực. Hãy mở lại đúng liên kết trong email khôi phục, hoặc{' '}
            <Link to={appRoutes.forgotPassword} className="font-semibold underline">
              gửi lại yêu cầu
            </Link>
            .
          </span>
        </div>
      )}

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5">
          <FormField
            control={form.control}
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <IconInput
                    icon={Lock}
                    type="password"
                    placeholder="Mật khẩu mới"
                    autoComplete="new-password"
                    autoFocus
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="confirmPassword"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <IconInput
                    icon={LockKeyhole}
                    type="password"
                    placeholder="Nhập lại mật khẩu mới"
                    autoComplete="new-password"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          {form.formState.errors.root && (
            <div className="flex items-center gap-2 rounded-[10px] border border-red-200 bg-red-100 px-3 py-2.5 text-[13px] text-destructive">
              <CircleAlert className="size-4 shrink-0" />
              {form.formState.errors.root.message}
            </div>
          )}

          {successMessage && (
            <div className="flex items-center gap-2 rounded-[10px] border border-emerald-200 bg-emerald-50 px-3 py-2.5 text-[13px] text-emerald-600">
              <CircleCheck className="size-4 shrink-0" />
              {successMessage} Đang chuyển về màn đăng nhập…
            </div>
          )}

          <Button
            type="submit"
            disabled={isSubmitting || !!successMessage}
            className="auth-submit mt-2 h-12 w-full rounded-xl text-[15px] font-semibold transition"
          >
            {isSubmitting ? (
              <Loader2 className="size-[18px] animate-spin" />
            ) : (
              <LockKeyhole className="size-[18px]" />
            )}
            {isSubmitting ? 'Đang xử lý…' : 'Xác nhận đổi mật khẩu'}
          </Button>
        </form>
      </Form>

      <div className="mt-4 flex justify-center">
        <Link
          to={appRoutes.login}
          className="flex items-center gap-1 text-[13px] font-medium text-primary hover:underline"
        >
          <ArrowLeft className="size-3.5" />
          Quay lại đăng nhập
        </Link>
      </div>
    </>
  )
}
