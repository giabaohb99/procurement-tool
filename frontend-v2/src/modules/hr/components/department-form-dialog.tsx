import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { Input } from '@/shared/ui/input'
import { useSaveDepartment } from '../hooks/use-departments'
import { useEmployees } from '../hooks/use-employees'
import {
  EMPTY_DEPARTMENT_FORM,
  departmentSchema,
  type DepartmentFormValues,
} from '../schemas/department-schema'
import type { Department } from '../types/department'
import { ActiveStatusSelect } from './active-status-select'
import { LookupSelect } from './lookup-select'

interface DepartmentFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  department?: Department | null
}

/** Form thêm/sửa phòng ban. */
export function DepartmentFormDialog({
  open,
  onOpenChange,
  department,
}: DepartmentFormDialogProps) {
  const saveDepartment = useSaveDepartment()
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })

  const form = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentSchema),
    defaultValues: EMPTY_DEPARTMENT_FORM,
  })

  useEffect(() => {
    if (!open) return
    form.reset(
      department ? { ...EMPTY_DEPARTMENT_FORM, ...department } : EMPTY_DEPARTMENT_FORM,
    )
  }, [open, department, form])

  async function onSubmit(values: DepartmentFormValues) {
    await saveDepartment.mutateAsync({ id: department?.id, values })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-lg">
        <DialogHeader>
          <DialogTitle>{department ? 'Sửa phòng ban' : 'Thêm phòng ban'}</DialogTitle>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã phòng ban</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="Để trống để hệ thống tự sinh"
                        disabled={!!department}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trạng thái</FormLabel>
                    <ActiveStatusSelect
                      value={field.value}
                      onChange={field.onChange}
                      onLabel="Hoạt động"
                      offLabel="Đã ẩn"
                    />
                    <FormDescription>
                      Ẩn phòng ban đã giải thể; dữ liệu cũ vẫn giữ nguyên.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <FormField
              control={form.control}
              name="name"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Tên phòng ban</FormLabel>
                  <FormControl>
                    <Input placeholder="VD: Phòng Mua hàng" {...field} />
                  </FormControl>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="manager_id"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Trưởng bộ phận</FormLabel>
                  <LookupSelect
                    value={field.value}
                    onChange={field.onChange}
                    placeholder="Chọn nhân sự"
                    emptyLabel="— Chưa chỉ định —"
                    items={(employees?.items ?? []).map((e) => ({
                      id: e.id,
                      label: `${e.code} — ${e.full_name}`,
                    }))}
                  />
                  <FormDescription>
                    Người duyệt/ký thay mặt phòng ban trong luồng mua hàng.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={saveDepartment.isPending}>
                {saveDepartment.isPending && <Loader2 className="size-4 animate-spin" />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
