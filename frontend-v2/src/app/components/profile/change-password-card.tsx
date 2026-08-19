import { zodResolver } from '@hookform/resolvers/zod'
import { CircleAlert, Info, Loader2, Lock } from 'lucide-react'
import { useState } from 'react'
import { useForm } from 'react-hook-form'
import { toast } from 'sonner'

import { extractErrorMessage, httpClient } from '@/core/api'
import {
  changePasswordSchema,
  type ChangePasswordFormValues,
} from '@/core/auth/change-password-schema'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { FormCard } from '@/shared/ui/form-card'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'

/**
 * Đổi mật khẩu của chính mình.
 *
 * KHÔNG tự đăng xuất sau khi đổi: backend không thu hồi token nào cả, nên đá
 * người dùng ra màn đăng nhập chỉ gây phiền chứ không làm phiên nào an toàn
 * hơn. Đổi lại, phải nói rõ các thiết bị khác vẫn còn đăng nhập.
 */
export function ChangePasswordCard() {
  const [showPassword, setShowPassword] = useState(false)

  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { oldPassword: '', newPassword: '', confirmPassword: '' },
  })

  async function onSubmit(values: ChangePasswordFormValues) {
    try {
      await httpClient.post(
        '/api/auth/change-password',
        { old_password: values.oldPassword, new_password: values.newPassword },
        { _silent: true } as never,
      )
      form.reset()
      toast.success('Đã đổi mật khẩu')
    } catch (error) {
      // Lỗi hay gặp nhất là sai mật khẩu hiện tại — gắn thẳng vào ô đó thay vì
      // đẩy lên một dòng đỏ chung chung ở cuối form.
      const message = extractErrorMessage(error)
      if (message.toLowerCase().includes('hiện tại')) {
        form.setError('oldPassword', { message })
      } else {
        form.setError('root', { message })
      }
    }
  }

  const type = showPassword ? 'text' : 'password'
  const { isSubmitting } = form.formState

  return (
    <FormCard title="Đổi mật khẩu" icon={Lock} iconClassName="text-muted-foreground">
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)} className="flex flex-col gap-3">
          <FormField
            control={form.control}
            name="oldPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Mật khẩu hiện tại</FormLabel>
                <FormControl>
                  <Input type={type} autoComplete="current-password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <FormField
            control={form.control}
            name="newPassword"
            render={({ field }) => (
              <FormItem>
                <FormLabel>Mật khẩu mới</FormLabel>
                <FormControl>
                  <Input type={type} autoComplete="new-password" {...field} />
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
                <FormLabel>Xác nhận mật khẩu mới</FormLabel>
                <FormControl>
                  <Input type={type} autoComplete="new-password" {...field} />
                </FormControl>
                <FormMessage />
              </FormItem>
            )}
          />

          <div className="flex items-center gap-2">
            <Checkbox
              id="show-password"
              checked={showPassword}
              onCheckedChange={(checked) => setShowPassword(checked === true)}
            />
            <Label htmlFor="show-password" className="text-[13px] text-muted-foreground">
              Hiện mật khẩu
            </Label>
          </div>

          {form.formState.errors.root && (
            <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-destructive">
              <CircleAlert className="size-4 shrink-0" />
              {form.formState.errors.root.message}
            </div>
          )}

          <Button type="submit" disabled={isSubmitting} className="self-start">
            {isSubmitting ? <Loader2 className="size-4 animate-spin" /> : <Lock className="size-4" />}
            {isSubmitting ? 'Đang đổi…' : 'Đổi mật khẩu'}
          </Button>

          <p className="flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
            <Info className="mt-0.5 size-3.5 shrink-0" />
            <span>
              Phiên đang mở trên máy này vẫn dùng được sau khi đổi. Nếu bạn nghi ngờ tài
              khoản bị lộ, hãy báo Quản trị hệ thống để khóa các phiên còn lại.
            </span>
          </p>
        </form>
      </Form>
    </FormCard>
  )
}
