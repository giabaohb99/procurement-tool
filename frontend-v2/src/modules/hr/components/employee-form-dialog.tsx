import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
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
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/shared/ui/select'
import { useDepartments } from '../hooks/use-departments'
import { useSaveEmployee } from '../hooks/use-employees'
import {
  EMPTY_EMPLOYEE_FORM,
  employeeSchema,
  type EmployeeFormValues,
} from '../schemas/employee-schema'
import { employeeStatusOptions, type Employee } from '../types/employee'
import { ActiveStatusSelect } from './active-status-select'
import { LookupSelect } from './lookup-select'

interface EmployeeFormDialogProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Có = sửa, không có = thêm mới. */
  employee?: Employee | null
}

/** Form thêm/sửa hồ sơ nhân sự. */
export function EmployeeFormDialog({
  open,
  onOpenChange,
  employee,
}: EmployeeFormDialogProps) {
  const saveEmployee = useSaveEmployee()
  // Đủ để phủ hết phòng ban của một doanh nghiệp cỡ này; không cần tìm kiếm động.
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })

  const form = useForm<EmployeeFormValues>({
    resolver: zodResolver(employeeSchema),
    defaultValues: EMPTY_EMPLOYEE_FORM,
  })

  // Dialog không unmount giữa các lần mở nên phải nạp lại giá trị mỗi lần mở,
  // nếu không sẽ thấy dữ liệu của bản ghi trước.
  useEffect(() => {
    if (!open) return
    form.reset(employee ? { ...EMPTY_EMPLOYEE_FORM, ...employee } : EMPTY_EMPLOYEE_FORM)
  }, [open, employee, form])

  async function onSubmit(values: EmployeeFormValues) {
    await saveEmployee.mutateAsync({ id: employee?.id, values })
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{employee ? 'Sửa hồ sơ nhân sự' : 'Thêm nhân sự'}</DialogTitle>
          <DialogDescription>
            Chức vụ ở đây chỉ là chức danh hiển thị trên phiếu — quyền thật của tài
            khoản đặt ở màn "Phân quyền tài khoản".
          </DialogDescription>
        </DialogHeader>

        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã NV</FormLabel>
                    <FormControl>
                      {/* Mã là định danh dùng khắp hệ, đổi sau khi tạo sẽ vỡ tham chiếu. */}
                      <Input
                        placeholder="Để trống để hệ thống tự sinh"
                        disabled={!!employee}
                        {...field}
                      />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="full_name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Họ tên</FormLabel>
                    <FormControl>
                      <Input placeholder="Nguyễn Văn A" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="email"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Email</FormLabel>
                    <FormControl>
                      <Input type="email" {...field} />
                    </FormControl>
                    <FormDescription>
                      Cũng là tên đăng nhập — đổi email KHÔNG tự đổi tài khoản đã cấp.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="phone"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Số điện thoại</FormLabel>
                    <FormControl>
                      <Input {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="department_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phòng ban</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={field.onChange}
                      placeholder="Chọn phòng ban"
                      emptyLabel="— Chưa gán phòng ban —"
                      items={(departments?.items ?? []).map((d) => ({
                        id: d.id,
                        label: d.name,
                      }))}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="position"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vị trí / Chức vụ</FormLabel>
                    <FormControl>
                      <Input placeholder="VD: Trưởng phòng mua hàng" {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              <FormField
                control={form.control}
                name="status"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tình trạng làm việc</FormLabel>
                    <Select onValueChange={field.onChange} value={field.value}>
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {employeeStatusOptions(field.value).map((item) => (
                          <SelectItem key={item.value} value={item.value}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="is_active"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Trạng thái hồ sơ</FormLabel>
                    <ActiveStatusSelect value={field.value} onChange={field.onChange} />
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
                Hủy
              </Button>
              <Button type="submit" disabled={saveEmployee.isPending}>
                {saveEmployee.isPending && <Loader2 className="size-4 animate-spin" />}
                Lưu
              </Button>
            </DialogFooter>
          </form>
        </Form>
      </DialogContent>
    </Dialog>
  )
}
