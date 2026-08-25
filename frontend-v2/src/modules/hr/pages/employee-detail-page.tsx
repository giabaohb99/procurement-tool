import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, Briefcase, Building2, Hash, Loader2, Save, UserCheck } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { AvatarUploader } from '@/shared/ui/avatar-uploader'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/shared/ui/form'
import { FormSection } from '@/shared/ui/form-section'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { Skeleton } from '@/shared/ui/skeleton'
import { ActiveStatusSelect } from '../components/active-status-select'
import { EmployeeAccountCard } from '../components/employee-account-card'
import { LookupSelect } from '../components/lookup-select'
import { useDepartments } from '../hooks/use-departments'
import {
  useDeleteEmployee,
  useEmployee,
  useSaveEmployee,
  useUploadEmployeeAvatar,
} from '../hooks/use-employees'
import {
  EMPTY_EMPLOYEE_FORM,
  employeeSchema,
  type EmployeeFormValues,
} from '../schemas/employee-schema'
import {
  employeeInitials,
  employeeStatusLabel,
  employeeStatusOptions,
  type EmployeeDetail,
} from '../types/employee'

/** Chi tiết hồ sơ nhân sự — form sửa trực tiếp + thẻ tài khoản đăng nhập. */
export function EmployeeDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const employeeId = Number(id)

  const { can } = usePermission()
  const canWrite = can('employee', 'write')

  const { data: employee, isLoading, isError } = useEmployee(employeeId)
  const saveEmployee = useSaveEmployee()
  const deleteEmployee = useDeleteEmployee()
  const uploadAvatar = useUploadEmployeeAvatar(employeeId)
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })

  const form = useForm<EmployeeFormValues>({
    resolver: zodResolver(employeeSchema),
    defaultValues: EMPTY_EMPLOYEE_FORM,
  })

  useEffect(() => {
    if (employee) form.reset({ ...EMPTY_EMPLOYEE_FORM, ...employee })
  }, [employee, form])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-28 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError || !employee) {
    return (
      <ErrorState
        title="Không tìm thấy nhân sự"
        description="Hồ sơ có thể đã bị xóa, hoặc bạn không có quyền xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.hr.employees)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  async function onSubmit(values: EmployeeFormValues) {
    await saveEmployee.mutateAsync({ id: employeeId, values })
  }

  async function handleDelete() {
    await deleteEmployee.mutateAsync(employeeId)
    navigate(appRoutes.hr.employees)
  }

  // Ảnh nằm trên tài khoản đăng nhập, chưa có tài khoản thì backend từ chối upload.
  const canEditAvatar = canWrite && employee.user_id > 0

  return (
    <PageContainer>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link to={appRoutes.hr.employees}>
                <ArrowLeft />
                Danh sách nhân sự
              </Link>
            </Button>

            <div className="flex items-center gap-2">
              <PermissionGate entity="employee" action="write">
                <Button type="submit" disabled={saveEmployee.isPending}>
                  {saveEmployee.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                  Lưu
                </Button>
              </PermissionGate>

              <PermissionGate entity="employee" action="delete">
                <DeleteConfirmButton
                  recordName={employee.full_name}
                  pending={deleteEmployee.isPending}
                  onConfirm={handleDelete}
                  warning="Tài khoản đăng nhập của nhân sự này sẽ bị khóa theo."
                />
              </PermissionGate>
            </div>
          </div>

          <RecordIdentityCard
            media={
              <AvatarUploader
                src={employee.avatar}
                fallback={employeeInitials(employee.full_name)}
                alt={employee.full_name}
                onUpload={canEditAvatar ? (file) => uploadAvatar.mutateAsync(file) : undefined}
                disabledHint={
                  employee.user_id
                    ? 'Ảnh đại diện'
                    : 'Nhân sự chưa có tài khoản đăng nhập nên chưa đặt được ảnh'
                }
              />
            }
            title={employee.full_name}
            chips={identityChips(employee)}
          />

          <div className="grid gap-5 lg:grid-cols-[1.4fr_1fr]">
            <Card className="gap-4 p-5">
              <FormSection title="Định danh">
                <FormField
                  control={form.control}
                  name="code"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Mã NV</FormLabel>
                      <FormControl>
                        {/* Mã dùng khắp hệ — đổi sau khi tạo sẽ vỡ tham chiếu. */}
                        <Input disabled {...field} />
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
                        <Input disabled={!canWrite} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </FormSection>

              <FormSection title="Liên hệ">
                <FormField
                  control={form.control}
                  name="email"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Email</FormLabel>
                      <FormControl>
                        <Input type="email" disabled={!canWrite} {...field} />
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
                        <Input disabled={!canWrite} {...field} />
                      </FormControl>
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </FormSection>

              <FormSection title="Công việc">
                <FormField
                  control={form.control}
                  name="department_id"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Phòng ban</FormLabel>
                      <LookupSelect
                        value={field.value}
                        onChange={field.onChange}
                        disabled={!canWrite}
                        placeholder="Chọn phòng ban"
                        emptyLabel="— Chưa gán phòng ban —"
                        fallbackLabel={employee.department_name ?? ''}
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
                        <Input disabled={!canWrite} {...field} />
                      </FormControl>
                      <FormDescription>
                        Chỉ là chức danh hiển thị trên phiếu — không phải phân quyền.
                      </FormDescription>
                      <FormMessage />
                    </FormItem>
                  )}
                />

                <FormField
                  control={form.control}
                  name="status"
                  render={({ field }) => (
                    <FormItem>
                      <FormLabel>Tình trạng làm việc</FormLabel>
                      <Select
                        onValueChange={field.onChange}
                        value={field.value}
                        disabled={!canWrite}
                      >
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
                      <ActiveStatusSelect
                        value={field.value}
                        onChange={field.onChange}
                        disabled={!canWrite}
                      />
                      <FormMessage />
                    </FormItem>
                  )}
                />
              </FormSection>
            </Card>

            <div className="space-y-5">
              <EmployeeAccountCard employeeId={employee.id} email={employee.email} />
              <AuditTimeline entity="employee" entityId={employeeId} />
            </div>
          </div>
        </form>
      </Form>
    </PageContainer>
  )
}

function identityChips(employee: EmployeeDetail): IdentityChip[] {
  const chips: IdentityChip[] = []
  if (employee.code) chips.push({ icon: Hash, text: employee.code, tone: 'code' })
  if (employee.position) chips.push({ icon: Briefcase, text: employee.position })
  if (employee.department_name) {
    chips.push({ icon: Building2, text: employee.department_name })
  }
  if (employee.status) {
    // B-03: hiện NHÃN. `status` giờ là mã, dán thẳng vào chip là người dùng đọc `official`.
    const nhan = employee.status_label || employeeStatusLabel(employee.status)
    chips.push({ icon: UserCheck, text: nhan, tone: 'ok' })
  }
  return chips
}
