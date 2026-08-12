import { zodResolver } from '@hookform/resolvers/zod'
import { CircleAlert, IdCard, Loader2, LockKeyhole, LogIn } from 'lucide-react'
import { useForm } from 'react-hook-form'
import { Link, useLocation, useNavigate } from 'react-router-dom'

import { extractErrorMessage } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form, FormControl, FormField, FormItem, FormMessage } from '@/shared/ui/form'
import { IconInput } from '@/shared/ui/icon-input'
import { loginSchema, type LoginFormValues } from '../login-schema'
import { useAuth } from '../use-auth'

/**
 * Màn đăng nhập — cũng là khuôn mẫu cho mọi form trong hệ: react-hook-form +
 * zodResolver, lỗi API gắn vào form (không dùng toast) để người dùng thấy ngay
 * tại chỗ nhập. Bố cục/thẩm mỹ giữ đúng bản `frontend/` hiện hành.
 */
export function LoginPage() {
  const { login, isLoggingIn } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()

  const form = useForm<LoginFormValues>({
    resolver: zodResolver(loginSchema),
    defaultValues: { username: '', password: '' },
  })

  async function onSubmit(values: LoginFormValues) {
    try {
      await login(values)
      // Quay lại đúng trang người dùng định vào trước khi bị chặn.
      const from = (location.state as { from?: Location } | null)?.from?.pathname
      navigate(from ?? appRoutes.launcher, { replace: true })
    } catch (error) {
      form.setError('root', { message: extractErrorMessage(error) })
    }
  }

  return (
    <>
      <h2 className="mb-1.5 text-[26px] font-extrabold tracking-[-0.4px] text-navy">
        Đăng nhập
      </h2>
      <p className="mb-6.5 text-sm text-muted-foreground">
        Dùng mã nhân viên nội bộ để tiếp tục.
      </p>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5">
          <FormField
            control={form.control}
            name="username"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <IconInput
                    icon={IdCard}
                    placeholder="Mã nhân viên"
                    autoComplete="username"
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
            name="password"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <IconInput
                    icon={LockKeyhole}
                    type="password"
                    placeholder="Mật khẩu"
                    autoComplete="current-password"
                    {...field}
                  />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="mt-1 flex justify-end">
            <Link
              to={appRoutes.forgotPassword}
              className="text-[13px] font-medium text-primary hover:underline"
            >
              Quên mật khẩu?
            </Link>
          </div>

          {form.formState.errors.root && (
            <div className="flex items-center gap-2 rounded-[10px] border border-red-200 bg-red-100 px-3 py-2.5 text-[13px] text-destructive">
              <CircleAlert className="size-4 shrink-0" />
              {form.formState.errors.root.message}
            </div>
          )}

          <Button
            type="submit"
            disabled={isLoggingIn}
            className="auth-submit mt-2 h-12 w-full rounded-xl text-[15px] font-semibold transition"
          >
            {isLoggingIn ? (
              <Loader2 className="size-[18px] animate-spin" />
            ) : (
              <LogIn className="size-[18px]" />
            )}
            {isLoggingIn ? 'Đang đăng nhập…' : 'Đăng nhập'}
          </Button>
        </form>
      </Form>
    </>
  )
}
