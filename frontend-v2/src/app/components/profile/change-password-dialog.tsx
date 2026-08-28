import { zodResolver } from '@hookform/resolvers/zod'
import { CircleAlert, KeyRound, Loader2 } from 'lucide-react'
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
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/shared/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'

/**
 * Đổi mật khẩu của chính mình — mở trong POPUP thay vì thẻ luôn hiện, để khối
 * "Tài khoản" gọn: chỉ hiện nút, bấm mới nhập.
 *
 * KHÔNG tự đăng xuất sau khi đổi: backend không thu hồi token nào, đá người dùng
 * ra màn đăng nhập chỉ gây phiền chứ không làm phiên nào an toàn hơn.
 */
export function ChangePasswordDialog() {
  const [open, setOpen] = useState(false)
  const [showPassword, setShowPassword] = useState(false)

  const form = useForm<ChangePasswordFormValues>({
    resolver: zodResolver(changePasswordSchema),
    defaultValues: { oldPassword: '', newPassword: '', confirmPassword: '' },
  })

  function onOpenChange(next: boolean) {
    setOpen(next)
    if (!next) {
      form.reset()
      setShowPassword(false)
    }
  }

  async function onSubmit(values: ChangePasswordFormValues) {
    try {
      await httpClient.post(
        '/api/auth/change-password',
        { old_password: values.oldPassword, new_password: values.newPassword },
        { _silent: true } as never,
      )
      toast.success('Đã đổi mật khẩu')
      onOpenChange(false)
    } catch (error) {
      // Lỗi hay gặp nhất là sai mật khẩu hiện tại — gắn thẳng vào ô đó.
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
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <KeyRound className="size-4" />
          Đổi mật khẩu
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Đổi mật khẩu</DialogTitle>
          <DialogDescription>
            Nhập mật khẩu hiện tại và mật khẩu mới. Phiên trên máy này vẫn dùng được sau khi đổi.
          </DialogDescription>
        </DialogHeader>

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
                id="change-password-show"
                checked={showPassword}
                onCheckedChange={(checked) => setShowPassword(checked === true)}
              />
              <Label htmlFor="change-password-show" className="text-[13px] text-muted-foreground">
                Hiện mật khẩu
              </Label>
            </div>

            {form.formState.errors.root && (
              <div className="flex items-center gap-2 rounded-lg border border-red-200 bg-red-50 px-3 py-2 text-[13px] text-destructive">
                <CircleAlert className="size-4 shrink-0" />
                {form.formState.errors.root.message}
              </div>
            )}

            <DialogFooter className="mt-1">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  <KeyRound className="size-4" />
                )}
                {isSubmitting ? 'Đang đổi…' : 'Đổi mật khẩu'}
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
