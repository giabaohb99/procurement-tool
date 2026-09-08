import { zodResolver } from '@hookform/resolvers/zod'
import { Loader2 } from 'lucide-react'
import { useEffect, useMemo } from 'react'
import { useForm } from 'react-hook-form'

import { Button } from '@/shared/ui/button'
import { DatePicker } from '@/shared/ui/date-picker'
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
import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import { useJobPositions } from '../hooks/use-job-positions'
import { useSaveEmployee } from '../hooks/use-employees'
import {
  EMPTY_EMPLOYEE_FORM,
  employeeFormValues,
  employeeSchema,
  type EmployeeFormValues,
} from '../schemas/employee-schema'
import {
  EMPLOYEE_GENDER_OPTIONS,
  employeeStatusOptions,
  type Employee,
} from '../types/employee'
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
  //  `enabled: open` — hộp thoại KHÔNG unmount giữa các lần mở, nên không tắt
  //  thì hai danh sách này nạp ngay lúc vào màn danh sách, trước cả khi ai bấm
  //  «Thêm mới». Người thiếu `company.read` còn ăn toast 403 chẳng liên quan.
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: open })
  //  Danh mục Chức vụ (duoc-CR-320) — cùng luật `enabled` với danh sách pháp
  //  nhân ở trên, cộng thêm chốt quyền: vai trò cũ trên hệ đang chạy KHÔNG tự
  //  có khóa `job_position` (D-018), mà gọi khi thiếu quyền là một toast 403
  //  bật lên ngay khi bấm «Thêm mới».
  const { can } = usePermission()
  const { data: positions } = useJobPositions(open && can('job_position', 'read'))
  const positionOptions = useMemo(
    () => (positions?.items ?? []).map((p) => ({ id: p.id, label: p.name })),
    [positions],
  )

  const form = useForm<EmployeeFormValues>({
    resolver: zodResolver(employeeSchema),
    defaultValues: EMPTY_EMPLOYEE_FORM,
  })

  //  Phòng ban lọc theo PHÁP NHÂN đang chọn — chưa chọn pháp nhân thì hiện hết.
  //  Không lọc thì hồ sơ ra đời đã lệch: công ty A, phòng ban của công ty B, và
  //  không màn nào báo cho tới lúc phạm vi dữ liệu chạy sai.
  const companyId = form.watch('company_id')
  const departmentOptions = useMemo(() => {
    const rows = departments?.items ?? []
    return rows
      .filter((d) => !companyId || d.company_id === companyId)
      .map((d) => ({ id: d.id, label: d.name }))
  }, [departments, companyId])

  // Dialog không unmount giữa các lần mở nên phải nạp lại giá trị mỗi lần mở,
  // nếu không sẽ thấy dữ liệu của bản ghi trước.
  useEffect(() => {
    if (!open) return
    form.reset(employeeFormValues(employee))
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
              {/*  PHÁP NHÂN — hỏi NGAY ở form tạo (C2). Hồ sơ không gắn pháp
                   nhân thì phạm vi dữ liệu của người đó rỗng ngay từ đầu, mà
                   màn chi tiết CỐ Ý để ô này chỉ xem (đổi pháp nhân là đổi tập
                   dữ liệu họ đọc được) — nên đây là chỗ duy nhất đặt được nó. */}
              <FormField
                control={form.control}
                name="company_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pháp nhân</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={(v) => {
                        field.onChange(v)
                        //  Đổi pháp nhân thì BỎ phòng ban đang chọn: phòng của
                        //  pháp nhân cũ không còn hợp lệ, mà để nguyên thì hồ sơ
                        //  ra đời đã lệch — công ty A, phòng ban của công ty B.
                        if (v !== field.value) form.setValue('department_id', 0)
                      }}
                      placeholder="Chọn pháp nhân"
                      emptyLabel="— Chưa gán pháp nhân —"
                      items={(companies?.items ?? []).map((c) => ({ id: c.id, label: c.name }))}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />

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
                      items={departmentOptions}
                    />
                    <FormMessage />
                  </FormItem>
                )}
              />
            </div>

            <div className="grid gap-4 sm:grid-cols-2">
              {/*  Ô CHỌN từ danh mục Chức vụ (duoc-CR-320), không gõ tay nữa.
                   Danh mục rỗng — hoặc người tạo hồ sơ không có quyền đọc nó —
                   thì vẫn tạo được hồ sơ và để trống ô này; chức vụ điền sau ở
                   màn chi tiết. Chặn ở đây là chặn đúng việc "khai nhanh một
                   người mới", thứ cả form này sinh ra để làm. */}
              <FormField
                control={form.control}
                name="position_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Vị trí / Chức vụ</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={field.onChange}
                      placeholder="Chọn chức vụ"
                      emptyLabel="— Chưa gán chức vụ —"
                      items={positionOptions}
                    />
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

            {/*  Ba ô cuối của form TẠO NHANH (C2). Cố ý dừng ở đây, không hỏi
                 tiếp 20 ô còn lại của hồ sơ: bài học của HrOnline là bắt điền đủ
                 30+ ô ngay từ đầu thì không ai nhập. Phần còn lại điền dần ở màn
                 chi tiết, nơi có đủ 5 tab. */}
            <div className="grid gap-4 sm:grid-cols-3">
              <FormField
                control={form.control}
                name="hire_date"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ngày vào làm</FormLabel>
                    <DatePicker value={field.value} onChange={field.onChange} />
                    <FormDescription>Mốc tính thâm niên (ngày phép cộng thêm).</FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="date_of_birth"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Ngày sinh</FormLabel>
                    <DatePicker value={field.value} onChange={field.onChange} />
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="gender"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Giới tính</FormLabel>
                    <Select
                      onValueChange={(v) => field.onChange(Number(v))}
                      value={String(field.value)}
                    >
                      <FormControl>
                        <SelectTrigger className="w-full">
                          <SelectValue />
                        </SelectTrigger>
                      </FormControl>
                      <SelectContent>
                        {EMPLOYEE_GENDER_OPTIONS.map((item) => (
                          <SelectItem key={item.value} value={String(item.value)}>
                            {item.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
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
