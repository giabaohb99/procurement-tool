import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  Briefcase,
  Building2,
  CalendarDays,
  Hash,
  IdCard,
  Loader2,
  Phone,
  Save,
  UserCheck,
  UserCog,
} from 'lucide-react'
import { useEffect, useRef } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { useBackTarget } from '@/shared/hooks/use-back-target'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { AvatarUploader } from '@/shared/ui/avatar-uploader'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { Form } from '@/shared/ui/form'
import { PageContainer } from '@/shared/ui/page-container'
import { RecordIdentityCard, type IdentityChip } from '@/shared/ui/record-identity-card'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/shared/ui/tabs'
import { EmployeeAccountCard } from '../components/employee-account-card'
import { EmployeeDepartmentCard } from '../components/employee-department-card'
import { EmployeeSignatureCard } from '../components/employee-signature-card'
import { EmployeeTabContact } from '../components/employee-tab-contact'
import { EmployeeTabDocuments } from '../components/employee-tab-documents'
import { EmployeeTabGeneral } from '../components/employee-tab-general'
import { EmployeeTabLeave } from '../components/employee-tab-leave'
import { useCanReadSensitive } from '../hooks/use-employee-profile'
import { useDepartments } from '../hooks/use-departments'
import {
  useDeleteEmployee,
  useEmployee,
  useEmployees,
  useSaveEmployee,
  useUploadEmployeeAvatar,
} from '../hooks/use-employees'
import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  employeeProfileFormValues,
  employeeProfileSchema,
  pickWritableProfile,
  type EmployeeProfileFormValues,
} from '../schemas/employee-schema'
import { employeeInitials, employeeStatusLabel, type EmployeeDetail } from '../types/employee'
import { firstInvalidTab } from '../utils/profile-field-tab'

/**
 * Chi tiết hồ sơ nhân sự — 5 TAB (duoc-CR-314 Đợt 2).
 *
 * Hồ sơ có hơn 30 ô sau khi mở rộng; dồn hết vào một trang cuộn thì không ai
 * tìm được ô mình cần. Bốn tab đầu chia theo NGƯỜI DÙNG chứ không theo bảng:
 * *Chung* (ai cũng xem) · *Liên hệ & Ngân hàng* + *Giấy tờ & BHXH* (việc của
 * Nhân sự) · *Quỹ phép* (lối sang phân hệ Nghỉ phép) · *Tài khoản*.
 *
 * ⚠️ **MỘT form cho cả bốn tab đầu.** `Tabs` của Radix hủy mount nội dung tab
 * ẩn, nhưng `react-hook-form` giữ giá trị trong `useForm` chứ không trong DOM —
 * nên sửa ở tab Chung rồi sang tab khác bấm Lưu vẫn gửi đủ. Tách bốn form là
 * bốn nút Lưu và bốn lần người dùng quên bấm.
 *
 * ⚠️ Hai bảng con (người báo tin, hộ gia đình) và hai ảnh CCCD **KHÔNG** nằm
 * trong form này — chúng đi cửa API riêng và có nút Lưu riêng, vì backend gác
 * chúng bằng một khóa quyền khác.
 */
export function EmployeeDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const employeeId = Number(id)

  const { can } = usePermission()
  const { user: currentUser } = useAuth()
  const canWrite = can('employee', 'write')
  const canReadSensitive = useCanReadSensitive(employeeId)

  const [tab, setTab] = useUrlParamState('tab', 'general')
  const backTarget = useBackTarget(appRoutes.hr.employees)

  const { data: employee, isLoading, isError } = useEmployee(employeeId)
  const saveEmployee = useSaveEmployee()
  const deleteEmployee = useDeleteEmployee()
  const uploadAvatar = useUploadEmployeeAvatar(employeeId)
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  //  Danh bạ để chọn NGƯỜI QUẢN LÝ TRỰC TIẾP. Lấy đủ một lượt — công ty cỡ này
  //  vài trăm người, không cần ô tìm động.
  const { data: colleagues } = useEmployees({ page_size: 500, is_active: true })

  const form = useForm<EmployeeProfileFormValues>({
    resolver: zodResolver(employeeProfileSchema),
    defaultValues: EMPTY_EMPLOYEE_PROFILE_FORM,
  })

  //  Cờ «đang gửi» đổi NGAY trong tick — xem `onSubmit`.
  const submittingRef = useRef(false)

  useEffect(() => {
    if (employee) form.reset(employeeProfileFormValues(employee))
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

  async function onSubmit(values: EmployeeProfileFormValues) {
    //  ⚠️ Chặn GỬI HAI LẦN bằng ref, không dựa vào `disabled={isPending}`.
    //
    //  `isPending` là state React nên chỉ đúng ở lần render SAU. Bấm đúp — hay
    //  bấm liên tiếp trong cùng một tick — thì cả hai lần bấm đều thấy nút còn
    //  bật. Bấm 5 lần liền tay ra **5 `PATCH`** (dựng lại được trên trình duyệt
    //  thật 08/09/2026), tức 5 dòng «Cập nhật» trong lịch sử thao tác cho một
    //  lần lưu — làm nhiễu đúng cái nhật ký vừa được đầu tư ở bao-CR-311.
    //
    //  Ref đổi NGAY trong cùng tick nên nó chặn được, còn `disabled` giữ vai
    //  trò báo hiệu cho người dùng.
    //
    //  ⚠️ Lỗ này là của KHUÔN CHUNG (`disabled={mutation.isPending}` dùng khắp
    //  các màn chi tiết), không riêng màn này. Ở đây vá khu trú; sửa cả khuôn
    //  là việc riêng, cần rà từng màn.
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      //  Bỏ các ô NHẠY CẢM khi người lưu không được xem chúng — backend đã che
      //  nên form đang cầm chuỗi RỖNG, gửi lên là ghi đè rỗng đè lên số tài
      //  khoản ngân hàng thật. Lý lẽ đầy đủ ở `pickWritableProfile`.
      await saveEmployee.mutateAsync({
        id: employeeId,
        values: pickWritableProfile(values, canReadSensitive),
      })
    } finally {
      submittingRef.current = false
    }
  }

  /**
   * Submit bị chặn vì còn ô sai — NHẢY tới tab chứa ô đó rồi nói ra.
   *
   * Không có hàm này thì lỗi ở tab ẩn = im lặng tuyệt đối (xem ghi chú ở
   * `<form>`). Chuyển tab TRƯỚC khi toast, để lúc người dùng đọc xong câu thông
   * báo thì ô đỏ đã nằm sẵn trên màn hình.
   */
  function onInvalid(errors: Record<string, unknown>) {
    const first = firstInvalidTab(errors)
    if (!first) return
    setTab(first.tab)
    toast.error('Còn ô chưa hợp lệ. Đã chuyển tới tab có ô đó.')
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
        {/*  Dựng handler NGAY TRONG sự kiện, không dựng lúc render: `onSubmit`
             đóng trên `submittingRef`, mà truyền một hàm-đọc-ref vào lúc render là
             thứ `react-hooks/refs` cảnh báo. Ở đây `handleSubmit` chỉ được gọi
             khi người dùng bấm, nên không có gì đọc ref trong lúc vẽ. */}
        <form onSubmit={(event) => void form.handleSubmit(onSubmit, onInvalid)(event)}>
          {/*  ⚠️ `onInvalid` là BẮT BUỘC với biểu mẫu chia tab, không phải tiện ích.

               Radix hủy mount nội dung tab ẩn, nên câu lỗi của một ô ở tab khác
               không có chỗ nào để hiện ra. Không có nhánh này thì bấm Lưu là
               **không có gì xảy ra**: không toast, không lỗi trên màn, không
               một lời gọi API nào — nút Lưu đọc ra như bị hỏng. Dựng lại được
               trên trình duyệt thật 08/09/2026. */}
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            {/*  ⚠️ Đích của nút lùi phụ thuộc CHỖ ĐẾN. Hồ sơ này mở được từ tab
                 «Người đang giữ» của một chức vụ hay bảng thành viên của một
                 phòng ban; trỏ cứng về danh sách nhân sự là ném người dùng sang
                 màn họ chưa từng đứng, mất luôn tab và bộ lọc đang đặt. Trên
                 điện thoại đây là nút lùi DUY NHẤT trong tầm mắt.
                 Nhãn đổi theo đích — «Danh sách nhân sự» mà bấm ra chức vụ thì
                 nút nói dối. Xem `use-back-target.ts`. */}
            <Button variant="ghost" size="sm" asChild>
              <Link to={backTarget.url}>
                <ArrowLeft />
                {backTarget.fromElsewhere ? 'Quay lại' : 'Danh sách nhân sự'}
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
                  warning="Tài khoản đăng nhập sẽ bị khóa. Người báo tin và thành viên hộ gia đình cũng bị xóa theo."
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

          <Tabs value={tab} onValueChange={setTab} className="mt-5">
            <TabsList>
              <TabsTrigger value="general">Chung</TabsTrigger>
              <TabsTrigger value="contact">
                <Phone className="size-4" />
                Liên hệ &amp; Ngân hàng
              </TabsTrigger>
              <TabsTrigger value="documents">
                <IdCard className="size-4" />
                Giấy tờ &amp; BHXH
              </TabsTrigger>
              <TabsTrigger value="leave">
                <CalendarDays className="size-4" />
                Quỹ phép
              </TabsTrigger>
              <TabsTrigger value="account">
                <UserCog className="size-4" />
                Tài khoản
              </TabsTrigger>
            </TabsList>

            <TabsContent value="general" className="mt-5">
              <EmployeeTabGeneral
                employee={employee}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
                departments={departments?.items ?? []}
                colleagues={(colleagues?.items ?? [])
                  //  Bỏ CHÍNH MÌNH khỏi ô chọn: tự làm quản lý của mình là một
                  //  vòng, backend chặn bằng 400 — thà đừng bày ra để chọn.
                  .filter((e) => e.id !== employeeId)
                  .map((e) => ({ id: e.id, label: `${e.full_name} (${e.code})` }))}
              />
            </TabsContent>

            <TabsContent value="contact" className="mt-5">
              <EmployeeTabContact
                employeeId={employeeId}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
              />
            </TabsContent>

            <TabsContent value="documents" className="mt-5">
              <EmployeeTabDocuments
                employee={employee}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
              />
            </TabsContent>

            <TabsContent value="leave" className="mt-5">
              <EmployeeTabLeave employee={employee} />
            </TabsContent>

            <TabsContent value="account" className="mt-5">
              {/* Kiêm nhiệm và tài khoản là hai nửa của câu «người này thấy được gì». */}
              <div className="grid items-stretch gap-5 lg:grid-cols-2">
                <EmployeeDepartmentCard
                  employeeId={employee.id}
                  companyId={employee.company_id}
                  primaryDepartmentId={employee.department_id}
                  canWrite={canWrite}
                  isSelf={currentUser?.employee_id === employee.id}
                  className="h-full"
                />
                <EmployeeAccountCard
                  employeeId={employee.id}
                  email={employee.email}
                  className="h-full"
                />
              </div>

              <EmployeeSignatureCard
                employeeId={employee.id}
                signature={employee.signature}
                canEdit={canWrite}
                hasAccount={employee.user_id > 0}
                className="mt-5"
              />
            </TabsContent>
          </Tabs>

          {/* Ngoài mọi TabsContent — lịch sử thao tác đúng ở mọi tab. */}
          <Card className="mt-5 gap-4 p-5">
            <SectionHeading>Lịch sử thao tác</SectionHeading>
            <AuditTimeline entity="employee" entityId={employeeId} />
          </Card>
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
  //  Người quản lý trực tiếp lên tận thẻ tiêu đề: đây là ô mà bộ máy duyệt đọc,
  //  nên nó đáng được nhìn thấy mà không phải mở tab nào.
  if (employee.direct_manager_name) {
    chips.push({ icon: UserCog, text: `QL: ${employee.direct_manager_name}` })
  }
  if (employee.status) {
    // B-03: hiện NHÃN. `status` giờ là mã, dán thẳng vào chip là người dùng đọc `official`.
    const statusLabel = employee.status_label || employeeStatusLabel(employee.status)
    chips.push({ icon: UserCheck, text: statusLabel, tone: 'ok' })
  }
  return chips
}
