import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2, Pencil, Save } from 'lucide-react'
import { useRef, useState } from 'react'
import { useForm } from 'react-hook-form'

import { useUpdateMyContact } from '@/modules/hr/hooks/use-my-contact'
import {
  selfContactSchema,
  toSelfContactFormValues,
  toSelfContactPayload,
  type SelfContactFormValues,
} from '@/modules/hr/schemas/self-contact-schema'
import type { Employee } from '@/modules/hr/types/employee'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Form, FormControl, FormField, FormItem, FormLabel, FormMessage } from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'

interface SelfContactDialogProps {
  employee: Employee
}

/**
 * Nút «Sửa» + hộp thoại TỰ SỬA LIÊN HỆ (bao-CR-508) — số điện thoại và hai địa
 * chỉ của chính mình. Lưu là áp ngay, không báo phòng Nhân sự; backend ghi nhật
 * ký như mọi lần sửa hồ sơ khác.
 *
 * ⚠️ Chặn bấm đúp bằng `useRef`, KHÔNG bằng `disabled={isPending}` (bẫy thứ tư
 * của CLAUDE.md): `disabled` là state React, chỉ đúng ở lần render sau, nên
 * năm cú bấm liền tay vẫn ra năm request và năm dòng nhật ký.
 */
export function SelfContactDialog({ employee }: SelfContactDialogProps) {
  const [open, setOpen] = useState(false)
  const submittingRef = useRef(false)
  const updateContact = useUpdateMyContact(employee.id)

  const form = useForm<SelfContactFormValues>({
    resolver: zodResolver(selfContactSchema),
    defaultValues: toSelfContactFormValues(employee),
  })

  function onOpenChange(next: boolean) {
    //  Mở ra thì nạp lại từ hồ sơ MỚI NHẤT — sửa xong lần trước, dữ liệu đã
    //  nạp lại, mà form vẫn giữ giá trị lúc dựng thì lần mở sau hiện số cũ.
    if (next) form.reset(toSelfContactFormValues(employee))
    setOpen(next)
  }

  async function onSubmit(values: SelfContactFormValues) {
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      await updateContact.mutateAsync(toSelfContactPayload(values))
      setOpen(false)
    } catch {
      //  http-client đã toast lỗi (cửa ghi) — giữ hộp mở để người dùng sửa tiếp.
    } finally {
      submittingRef.current = false
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <Button type="button" variant="outline" size="sm" onClick={() => onOpenChange(true)}>
        <Pencil className="size-4" />
        Sửa
      </Button>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>Sửa thông tin liên hệ</DialogTitle>
          <DialogDescription>
            Thay đổi được áp dụng ngay và được ghi vào lịch sử hồ sơ nhân sự của bạn.
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          {/*  Dựng handler NGAY TRONG sự kiện, không lúc render: `onSubmit` đóng
               trên `submittingRef`, truyền hàm-đọc-ref vào lúc render là thứ
               `react-hooks/refs` cảnh báo (cùng lối `employee-detail-page`). */}
          <form
            onSubmit={(event) => void form.handleSubmit(onSubmit)(event)}
            className="flex flex-col gap-3"
          >
            <FormField
              control={form.control}
              name="phone"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Số điện thoại</FormLabel>
                  <FormControl>
                    <Input type="tel" autoComplete="tel" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="permanent_address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Địa chỉ thường trú</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />
            <FormField
              control={form.control}
              name="current_address"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Địa chỉ hiện nay (tạm trú)</FormLabel>
                  <FormControl>
                    <Input {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter className="mt-2">
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={updateContact.isPending}>
                {updateContact.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
