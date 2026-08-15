import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  CircleAlert,
  CircleCheck,
  Loader2,
  Mail,
  Send,
} from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link } from 'react-router-dom'

import { extractErrorMessage, httpClient } from '@/core/api'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Form, FormControl, FormField, FormItem, FormMessage } from '@/shared/ui/form'
import { IconInput } from '@/shared/ui/icon-input'
import {
  forgotPasswordSchema,
  type ForgotPasswordFormValues,
} from '../forgot-password-schema'

/** Gửi email đặt lại mật khẩu. Backend trả link kèm token qua email. */
export function ForgotPasswordPage() {
  // Dùng `message` của phong bì (không phải `data`) nên gọi httpClient trực tiếp.
  const [successMessage, setSuccessMessage] = useState('')

  const form = useForm<ForgotPasswordFormValues>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: { email: '' },
  })

  async function onSubmit(values: ForgotPasswordFormValues) {
    setSuccessMessage('')
    try {
      const res = await httpClient.post('/api/auth/forgot-password', values, {
        _silent: true,
      } as never)
      setSuccessMessage(
        res.data?.message || 'Đã gửi yêu cầu khôi phục mật khẩu, kiểm tra hộp thư.',
      )
    } catch (error) {
      form.setError('root', { message: extractErrorMessage(error) })
    }
  }

  const { isSubmitting } = form.formState

  return (
    <>
      <h2 className="mb-1.5 text-[26px] font-extrabold tracking-[-0.4px] text-navy">
        Khôi phục mật khẩu
      </h2>
      <p className="mb-6.5 text-sm text-muted-foreground">
        Nhập email để nhận hướng dẫn đặt lại mật khẩu.
      </p>

      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3.5">
          <FormField
            control={form.control}
            name="email"
            render={({ field }) => (
              <FormItem>
                <FormControl>
                  <IconInput
                    icon={Mail}
                    type="email"
                    placeholder="Địa chỉ email"
                    autoComplete="email"
                    autoFocus
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
              {successMessage}
            </div>
          )}

          <Button
            type="submit"
            disabled={isSubmitting}
            className="auth-submit mt-2 h-12 w-full rounded-xl text-[15px] font-semibold transition"
          >
            {isSubmitting ? (
              <Loader2 className="size-[18px] animate-spin" />
            ) : (
              <Send className="size-[18px]" />
            )}
            {isSubmitting ? 'Đang gửi…' : 'Gửi yêu cầu'}
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
