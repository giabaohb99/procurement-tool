import { zodResolver } from '@hookform/resolvers/zod'
import { ArrowLeft, CircleCheck, CircleX, Hash, Loader2, Save, UserStar } from 'lucide-react'
import { useEffect } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { Skeleton } from '@/shared/ui/skeleton'
import { ActiveStatusSelect } from '../components/active-status-select'
import { DepartmentCompanyCard } from '../components/department-company-card'
import { DepartmentMembersTable } from '../components/department-members-table'
import { LookupSelect } from '../components/lookup-select'
import { useCompanies } from '../hooks/use-companies'
import {
  useDeleteDepartment,
  useDepartment,
  useDepartments,
  useSaveDepartment,
} from '../hooks/use-departments'
import { useEmployees } from '../hooks/use-employees'
import {
  EMPTY_DEPARTMENT_FORM,
  departmentSchema,
  type DepartmentFormValues,
} from '../schemas/department-schema'
import type { Department } from '../types/department'
import { DEPARTMENT_KIND_LABELS } from '../types/department'

/**
 * Chi tiết phòng ban — form sửa trực tiếp, bên dưới là bảng nhân sự thuộc phòng
 * và nhật ký thao tác. Không chia 2 cột: bảng nhân sự cần trọn chiều ngang.
 */
export function DepartmentDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const departmentId = Number(id)

  const { can } = usePermission()
  const canWrite = can('department', 'write')

  const { data: department, isLoading, isError } = useDepartment(departmentId)
  const saveDepartment = useSaveDepartment()
  const deleteDepartment = useDeleteDepartment()
  const { data: employees } = useEmployees({ page_size: 1000, is_active: true })
  const { data: companies } = useCompanies({ page_size: 1000, is_active: true })
  const { data: departments } = useDepartments({ page_size: 1000, is_active: true })

  const form = useForm<DepartmentFormValues>({
    resolver: zodResolver(departmentSchema),
    defaultValues: EMPTY_DEPARTMENT_FORM,
  })

  useEffect(() => {
    if (department) form.reset({ ...EMPTY_DEPARTMENT_FORM, ...department })
  }, [department, form])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-5 h-24 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError || !department) {
    return (
      <ErrorState
        title="Không tìm thấy phòng ban"
        description="Phòng ban có thể đã bị xóa, hoặc bạn không có quyền xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.hr.departments)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  async function onSubmit(values: DepartmentFormValues) {
    await saveDepartment.mutateAsync({ id: departmentId, values })
  }

  async function handleDelete() {
    await deleteDepartment.mutateAsync(departmentId)
    navigate(appRoutes.hr.departments)
  }

  const selectedCompanyId = form.watch('company_id')
  const managerOptions = (employees?.items ?? [])
    .filter((employee) => !selectedCompanyId || employee.company_id === selectedCompanyId)
    .map((employee) => ({
      id: employee.id,
      label: `${employee.code} — ${employee.full_name}`,
    }))

  return (
    <PageContainer>
      <Form {...form}>
        <form onSubmit={form.handleSubmit(onSubmit)}>
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            <Button variant="ghost" size="sm" asChild>
              <Link to={appRoutes.hr.departments}>
                <ArrowLeft />
                Danh sách phòng ban
              </Link>
            </Button>

            <div className="flex items-center gap-2">
              <PermissionGate entity="department" action="write">
                <Button type="submit" disabled={saveDepartment.isPending}>
                  {saveDepartment.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                  Lưu
                </Button>
              </PermissionGate>

              <PermissionGate entity="department" action="delete">
                <DeleteConfirmButton
                  recordName={department.name}
                  pending={deleteDepartment.isPending}
                  onConfirm={handleDelete}
                  warning="Nhân sự đang thuộc phòng này sẽ mất phòng ban."
                />
              </PermissionGate>
            </div>
          </div>

          <RecordIdentityCard title={department.name} chips={identityChips(department)} />

          <Card className="gap-4 p-5">
            <FormSection title="Định danh">
              <FormField
                control={form.control}
                name="code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã phòng ban</FormLabel>
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
                name="name"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Tên phòng ban</FormLabel>
                    <FormControl>
                      <Input disabled={!canWrite} {...field} />
                    </FormControl>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="issue_code"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Mã trên số hiệu văn bản</FormLabel>
                    <FormControl>
                      <Input
                        placeholder="VD: HCNS"
                        maxLength={20}
                        disabled={!canWrite}
                        {...field}
                        onChange={(event) =>
                          field.onChange(event.target.value.toUpperCase().replace(/[^A-Z0-9]/g, ''))
                        }
                      />
                    </FormControl>
                    <FormDescription>
                      Chỉ dùng chữ hoa và số; được ghép vào số hiệu của phòng chức năng.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="kind"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Loại đơn vị</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={field.onChange}
                      items={Object.entries(DEPARTMENT_KIND_LABELS).map(([id, label]) => ({
                        id: Number(id),
                        label,
                      }))}
                      placeholder="Chọn loại đơn vị"
                      disabled={!canWrite}
                    />
                    <FormDescription>
                      Chỉ “Phòng chức năng” xuất hiện trong số hiệu văn bản.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>

            <FormSection title="Cơ cấu tổ chức">
              <FormField
                control={form.control}
                name="company_id"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Pháp nhân gốc</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={(companyId) => {
                        field.onChange(companyId)
                        form.setValue('manager_id', 0)
                      }}
                      items={(companies?.items ?? []).map((company) => ({
                        id: company.id,
                        label: `${company.issue_code || company.code} — ${company.name}`,
                      }))}
                      placeholder="Chọn pháp nhân gốc"
                      disabled={!canWrite}
                    />
                    <FormDescription>
                      Dòng pháp nhân gốc luôn được giữ trong cấu hình áp dụng bên dưới.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />

              <FormField
                control={form.control}
                name="parent"
                render={({ field }) => (
                  <FormItem>
                    <FormLabel>Phòng ban cấp trên</FormLabel>
                    <LookupSelect
                      value={field.value}
                      onChange={field.onChange}
                      items={(departments?.items ?? [])
                        .filter((item) => item.id !== departmentId)
                        .map((item) => ({ id: item.id, label: `${item.code} — ${item.name}` }))}
                      placeholder="Chọn phòng ban cấp trên"
                      emptyLabel="— Phòng ban gốc —"
                      disabled={!canWrite}
                    />
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
                      disabled={!canWrite}
                      placeholder="Chọn nhân sự"
                      emptyLabel="— Chưa chỉ định —"
                      items={managerOptions}
                      //  Trưởng bộ phận CÓ THỂ nằm ngoài `managerOptions` một
                      //  cách hợp lệ: danh sách lọc theo pháp nhân gốc, mà dữ
                      //  liệu cũ có phòng ở pháp nhân này lại giữ trưởng phòng
                      //  của pháp nhân khác. Không có nhãn dự phòng thì ô hiện
                      //  trống, đọc thành «chưa chỉ định» — sai hẳn.
                      fallbackLabel={department.manager_name ?? undefined}
                    />
                    <FormDescription>
                      Người duyệt/ký thay mặt phòng ban trong luồng mua hàng.
                    </FormDescription>
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
                      disabled={!canWrite}
                    />
                    <FormDescription>
                      Ẩn phòng ban đã giải thể; dữ liệu cũ vẫn giữ nguyên.
                    </FormDescription>
                    <FormMessage />
                  </FormItem>
                )}
              />
            </FormSection>
          </Card>
        </form>
      </Form>

      <div className="mt-5 space-y-5">
        <DepartmentCompanyCard
          departmentId={department.id}
          primaryCompanyId={department.company_id}
          canWrite={canWrite}
        />
        <DepartmentMembersTable departmentId={department.id} managerId={department.manager_id} />
        <AuditTimeline entity="department" entityId={departmentId} />
      </div>
    </PageContainer>
  )
}

function identityChips(department: Department): IdentityChip[] {
  const chips: IdentityChip[] = []
  if (department.code) chips.push({ icon: Hash, text: department.code, tone: 'code' })
  if (department.issue_code) {
    chips.push({ icon: Hash, text: `Số hiệu: ${department.issue_code}`, tone: 'code' })
  }
  if (department.manager_name) {
    chips.push({ icon: UserStar, text: `Trưởng BP: ${department.manager_name}` })
  }
  chips.push(
    department.is_active
      ? { icon: CircleCheck, text: 'Hoạt động', tone: 'ok' }
      : { icon: CircleX, text: 'Đã ẩn', tone: 'muted' },
  )
  return chips
}
