import { zodResolver } from '@hookform/resolvers/zod'
import {
  ArrowLeft,
  CalendarDays,
  FileCheck2,
  FileSignature,
  History,
  IdCard,
  Loader2,
  Phone,
  Printer,
  Save,
  UserCog,
} from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useForm } from 'react-hook-form'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { AuditActivityFeed } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { useBackTarget } from '@/shared/hooks/use-back-target'
import { useHeightCssVar } from '@/shared/hooks/use-height-css-var'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { AvatarUploader } from '@/shared/ui/avatar-uploader'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { Form } from '@/shared/ui/form'
import { FormSectionProvider, type FormSectionContextValue } from '@/shared/ui/form-section'
import { PageContainer } from '@/shared/ui/page-container'
import { LoginSessionUserCard } from '@/modules/system/components/login-session-user-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { TAB_LIST_UNDERLINE_ALWAYS, TAB_TRIGGER_UNDERLINE_ALWAYS } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { cn } from '@/shared/utils/cn'
import { EmployeeAccountCard } from '../components/employee-account-card'
import { EmployeePendingChangeRequestBanner } from '../components/employee-pending-change-request-banner'
import { EmployeePendingWorkConfirmDialog } from '../components/employee-pending-work-confirm-dialog'
import { EmployeeDepartmentCard } from '../components/employee-department-card'
import { EmployeeDetailBlock } from '../components/employee-detail-block'
import { EmployeeDetailSidebar } from '../components/employee-detail-sidebar'
import { EmployeeSignatureCard } from '../components/employee-signature-card'
import { EmployeeStatusIndicator } from '../components/employee-status-indicator'
import { EmployeeTabContact } from '../components/employee-tab-contact'
import { EmployeeTabDocuments } from '../components/employee-tab-documents'
import { EmployeeTabGeneral } from '../components/employee-tab-general'
import { EmployeeTabLaborContracts } from '../components/employee-tab-labor-contracts'
import { EmployeeTabLeave } from '../components/employee-tab-leave'
import { EmployeeWorkScheduleCard } from '../components/employee-work-schedule-card'
import { EmployeeTabWorkDecisions } from '../components/employee-tab-work-decisions'
import { EmployeeTabWorkHistory } from '../components/employee-tab-work-history'
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
import { employeeInitials } from '../types/employee'
import { EMPLOYEE_FIELD_LABELS } from '../utils/employee-field-labels'
import { firstInvalidTab } from '../utils/profile-field-tab'

/** Tab không tự đệm: mọi khối là một nhóm phẳng (`FormSection` / `EmployeeDetailBlock`) tự đệm và kẻ sát mép như ERPNext. */
const TAB_PANEL_CLASS = 'mt-0'

/** Kiểu nhóm của cả màn — hằng số ngoài component để Provider không đổi giá trị mỗi lượt vẽ. */
const FORM_SECTION_STYLE: FormSectionContextValue = {
  variant: 'flat',
  inset: true,
  storagePrefix: 'hr.employee-detail',
  hints: 'icon',
}

/**
 * Làm PHẲNG mọi `Card` trong cột nội dung (duoc-CR-708): các tab cũ vẫn dựng bằng thẻ,
 * mà khung ERPNext không có thẻ lồng trong mặt phẳng. Chỉ gỡ viền / bóng / nền / đệm
 * NGOÀI của thẻ; nội dung giữ nguyên. Hộp thoại dựng qua portal nên không bị ảnh hưởng.
 */
const FLATTEN_CARDS = cn(
  '[&_[data-slot=card]]:gap-4 [&_[data-slot=card]]:rounded-none [&_[data-slot=card]]:border-0',
  '[&_[data-slot=card]]:bg-transparent [&_[data-slot=card]]:p-0 [&_[data-slot=card]]:shadow-none',
  '[&_[data-slot=card-content]]:px-0 [&_[data-slot=card-header]]:px-0',
)

/**
 * Ô nhập NỀN XÁM, không viền — như form ERPNext (duoc-CR-708). Chỉ áp trong màn này:
 * ô nhập thường, ô chữ dài, ô chọn, và nút mở lịch / hộp chọn nằm trong một ô biểu mẫu.
 * Ô bị khóa vẫn mờ đi như cũ nên vẫn phân biệt được với ô sửa được.
 */
const FILLED_FIELDS = cn(
  //  Ô chọn nằm trong `FormControl` (Ô mã số, chọn người…) là `<button data-slot="form-control">`.
  //  Trừ checkbox / switch của Radix — chúng cũng là `<button>`, tô xám bỏ viền là biến mất.
  '[&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:border-transparent [&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:bg-muted [&_button[data-slot=form-control]:not([role=checkbox]):not([role=switch])]:shadow-none',
  //  Ô nằm trong `FormControl` mang `data-slot="form-control"` (Slot đè `data-slot="input"`),
  //  nên phải bắt thêm theo thẻ. Chỉ `input`/`textarea` — ô đánh dấu (checkbox) cũng có thể
  //  nằm trong `FormControl`, tô nền xám + bỏ viền là nó biến mất.
  '[&_input[data-slot=form-control]:not([type=checkbox])]:border-transparent [&_input[data-slot=form-control]:not([type=checkbox])]:bg-muted [&_input[data-slot=form-control]:not([type=checkbox])]:shadow-none',
  '[&_textarea[data-slot=form-control]]:border-transparent [&_textarea[data-slot=form-control]]:bg-muted [&_textarea[data-slot=form-control]]:shadow-none',
  '[&_[data-slot=input]]:border-transparent [&_[data-slot=input]]:bg-muted [&_[data-slot=input]]:shadow-none',
  '[&_[data-slot=textarea]]:border-transparent [&_[data-slot=textarea]]:bg-muted [&_[data-slot=textarea]]:shadow-none',
  '[&_[data-slot=select-trigger]]:border-transparent [&_[data-slot=select-trigger]]:bg-muted [&_[data-slot=select-trigger]]:shadow-none',
  '[&_[data-slot=form-item]_button[aria-haspopup=dialog]]:border-transparent [&_[data-slot=form-item]_button[aria-haspopup=dialog]]:bg-muted [&_[data-slot=form-item]_button[aria-haspopup=dialog]]:shadow-none',
)

/**
 * Chi tiết hồ sơ nhân sự — 8 TAB (duoc-CR-314 Đợt 2, thêm dần về sau).
 *
 * Khung theo ERPNext (duoc-CR-708): tiêu đề + nhãn tình trạng + nút ở một hàng,
 * THANH BÊN trái (ảnh, nhận diện, mốc sinh nhật / kỷ niệm) và cột phải chứa tab
 * cùng lịch sử thao tác. Tab và mọi luật lưu bên dưới giữ nguyên.
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
  const canReadLoginSessions = can('login_session', 'read')
  const canReadSensitive = useCanReadSensitive(employeeId)

  const [urlTab, setTab] = useUrlParamState('tab', 'general')
  //  Mở thẳng `?tab=labor-contracts` khi không có quyền thì về tab Chung, không để khung trống.
  const tab = urlTab === 'labor-contracts' && !canReadLaborContract ? 'general' : urlTab
  const backTarget = useBackTarget(appRoutes.hr.employees)
  //  Chiều cao cụm tiêu đề + dải tab đang dính → `--sticky-head-h`, để thanh bên phải
  //  dính ngay bên dưới nó (cụm này cao thấp tùy khổ màn, không gán cứng được).
  const stickyHeadRef = useHeightCssVar('--sticky-head-h')

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

  //  Cờ "đang gửi" đổi NGAY trong tick — xem `onSubmit`.
  const submittingRef = useRef(false)
  //  duoc-CR-665 (V0-4): lần lưu đưa hồ sơ sang NGHỈ VIỆC / ngừng hoạt động sẽ khóa tài khoản,
  //  nên dừng lại ở hộp "kiểm việc duyệt đang treo" trước. Giữ giá trị form để lưu tiếp khi xác nhận.
  const [pendingLeave, setPendingLeave] = useState<EmployeeProfileFormValues | null>(null)

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
        {/*  Cùng dáng trang thật (tiêu đề · thanh bên · nội dung) để tải xong không nhảy bố cục. */}
        <Skeleton className="mb-4 h-16 w-full" />
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_20rem]">
          <Skeleton className="h-96 w-full" />
          <Skeleton className="h-40 w-full max-xl:order-first xl:h-96" />
        </div>
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
    const leaving =
      (values.status === 'resigned' && employee?.status !== 'resigned') ||
      (!values.is_active && employee?.is_active === true)
    if (leaving) {
      setPendingLeave(values)
      return
    }
    await saveProfile(values)
  }

  async function saveProfile(values: EmployeeProfileFormValues) {
    //  ⚠️ Chặn GỬI HAI LẦN bằng ref, không dựa vào `disabled={isPending}`.
    //
    //  `isPending` là state React nên chỉ đúng ở lần render SAU. Bấm đúp — hay
    //  bấm liên tiếp trong cùng một tick — thì cả hai lần bấm đều thấy nút còn
    //  bật. Bấm 5 lần liền tay ra **5 `PATCH`** (dựng lại được trên trình duyệt
    //  thật 08/09/2026), tức 5 dòng "Cập nhật" trong lịch sử thao tác cho một
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
        values: pickWritableProfile(values, canReadSensitive, employee?.extra_phones),
      })
      //  Lưu xong thì coi giá trị vừa gửi là mốc sạch. `keepDirtyValues` ở effect
      //  trên KHÔNG xóa `dirtyFields`, nên thiếu dòng này thì ô đã lưu vẫn bị coi
      //  là "đang sửa" tới khi rời trang — rồi "Áp" quá trình công tác đổi phòng
      //  ban xong, lần Lưu sau đè ngược giá trị cũ lên (duoc-CR-627, review).
      //  Hai ô lương về lại "không đụng" (null): người lưu không được xem số, để nguyên số vừa gõ
      //  thì lần Lưu sau gửi lại số cũ đè lên số mà HĐLĐ ký sau đó vừa cập nhật (duoc-CR-693).
      form.reset({ ...values, salary_monthly: null, allowance_monthly: null })
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
  const canSeeLoginSessions = canReadLoginSessions && employee.user_id > 0

  return (
    //  duoc-CR-708: trang tràn sát khung như ERPNext — không đệm quanh, không viền bo góc.
    //  Chuỗi `flex-1` từ khung trang xuống lưới hai cột: mặt phẳng trắng (và đường kẻ dọc
    //  của thanh bên) phải kéo HẾT chiều cao vùng nội dung kể cả khi các nhóm đang gập —
    //  `min-h-full` đơn lẻ ở mặt phẳng không đủ vì các lớp cha không có chiều cao.
    <PageContainer className="flex min-h-full flex-col bg-card p-0 lg:p-0">
      <Form {...form}>
        {/*  Dựng handler NGAY TRONG sự kiện, không dựng lúc render: `onSubmit`
             đóng trên `submittingRef`, mà truyền một hàm-đọc-ref vào lúc render là
             thứ `react-hooks/refs` cảnh báo. Ở đây `handleSubmit` chỉ được gọi
             khi người dùng bấm, nên không có gì đọc ref trong lúc vẽ. */}
        <form
          className="flex flex-1 flex-col"
          onSubmit={(event) => void form.handleSubmit(onSubmit, onInvalid)(event)}
        >
          {/*  ⚠️ `onInvalid` là BẮT BUỘC với biểu mẫu chia tab, không phải tiện ích.

               Radix hủy mount nội dung tab ẩn, nên câu lỗi của một ô ở tab khác
               không có chỗ nào để hiện ra. Không có nhánh này thì bấm Lưu là
               **không có gì xảy ra**: không toast, không lỗi trên màn, không
               một lời gọi API nào — nút Lưu đọc ra như bị hỏng. Dựng lại được
               trên trình duyệt thật 08/09/2026. */}
          {/*  duoc-CR-708 — khung form ERPNext: MỘT mặt phẳng, không thẻ con. Hàng tiêu đề
               «Nhân sự / Tên» + nhãn tình trạng + nút bên phải; dưới là cột nội dung (tab
               gạch chân, các nhóm ngăn bằng đường kẻ) và THANH BÊN PHẢI ngăn bằng kẻ dọc. */}
          <div className="flex flex-1 flex-col bg-card">
            {/*  ⚠️ Năm tab nhãn tiếng Việt dài KHÔNG vừa một hàng 390px — đo được
               dải rộng 633px, và bản trước để nó tràn nên kéo theo CẢ TRANG trôi
               ngang. Bóp cho vừa cũng không được: riêng phần chữ ở cỡ 12px đã
               361px trên 358px dùng được. Nên dải tự cuộn ngang, và tab đang mở
               tự được kéo vào tầm nhìn — xem `ScrollableTabsList`. */}
            <Tabs value={tab} onValueChange={setTab} className="flex-1 gap-0">
              {/*  CỐ ĐỊNH khi cuộn (anh Được, 02/11/2026): hàng tiêu đề + nút Lưu + dải tab dính
                 đầu khung cuộn của trang. Chỉ từ `md`: ở điện thoại cụm này cao ~240px (tên
                 xuống dòng, nút xuống hàng), dính lại là mất gần một phần ba màn hình.
                 ⚠️ Không đặt `overflow-hidden` ở mặt phẳng bọc ngoài — nó biến mặt phẳng thành
                 khung cuộn riêng và `sticky` thôi dính. */}
              <div ref={stickyHeadRef} className="z-20 bg-card md:sticky md:top-0">
                <div className="flex flex-wrap items-center justify-between gap-3 border-b px-4 py-3 sm:px-6">
                  <div className="flex min-w-0 flex-wrap items-center gap-x-2 gap-y-1">
                    {/*  ⚠️ Đích của nút lùi phụ thuộc CHỖ ĐẾN. Hồ sơ này mở được từ tab
                 "Người đang giữ" của một chức vụ hay bảng thành viên của một
                 phòng ban; trỏ cứng về danh sách nhân sự là ném người dùng sang
                 màn họ chưa từng đứng, mất luôn tab và bộ lọc đang đặt. Trên
                 điện thoại đây là nút lùi DUY NHẤT trong tầm mắt.
                 Nhãn đổi theo đích — "Danh sách nhân sự" mà bấm ra chức vụ thì
                 nút nói dối. Xem `use-back-target.ts`. */}
                    {/*  Nút lùi dạng MŨI TÊN, không ghi chữ «Nhân sự /»: thanh trên cùng đã có cấp «Nhân sự»
                         (bấm được về danh sách), ghi thêm ở đây là lặp lần nữa (anh Được báo 02/11/2026).
                         Nhãn đọc cho trình đọc màn hình vẫn đổi theo đích như cũ. */}
                    <Button variant="ghost" size="icon" className="-ml-2 size-8" asChild>
                      <Link
                        to={backTarget.url}
                        aria-label={backTarget.fromElsewhere ? 'Quay lại' : 'Về danh sách nhân sự'}
                        title={backTarget.fromElsewhere ? 'Quay lại' : 'Về danh sách nhân sự'}
                      >
                        <ArrowLeft />
                      </Link>
                    </Button>
                    {/*  `line-clamp-2` chứ không `truncate` — cùng lý do ở `RecordIdentityCard`:
                     tên dài trên màn 390px không được mất đuôi. */}
                    <h1 className="line-clamp-2 text-lg font-semibold text-foreground">
                      {employee.full_name}
                    </h1>
                    <EmployeeStatusIndicator
                      status={employee.status}
                      statusLabel={employee.status_label}
                      isActive={employee.is_active}
                    />
                  </div>

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

                {/*  Dải tab chỉ rộng bằng cột nội dung; ô trống bên phải nối tiếp đường kẻ dọc
                 của thanh bên để hai cột thẳng hàng như ERPNext. */}
                <div className="xl:grid xl:grid-cols-[minmax(0,1fr)_20rem]">
                  {/*  duoc-CR-708: 8 tab rộng ~1100px mà cột nội dung cạnh thanh bên chỉ ~720px ở
                       laptop 1280px. Cuộn NGANG ở mọi khổ (có mũi tên ở mép) chứ không xuống
                       hàng — anh Được chốt 02/11/2026: xuống hàng làm dải tab cao gấp đôi. */}
                  <ScrollableTabsList
                    value={tab}
                    //  Bỏ lề âm `-mx-4`: nó dành cho trang không khung, còn ở đây dải nằm TRONG
                    //  mặt phẳng nên lề âm đẩy tab đầu dính sát mép.
                    className="max-md:mx-0"
                    scroll="always"
                    listClassName={cn(TAB_LIST_UNDERLINE_ALWAYS, 'gap-5 border-b-0 px-0')}
                  >
                    <TabsTrigger value="general" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      Chung
                    </TabsTrigger>
                    <TabsTrigger value="work-history" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <History className="size-4" />
                      Quá trình công tác
                    </TabsTrigger>
                    <TabsTrigger value="decisions" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <FileCheck2 className="size-4" />
                      Quyết định bổ nhiệm
                    </TabsTrigger>
                    <TabsTrigger value="contact" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <Phone className="size-4" />
                      Liên hệ &amp; Ngân hàng
                    </TabsTrigger>
                    <TabsTrigger value="documents" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <IdCard className="size-4" />
                      Giấy tờ &amp; BHXH
                    </TabsTrigger>
                    {canReadLaborContract && (
                      <TabsTrigger value="labor-contracts" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                        <FileSignature className="size-4" />
                        Hợp đồng
                      </TabsTrigger>
                    )}
                    <TabsTrigger value="leave" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <CalendarDays className="size-4" />
                      Quỹ phép
                    </TabsTrigger>
                    <TabsTrigger value="account" className={TAB_TRIGGER_UNDERLINE_ALWAYS}>
                      <UserCog className="size-4" />
                      Tài khoản
                    </TabsTrigger>
                  </ScrollableTabsList>
                  <div aria-hidden className="max-xl:hidden xl:border-b xl:border-l" />
                </div>
              </div>

              <EmployeePendingChangeRequestBanner employee={employee} enabled={canWrite} />

              {/*  Hai cột từ `xl` (1280px): nội dung + thanh bên phải 20rem. Không dùng `lg`: ở
                 1024px trừ menu phân hệ và thanh bên thì cột nội dung chỉ còn ~460px. Dưới
                 `xl` thanh bên thành một dải ngang phía trên tab (`order-first`). */}
              <div className="grid flex-1 content-start xl:grid-cols-[minmax(0,1fr)_20rem] xl:content-stretch">
                {/*  Bật cho CẢ cột nội dung: mọi nhóm phẳng + gập / mở (nhớ trạng thái), chú thích
                     dưới ô thu vào biểu tượng (i) — anh Được chốt 02/11/2026. */}
                <FormSectionProvider value={FORM_SECTION_STYLE}>
                  <div className={cn('min-w-0', FLATTEN_CARDS, FILLED_FIELDS)}>
                    <TabsContent value="general" className="mt-0">
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

                      {/*  Kiêm nhiệm dời từ tab "Tài khoản" sang đây (khách chốt
                   10/09/2026): nó là thông tin CÔNG VIỆC — người này phụ trách
                   thêm phòng nào — nên đứng cạnh Phòng ban · Chức vụ · Quản lý
                   trực tiếp thì người khai tìm được mà không phải đoán.

                   ⚠️ Lý do cũ để nó cạnh thẻ tài khoản KHÔNG sai và đừng quên:
                   phòng kiêm nhiệm mở rộng **phạm vi dữ liệu** người này đọc
                   được, tức nó cũng là một nửa của câu "người này thấy được
                   gì". Đổi chỗ là chọn cách đọc thứ nhất; ai đổi lại thì đọc
                   dòng này trước. */}
                      <EmployeeDepartmentCard
                        employeeId={employee.id}
                        companyId={employee.company_id}
                        primaryDepartmentId={employee.department_id}
                        canWrite={canWrite}
                        isSelf={currentUser?.employee_id === employee.id}
                        variant="section"
                      />
                    </TabsContent>

                    <TabsContent value="work-history" className={TAB_PANEL_CLASS}>
                      <EmployeeDetailBlock title="Quá trình công tác">
                        <EmployeeTabWorkHistory employee={employee} />
                      </EmployeeDetailBlock>
                    </TabsContent>

                    <TabsContent value="decisions" className={TAB_PANEL_CLASS}>
                      <EmployeeDetailBlock title="Quyết định bổ nhiệm">
                        <EmployeeTabWorkDecisions employee={employee} />
                      </EmployeeDetailBlock>
                    </TabsContent>

                    {/*  Hai tab này tự dựng `FormSection` (tự thành nhóm gập / mở) và tự bọc bảng
                       người báo tin / hộ gia đình bằng `EmployeeDetailBlock`. */}
                    <TabsContent value="contact" className={TAB_PANEL_CLASS}>
                      <EmployeeTabContact
                        employeeId={employeeId}
                        canWrite={canWrite}
                        canReadSensitive={canReadSensitive}
                      />
                    </TabsContent>

                    <TabsContent value="documents" className={TAB_PANEL_CLASS}>
                      <EmployeeTabDocuments
                        employee={employee}
                        canWrite={canWrite}
                        canReadSensitive={canReadSensitive}
                      />
                    </TabsContent>

                    {canReadLaborContract && (
                      <TabsContent value="labor-contracts" className={TAB_PANEL_CLASS}>
                        <EmployeeDetailBlock title="Hợp đồng lao động">
                          <EmployeeTabLaborContracts employee={employee} />
                        </EmployeeDetailBlock>
                      </TabsContent>
                    )}

                    <TabsContent value="leave" className={TAB_PANEL_CLASS}>
                      <EmployeeDetailBlock title="Quỹ phép">
                        <EmployeeTabLeave employee={employee} />
                      </EmployeeDetailBlock>
                      <EmployeeDetailBlock title="Lịch làm việc">
                        <EmployeeWorkScheduleCard employeeId={employee.id} />
                      </EmployeeDetailBlock>
                    </TabsContent>

                    <TabsContent value="account" className={TAB_PANEL_CLASS}>
                      {/*  Ba nhóm gập / mở của TÀI KHOẢN ĐĂNG NHẬP: quyền vào hệ thống, chữ ký dùng
                         trên chứng từ, phiên đăng nhập. Xếp chồng (không ghép đôi hai cột như bản
                         thẻ cũ) vì mỗi nhóm giờ có hàng tiêu đề riêng kẻ hết bề ngang. */}
                      <EmployeeDetailBlock title="Tài khoản đăng nhập">
                        <EmployeeAccountCard employeeId={employee.id} email={employee.email} />
                      </EmployeeDetailBlock>
                      <EmployeeDetailBlock title="Chữ ký">
                        <EmployeeSignatureCard
                          employeeId={employee.id}
                          signature={employee.signature}
                          canEdit={canWrite}
                          hasAccount={employee.user_id > 0}
                        />
                      </EmployeeDetailBlock>
                      {/*  bao-CR-395: phiên đang mở + lịch sử đăng nhập 90 ngày. Thẻ tự ẩn khi thiếu
                         `login_session.read` hoặc nhân sự chưa có tài khoản — cùng điều kiện đó
                         gác cả NHÓM, không thì còn trơ một tiêu đề «Phiên đăng nhập» rỗng. */}
                      {canSeeLoginSessions && (
                        <EmployeeDetailBlock title="Phiên đăng nhập">
                          <LoginSessionUserCard
                            employeeId={employee.id}
                            userId={employee.user_id}
                            userName={employee.full_name}
                          />
                        </EmployeeDetailBlock>
                      )}
                    </TabsContent>

                    {/* Ngoài mọi TabsContent — lịch sử thao tác đúng ở mọi tab (như «Hoạt động» của ERPNext). */}
                    {/*  duoc-CR-710: khối «Hoạt động» kiểu ERPNext — đường dọc có chấm, câu «A đã cập nhật Phòng ban ·
                         3 ngày trước». `AuditTimeline` (khối thẻ) vẫn dùng ở các màn khác. */}
                    <EmployeeDetailBlock title="Hoạt động">
                      <AuditActivityFeed
                        entity="employee"
                        entityId={employeeId}
                        fieldLabels={EMPLOYEE_FIELD_LABELS}
                        createdNoun="hồ sơ này"
                      />
                    </EmployeeDetailBlock>
                  </div>
                </FormSectionProvider>

                <EmployeeDetailSidebar
                  className="max-xl:order-first max-xl:border-b xl:border-l"
                  employee={employee}
                  avatar={
                    <AvatarUploader
                      src={employee.avatar}
                      fallback={employeeInitials(employee.full_name)}
                      alt={employee.full_name}
                      className="rounded-xl xl:size-24 xl:[&>span]:text-3xl"
                      onUpload={
                        canEditAvatar ? (file) => uploadAvatar.mutateAsync(file) : undefined
                      }
                      disabledHint={
                        employee.user_id
                          ? 'Ảnh đại diện'
                          : 'Nhân sự chưa có tài khoản đăng nhập nên chưa đặt được ảnh'
                      }
                    />
                  }
                />
              </div>
            </Tabs>
          </div>
        </form>
      </Form>
      {pendingLeave && (
        <EmployeePendingWorkConfirmDialog
          open
          onOpenChange={(next) => !next && setPendingLeave(null)}
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
          onConfirm={() => {
            const values = pendingLeave
            setPendingLeave(null)
            void saveProfile(values)
          }}
        />
      )}
    </PageContainer>
  )
}
