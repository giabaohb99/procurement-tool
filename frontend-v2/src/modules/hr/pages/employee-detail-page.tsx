import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  Briefcase,
  Building2,
  CalendarDays,
  FileCheck2,
  FileSignature,
  Hash,
  History,
  IdCard,
  Layers,
  Loader2,
  Phone,
  Printer,
  Save,
  UserCheck,
  UserCog,
} from 'lucide-react'
import { useEffect } from 'react'
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
import { LoginSessionUserCard } from '@/modules/system/components/login-session-user-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { EmployeeAccountCard } from '../components/employee-account-card'
import { EmployeePendingChangeRequestBanner } from '../components/employee-pending-change-request-banner'
import { EmployeePendingWorkConfirmDialog } from '../components/employee-pending-work-confirm-dialog'
import { EmployeeCompanyChangeConcurrentDialog } from '../components/employee-company-change-concurrent-dialog'
import { EmployeeKeepOldDepartmentDialog } from '../components/employee-keep-old-department-dialog'
import { EmployeeSignatureCard } from '../components/employee-signature-card'
import { EmployeeTabConcurrent } from '../components/employee-tab-concurrent'
import { EmployeeTabContact } from '../components/employee-tab-contact'
import { EmployeeTabDocuments } from '../components/employee-tab-documents'
import { EmployeeTabGeneral } from '../components/employee-tab-general'
import { EmployeeTabLaborContracts } from '../components/employee-tab-labor-contracts'
import { EmployeeTabLeave } from '../components/employee-tab-leave'
import { EmployeeWorkScheduleCard } from '../components/employee-work-schedule-card'
import { EmployeeTabWorkDecisions } from '../components/employee-tab-work-decisions'
import { EmployeeTabWorkHistory } from '../components/employee-tab-work-history'
import { useCanReadSensitive } from '../hooks/use-employee-profile'
import { useEmployeeProfileSaveFlow } from '../hooks/use-employee-profile-save-flow'
import { useCompanies } from '../hooks/use-companies'
import { useDepartments } from '../hooks/use-departments'
import {
  useDeleteEmployee,
  useEmployee,
  useEmployees,
  useUploadEmployeeAvatar,
} from '../hooks/use-employees'
import {
  EMPTY_EMPLOYEE_PROFILE_FORM,
  employeeProfileFormValues,
  employeeProfileSchema,
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
  //  Lương là dữ liệu nhạy cảm: không có quyền thì không dựng cả tab lẫn nội dung (tránh 403 lúc mount).
  const canReadLaborContract = can('labor_contract', 'read')
  const canReadSensitive = useCanReadSensitive(employeeId)

  const [urlTab, setTab] = useUrlParamState('tab', 'general')
  //  Mở thẳng `?tab=labor-contracts` khi không có quyền thì về tab Chung, không để khung trống.
  const tab = urlTab === 'labor-contracts' && !canReadLaborContract ? 'general' : urlTab
  const backTarget = useBackTarget(appRoutes.hr.employees)

  const { data: employee, isLoading, isError } = useEmployee(employeeId)
  const deleteEmployee = useDeleteEmployee()
  const uploadAvatar = useUploadEmployeeAvatar(employeeId)
  const { data: departments } = useDepartments({ page_size: 500, is_active: true })
  //  Danh bạ để chọn NGƯỜI QUẢN LÝ TRỰC TIẾP. Lấy đủ một lượt — công ty cỡ này
  //  vài trăm người, không cần ô tìm động.
  const { data: colleagues } = useEmployees({ page_size: 500, is_active: true })
  //  Cùng tham số với ô Pháp nhân ở tab Chung nên dùng chung bộ đệm — chỉ để gọi TÊN công ty mới trong hộp đổi pháp nhân.
  const { data: companies } = useCompanies({ page_size: 200, is_active: true }, { enabled: can('company', 'read') })

  const form = useForm<EmployeeProfileFormValues>({
    resolver: zodResolver(employeeProfileSchema),
    defaultValues: EMPTY_EMPLOYEE_PROFILE_FORM,
  })
  //  Ba hộp hỏi trước khi lưu (giữ phòng cũ · kiêm nhiệm ở công ty cũ · nghỉ việc) + chặn bấm đúp — xem hook.
  const saveFlow = useEmployeeProfileSaveFlow({ employeeId, employee, form, canReadSensitive })
  const { saveEmployee } = saveFlow

  //  ⚠️ `keepDirtyValues` — `employee` đổi không chỉ lúc mở trang: tải ảnh CCCD /
  //  ảnh đại diện / chữ ký hay "Áp" một dòng quá trình công tác đều làm hồ sơ
  //  tải lại. Reset trần thì mọi ô đang gõ dở ở mọi tab biến mất, im lặng
  //  (duoc-CR-627, dựng lại được trên trình duyệt). Đừng đổi thành "chỉ reset khi
  //  đổi id": form gửi lại mọi ô, lần Lưu sau sẽ đè phòng ban/chức vụ vừa "Áp".
  useEffect(() => {
    if (employee) form.reset(employeeProfileFormValues(employee), { keepDirtyValues: true })
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

  function departmentName(id: number, fallback?: string | null) {
    return departments?.items.find((d) => d.id === id)?.name ?? fallback ?? `Phòng #${id}`
  }

  function companyName(id: number, fallback?: string | null) {
    return companies?.items.find((c) => c.id === id)?.name ?? fallback ?? `Công ty #${id}`
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
        {/*  Dựng handler NGAY TRONG sự kiện, không dựng lúc render: `saveFlow.onSubmit`
             đóng trên ref chặn bấm đúp, mà truyền một hàm-đọc-ref vào lúc render là
             thứ `react-hooks/refs` cảnh báo. Ở đây `handleSubmit` chỉ được gọi
             khi người dùng bấm, nên không có gì đọc ref trong lúc vẽ. */}
        <form onSubmit={(event) => void form.handleSubmit(saveFlow.onSubmit, onInvalid)(event)}>
          {/*  ⚠️ `onInvalid` là BẮT BUỘC với biểu mẫu chia tab, không phải tiện ích.

               Radix hủy mount nội dung tab ẩn, nên câu lỗi của một ô ở tab khác
               không có chỗ nào để hiện ra. Không có nhánh này thì bấm Lưu là
               **không có gì xảy ra**: không toast, không lỗi trên màn, không
               một lời gọi API nào — nút Lưu đọc ra như bị hỏng. Dựng lại được
               trên trình duyệt thật 08/09/2026. */}
          <div className="mb-4 flex flex-wrap items-center justify-between gap-3">
            {/*  ⚠️ Đích của nút lùi phụ thuộc CHỖ ĐẾN. Hồ sơ này mở được từ tab
                 "Người đang giữ" của một chức vụ hay bảng thành viên của một
                 phòng ban; trỏ cứng về danh sách nhân sự là ném người dùng sang
                 màn họ chưa từng đứng, mất luôn tab và bộ lọc đang đặt. Trên
                 điện thoại đây là nút lùi DUY NHẤT trong tầm mắt.
                 Nhãn đổi theo đích — "Danh sách nhân sự" mà bấm ra chức vụ thì
                 nút nói dối. Xem `use-back-target.ts`. */}
            <Button variant="ghost" size="sm" asChild>
              <Link to={backTarget.url}>
                <ArrowLeft />
                {backTarget.fromElsewhere ? 'Quay lại' : 'Danh sách nhân sự'}
              </Link>
            </Button>

            <div className="flex items-center gap-2">
              {/*  duoc-CR-676 — Phiếu thông tin nhân viên BM00../QT01/NS. Là LIÊN KẾT (không phải
                   nút) nên không bao giờ submit form hồ sơ. */}
              <Button variant="outline" asChild>
                <Link to={appRoutes.hr.employeeInfoPrint(employee.id)}>
                  <Printer />
                  In phiếu thông tin
                </Link>
              </Button>
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

          <EmployeePendingChangeRequestBanner employee={employee} enabled={canWrite} />

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

          {/*  ⚠️ Năm tab nhãn tiếng Việt dài KHÔNG vừa một hàng 390px — đo được
               dải rộng 633px, và bản trước để nó tràn nên kéo theo CẢ TRANG trôi
               ngang. Bóp cho vừa cũng không được: riêng phần chữ ở cỡ 12px đã
               361px trên 358px dùng được. Nên dải tự cuộn ngang, và tab đang mở
               tự được kéo vào tầm nhìn — xem `ScrollableTabsList`. */}
          <Tabs value={tab} onValueChange={setTab} className="mt-5">
            <ScrollableTabsList value={tab}>
              <TabsTrigger value="general" className={TAB_TRIGGER_UNDERLINE}>
                Chung
              </TabsTrigger>
              <TabsTrigger value="work-history" className={TAB_TRIGGER_UNDERLINE}>
                <History className="size-4" />
                Quá trình công tác
              </TabsTrigger>
              <TabsTrigger value="decisions" className={TAB_TRIGGER_UNDERLINE}>
                <FileCheck2 className="size-4" />
                Quyết định bổ nhiệm
              </TabsTrigger>
              <TabsTrigger value="concurrent" className={TAB_TRIGGER_UNDERLINE}>
                <Layers className="size-4" />
                Kiêm nhiệm
              </TabsTrigger>
              <TabsTrigger value="contact" className={TAB_TRIGGER_UNDERLINE}>
                <Phone className="size-4" />
                Liên hệ &amp; Ngân hàng
              </TabsTrigger>
              <TabsTrigger value="documents" className={TAB_TRIGGER_UNDERLINE}>
                <IdCard className="size-4" />
                Giấy tờ &amp; BHXH
              </TabsTrigger>
              {canReadLaborContract && (
                <TabsTrigger value="labor-contracts" className={TAB_TRIGGER_UNDERLINE}>
                  <FileSignature className="size-4" />
                  Hợp đồng
                </TabsTrigger>
              )}
              <TabsTrigger value="leave" className={TAB_TRIGGER_UNDERLINE}>
                <CalendarDays className="size-4" />
                Quỹ phép
              </TabsTrigger>
              <TabsTrigger value="account" className={TAB_TRIGGER_UNDERLINE}>
                <UserCog className="size-4" />
                Tài khoản
              </TabsTrigger>
            </ScrollableTabsList>

            <TabsContent value="general" className="mt-5 max-md:mt-2">
              <EmployeeTabGeneral
                employee={employee}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
                isSelf={currentUser?.employee_id === employee.id}
                departments={departments?.items ?? []}
                colleagues={(colleagues?.items ?? [])
                  //  Bỏ CHÍNH MÌNH khỏi ô chọn: tự làm quản lý của mình là một
                  //  vòng, backend chặn bằng 400 — thà đừng bày ra để chọn.
                  .filter((e) => e.id !== employeeId)
                  .map((e) => ({ id: e.id, label: `${e.full_name} (${e.code})` }))}
              />
            </TabsContent>

            <TabsContent value="work-history" className="mt-5 max-md:mt-2">
              <EmployeeTabWorkHistory employee={employee} />
            </TabsContent>

            <TabsContent value="decisions" className="mt-5 max-md:mt-2">
              <EmployeeTabWorkDecisions employee={employee} />
            </TabsContent>

            <TabsContent value="concurrent" className="mt-5 max-md:mt-2">
              {/*  duoc-CR-755: kiêm nhiệm thành TAB RIÊNG (thay thẻ chọn nhiều phòng ở tab Chung) vì mỗi dòng nay có
                   công ty, chức vụ, ngày, quyết định và công tắc phạm vi quyền. Nó vẫn là một nửa của câu "người này
                   thấy được gì" — công tắc nằm ngay trên từng dòng. */}
              <EmployeeTabConcurrent employee={employee} />
            </TabsContent>

            <TabsContent value="contact" className="mt-5 max-md:mt-2">
              <EmployeeTabContact
                employeeId={employeeId}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
              />
            </TabsContent>

            <TabsContent value="documents" className="mt-5 max-md:mt-2">
              <EmployeeTabDocuments
                employee={employee}
                canWrite={canWrite}
                canReadSensitive={canReadSensitive}
              />
            </TabsContent>

            {canReadLaborContract && (
              <TabsContent value="labor-contracts" className="mt-5 max-md:mt-2">
                <EmployeeTabLaborContracts employee={employee} />
              </TabsContent>
            )}

            <TabsContent value="leave" className="mt-5 max-md:mt-2">
              <div className="space-y-5">
                <EmployeeTabLeave employee={employee} />
                <EmployeeWorkScheduleCard employeeId={employee.id} />
              </div>
            </TabsContent>

            <TabsContent value="account" className="mt-5 max-md:mt-2">
              {/*  Còn lại đúng hai thứ của TÀI KHOẢN ĐĂNG NHẬP: quyền vào hệ
                   thống và chữ ký dùng trên chứng từ. Ghép đôi để ở màn rộng
                   chúng không thành hai dải ngang rỗng nửa bên phải. */}
              <div className="grid items-stretch gap-5 lg:grid-cols-2">
                <EmployeeAccountCard
                  employeeId={employee.id}
                  email={employee.email}
                  className="h-full"
                />
                <EmployeeSignatureCard
                  employeeId={employee.id}
                  signature={employee.signature}
                  canEdit={canWrite}
                  hasAccount={employee.user_id > 0}
                  className="h-full"
                />
              </div>
              {/*  bao-CR-395: phiên đang mở + lịch sử đăng nhập 90 ngày. Thẻ tự
                   ẩn khi thiếu `login_session.read` hoặc nhân sự chưa có tài
                   khoản — mọi hook bên trong đều gác `enabled`. */}
              <LoginSessionUserCard
                employeeId={employee.id}
                userId={employee.user_id}
                userName={employee.full_name}
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
      {saveFlow.pendingLeave && (
        <EmployeePendingWorkConfirmDialog
          open
          onOpenChange={(next) => !next && saveFlow.cancelLeave()}
          employeeId={employeeId}
          title="Lưu hồ sơ nghỉ việc?"
          description={
            <>
              <p>
                Lưu xong, mọi tài khoản đăng nhập của người này sẽ bị <strong>KHÓA</strong> và{' '}
                <strong>ĐĂNG XUẤT</strong> khỏi mọi thiết bị.
              </p>
              <p>Kiểm các việc người này đang giữ dưới đây — chuyển đi trước khi khóa.</p>
            </>
          }
          confirmLabel="Lưu và chuyển nghỉ việc"
          pending={saveEmployee.isPending}
          onConfirm={saveFlow.confirmLeave}
        />
      )}
      {saveFlow.pendingDepartment && (
        <EmployeeKeepOldDepartmentDialog
          open
          onOpenChange={(next) => !next && saveFlow.cancelDepartment()}
          oldDepartmentName={departmentName(employee.department_id, employee.department_name)}
          newDepartmentName={departmentName(saveFlow.pendingDepartment.department_id)}
          pending={saveEmployee.isPending}
          onChoose={saveFlow.answerKeepOldDepartment}
        />
      )}
      {saveFlow.pendingCompany && (
        <EmployeeCompanyChangeConcurrentDialog
          open
          onOpenChange={(next) => !next && saveFlow.cancelCompany()}
          oldCompanyName={companyName(employee.company_id, employee.company_name)}
          newCompanyName={companyName(saveFlow.pendingCompany.values.company_id)}
          rows={saveFlow.pendingCompany.rows}
          pending={saveEmployee.isPending}
          onConfirm={saveFlow.answerCompanyChange}
        />
      )}
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
