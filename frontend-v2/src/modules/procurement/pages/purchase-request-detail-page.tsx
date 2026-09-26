import {
  ArrowLeft,
  ArrowRightLeft,
  Ban,
  Check,
  CheckCheck,
  Copy,
  CornerUpLeft,
  ListChecks,
  Loader2,
  Pencil,
  Plus,
  Printer,
  Save,
  Send,
  ShoppingCart,
  X,
} from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import type { AuthUser } from '@/core/auth/auth-types'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { RequiredDossiersCard } from '@/modules/dossier/components/required-dossiers-card'
import { DOC_KINDS } from '@/modules/dossier/types/dossier-applicability'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { DOSSIER_UI_ENABLED } from '@/shared/constants/feature-flags'
import { queryKeys } from '@/shared/constants/query-keys'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from '@/shared/ui/alert-dialog'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { DetailPageHeader } from '@/shared/ui/detail-page-header'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { confirm as confirmDialog } from '@/shared/ui/confirm-dialog'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { formatDate } from '@/shared/utils/format-date'
import { StatusBadge } from '../components/document-status-badge'
import { DocumentAttachmentsCard } from '../components/document-attachments-card'
import { DocumentComments } from '../components/document-comments'
import { PurchaseRequestInfoCard } from '../components/purchase-request-info-card'
import {
  EMPTY_PURCHASE_REQUEST_ITEM,
  PurchaseRequestItemsTable,
} from '../components/purchase-request-items-table'
import { PurchaseRequestLineDetailDialog } from '../components/purchase-request-line-detail-dialog'
import { PurchaseRequestChooseCard } from '../components/purchase-request-choose-card'
import { PurchaseRequestSupplierCard } from '../components/purchase-request-supplier-card'
import { DocumentMoneyTotals } from '../components/document-money-totals'
import { PurchaseRequestLinkedDocumentsCard } from '../components/purchase-request-linked-documents-card'
import { ReturnChoiceDialog } from '../components/return-choice-dialog'
import { TransferDeptDialog, type TransferDeptMode } from '../components/transfer-dept-dialog'
import {
  useAssignPurchaser,
  useDeletePurchaseRequest,
  useDefaultDeptHead,
  useDeptHeadCandidates,
  useOrderProgress,
  usePurchaseRequest,
  usePurchaseRequestAction,
  usePurchaseRequestAssignableStaff,
  useSavePurchaseRequest,
  useSetUrgent,
  useTransferPurchaseRequestDept,
  useUpdateItemStatus,
  type PurchaseRequestAction,
} from '../hooks/use-purchase-request'
import { useGeneratePrOrders } from '../hooks/use-purchase-request-options'
import { useRelatedPurchaseOrders } from '../hooks/use-purchase-request-support'
import { isPrOptionStageOpen } from '../types/purchase-request-options'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import type { PurchaseOrder } from '../types/purchase-document'
import type { PurchaseOrderItem } from '../types/purchase-order-detail'
import { handlingDeptForCreate } from '../utils/handling-dept-display'
import {
  buildPurchaseOrderLines,
  toDraftFromRequest,
} from '../utils/purchase-order-draft'
import { validatePurchaseRequest } from '../utils/required-fields'
import { resolveReturnAction, type ReturnTarget } from '../utils/return-action'
import {
  parsePurchaseAssistantDraft,
  type PurchaseAssistantDraft,
} from '../utils/assistant-draft'
import { purchaseRequestApi } from '../api/purchase-request-api'
import {
  isClosed,
  isDispatched,
  isEditable,
  type PurchaseRequestDetail,
  type PurchaseRequestItem,
} from '../types/purchase-request-detail'

type ReasonAction = Extract<PurchaseRequestAction, 'return' | 'cancel'>
type ConfirmAction = Extract<PurchaseRequestAction, 'dispatch' | 'complete'>

const REASON_ACTIONS: Record<ReasonAction, { title: string; description: string }> = {
  return: {
    title: 'Trả phiếu về cho người yêu cầu',
    description: 'Phiếu chuyển sang Bị trả lại để người yêu cầu sửa và gửi duyệt lại.',
  },
  cancel: {
    title: 'Từ chối phiếu',
    description: 'Phiếu sẽ bị khóa và không thể sửa lại.',
  },
}

const CONFIRM_ACTIONS: Record<ConfirmAction, { title: string; description: string }> = {
  dispatch: {
    title: 'Duyệt điều phối phiếu?',
    description: 'Hệ thống sẽ tự động phân bổ nhân sự thu mua phụ trách theo phân loại hàng.',
  },
  complete: {
    title: 'Hoàn thành phiếu?',
    description: 'Phiếu được đóng sau khi mọi dòng hàng đã Hoàn thành hoặc Hủy đơn.',
  },
}

/**
 * Chi tiết PYC theo đầy đủ cấu trúc nghiệp vụ của frontend v1, nhưng tách thành
 * các component v2 để giữ page điều phối state và quyền thay vì ôm mọi UI.
 */
export function PurchaseRequestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const location = useLocation()
  // Route tạo mới là route tĩnh `/new`, không khai `:id`, nên `useParams()`
  // trả `undefined`. Vẫn chấp nhận giá trị `new` để component an toàn nếu sau
  // này route được gộp lại với route chi tiết.
  const isNew = !id || id === 'new'
  const purchaseRequestId = isNew ? 0 : Number(id)
  const { user } = useAuth()
  const { can } = usePermission()

  //  Bản nháp do Trợ lý AI soạn (tool `draft_purchase_request`), truyền qua state khi
  //  điều hướng từ trang chat. Chỉ áp cho phiếu MỚI; state không hợp lệ thì bỏ qua.
  const assistantDraft = isNew
    ? parsePurchaseAssistantDraft(
        (location.state as { assistantDraft?: unknown } | null)?.assistantDraft,
      )
    : null

  const { data: serverData, isLoading, isError } = usePurchaseRequest(purchaseRequestId)
  const { data: progress } = useOrderProgress(purchaseRequestId)
  //  bao-CR-486: chỉ người phân bổ được mới cần danh sách NSTM; người yêu cầu không gọi.
  //  Gọi ở ĐÂY (trước mọi `return` sớm) — luật hook.
  const { data: assignableStaff } = usePurchaseRequestAssignableStaff(
    purchaseRequestId,
    can('purchase_request', 'approve'),
  )
  // bao-CR-421: hộp xác nhận trước khi gom đơn theo phương án phải nói được phiếu
  // này ĐÃ có đơn mua hàng nào chưa. Gọi đúng truy vấn của thẻ "Chứng từ liên quan"
  // (cùng `queryKey`) nên TanStack Query dùng lại kết quả, không tốn thêm lượt gọi.
  const { data: relatedOrdersData } = useRelatedPurchaseOrders(isNew ? '' : serverData?.code || '')
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })
  const { data: employeesData } = useEmployees({ page_size: 1000, is_active: true })
  // bao-CR-414: danh mục phòng ban cho ô «Phòng xử lý» (bao-CR-480 đổi tên). Mọi vai trò seed đều đọc được
  // `department`, nhưng vẫn gác bằng quyền để người bị cắt quyền không ăn 403 lúc mở phiếu.
  const { data: departmentsData } = useDepartments(
    { page_size: 500 },
    { enabled: can('department', 'read') },
  )
  const savePurchaseRequest = useSavePurchaseRequest()
  const runAction = usePurchaseRequestAction(purchaseRequestId)
  const deletePurchaseRequest = useDeletePurchaseRequest()
  const assignPurchaser = useAssignPurchaser(purchaseRequestId)
  const updateItemStatus = useUpdateItemStatus(purchaseRequestId)
  const setUrgent = useSetUrgent(purchaseRequestId)
  // bao-CR-414 GĐ5: đẩy cả phiếu sang phòng khác xử lý / trả về phòng lập.
  const transferDept = useTransferPurchaseRequestDept(purchaseRequestId)
  const [transferMode, setTransferMode] = useState<TransferDeptMode | null>(null)
  const [returnChoiceOpen, setReturnChoiceOpen] = useState(false)   // bao-CR-498
  // bao-CR-310 đợt 4 (rà lại): nút gom theo phương án dời từ thẻ Phương án lên
  // đầu trang, nhập chung một nút "Tạo đơn mua hàng" sổ xuống — 2 nút tạo đơn
  // còn 1. Chặn bấm đúp bằng ref (state React trễ một nhịp, luật duoc-CR-317).
  const generateOrders = useGeneratePrOrders(purchaseRequestId)
  const generatingRef = useRef(false)

  const [editing, setEditing] = useState(isNew)

  const [draft, setDraft] = useState<PurchaseRequestDetail | null>(() =>
    isNew ? applyPurchaseAssistantDraft(createEmptyPurchaseRequest(user), assistantDraft) : null,
  )
  // CR-071 — chỉ hỏi backend khi đang SỬA: ô TBP lúc chỉ đọc là chữ, không cần danh sách.
  // bao-CR-474: tra theo PHÒNG BAN trên form (tạo mới cũng chọn được) + trưởng phòng mặc
  // định để ô luôn hiện một người khi chưa ai được chọn.
  const formDepartment = (draft ?? serverData)?.department ?? ''
  const formDepartmentId = (draft ?? serverData)?.department_id ?? 0
  const { data: deptHeadData } = useDeptHeadCandidates(
    formDepartment,
    (draft ?? serverData)?.company_id ?? 0,
    editing,
  )
  const { data: defaultDeptHead } = useDefaultDeptHead(formDepartment, formDepartmentId, editing)
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [reason, setReason] = useState('')
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null)
  const [lineIndex, setLineIndex] = useState<number | null>(null)
  /** Cảnh báo trước khi tạo ĐMH: có dòng đã đặt đủ/vượt so với số yêu cầu. */
  const [orderedWarning, setOrderedWarning] = useState<{
    message: string
    remaining: PurchaseOrderItem[]
    all: PurchaseOrderItem[]
  } | null>(null)

  // Tạo mới -> dựng phiếu rỗng và vào thẳng chế độ sửa.
  // Xem phiếu có sẵn -> nạp dữ liệu server; phiếu CÒN SỬA ĐƯỢC (nháp / bị trả)
  // mở thẳng chế độ sửa như bản v1 — bắt bấm thêm nút "Sửa" là thừa một bước
  // và làm người dùng tưởng mình hết quyền (QA 29/08).
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook sau không chạy.
  const isNewChanged = useHasChanged(isNew)
  const serverDataChanged = useHasChanged(serverData)
  const userChanged = useHasChanged(user)
  if (isNewChanged || serverDataChanged || userChanged) {
    if (isNew) {
      setDraft(
        (current) =>
          current ?? applyPurchaseAssistantDraft(createEmptyPurchaseRequest(user), assistantDraft),
      )
      setEditing(true)
    } else {
      setDraft(serverData ?? null)
      setEditing(serverData ? isEditable(serverData.status) : false)
    }
  }

  const calculatedTotals = useMemo(() => {
    const items = draft?.items ?? []
    const subtotal = items.reduce((sum, item) => sum + item.qty * item.price, 0)
    const total = items.reduce(
      (sum, item) => sum + item.qty * item.price * (1 + (item.vat_pct || 0) / 100),
      0,
    )
    return { subtotal, vat: total - subtotal, total }
  }, [draft?.items])

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-20 w-full" />
        <div className="grid gap-4 xl:grid-cols-[minmax(0,1fr)_360px]">
          <Skeleton className="h-[540px] w-full" />
          <Skeleton className="h-80 w-full" />
        </div>
      </PageContainer>
    )
  }

  if (!isNew && (isError || !serverData)) {
    return (
      <ErrorState
        title="Không mở được phiếu"
        description="Phiếu có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseRequests)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  // Biến ổn định để các callback bên dưới giữ được kiểu non-null sau nhánh lỗi.
  const data = serverData ?? draft ?? createEmptyPurchaseRequest(user)
  const loadedData = data
  const loadedDraft = draft ?? data

  const editable = isEditable(data.status)
  const closed = isClosed(data.status)
  const canManage = can('purchase_request', 'cancel')
  const canAssign = can('purchase_request', 'approve') && !closed
  const showAssignee = can('survey_request', 'process')
  // bao-CR-292/297 (ticket 22): thêm hai mốc purchasing/purchased — phiếu đã mua
  // đủ vẫn có thể cần thêm ĐMH (đặt bổ sung / NCC khác) nên không khóa nút ở đó.
  const workableStatuses = data.dispatch_enabled === false
    ? ['approved', 'dispatched', 'processing', 'purchasing', 'purchased']
    : ['dispatched', 'processing', 'purchasing', 'purchased']
  const allItemsDone =
    data.items.length > 0 &&
    data.items.every((item) => ['completed', 'cancelled'].includes(item.line_status))
  /**
   * NSTM chọn được — bao-CR-486: đọc từ API theo ô «Phòng xử lý» của phiếu (phòng
   * xử lý ≠ 0 → người thu mua của phòng đó; = 0 → người thu mua chung). Trước đó lọc
   * danh mục nhân sự theo TÊN phòng có chữ «thu mua», nên phiếu nhà máy vẫn thấy người
   * thu mua chung. Ô chọn hiện TÊN nhưng lưu MÃ nhân viên.
   * QA 29/08: bổ sung người đã gán ở từng dòng dù họ nằm ngoài danh sách (gán trước khi
   * chuyển phòng, hoặc danh sách chưa tải xong) — không thì ô Select hiện trống như chưa
   * phân công dù DB đã có, cùng bẫy trang Khảo sát từng dính.
   */
  const purchasers = (() => {
    const employees = employeesData?.items ?? []
    const options = (assignableStaff?.items ?? []).map((staff) => ({
      code: staff.code,
      name: staff.full_name,
    }))
    for (const item of data.items) {
      if (item.assignee && !options.some((option) => option.code === item.assignee)) {
        const found = employees.find((employee) => employee.code === item.assignee)
        options.push({ code: item.assignee, name: found?.full_name || item.assignee })
      }
    }
    return options
  })()

  /** Sửa tiến độ dòng: quản lý/người duyệt, hoặc chính NSTM phụ trách dòng đó. */
  const canEditLine = (item: PurchaseRequestItem) =>
    canAssign || canManage || (!!item.assignee && item.assignee === user?.emp_code)

  /** Còn dòng chưa đặt đủ -> mới có việc cho nút "Tạo đơn mua hàng". */
  const hasUnorderedItem = data.items.some(
    (item) =>
      item.product_name &&
      item.line_status !== 'cancelled' &&
      (item.qty || 0) - (progress?.ordered?.[item.product_code] ?? 0) > 0,
  )
  /** Dòng NSTM đã chốt hoàn thành xử lý phương án — nguồn của gom đơn + bản in theo NCC. */
  const hasDoneLine = data.items.some((item) => !!item.id && !!item.options_done)
  /** Đường LẬP TAY: sang màn tạo ĐMH với dòng còn phải mua điền sẵn. */
  const canCreateManual =
    can('purchase_order', 'create') && workableStatuses.includes(data.status) && hasUnorderedItem
  // Dòng nút gom còn tạo được đơn: chưa hủy, CHƯA nằm trên ĐMH nào (kể cả
  // nháp — CR-074 rời `no_po` ngay lúc lập) và còn phương án đang chọn — soi
  // gương đúng luật bỏ qua của backend `generate_orders`.
  const hasLineToGenerate = data.items.some(
    (item) =>
      !!item.id &&
      item.line_status !== 'cancelled' &&
      (item.line_status || 'no_po') === 'no_po' &&
      !!item.chosen_option,
  )
  // Đường GOM THEO PHƯƠNG ÁN — cùng cổng với backend `generate_orders`
  // (H.10.6): ai lập được đơn tay thì gom được, phiếu còn trong giai đoạn mở.
  // Hết dòng gom được thì ẨN mục này thay vì để bấm ra lỗi 400 "Không còn dòng
  // nào tạo được đơn" — khách từng tưởng lỗi trong khi đơn đã tạo rồi (15/09).
  const canGenerateFromOptions =
    !!data.options_enabled &&
    isPrOptionStageOpen(data.status) &&
    can('purchase_order', 'create') &&
    hasDoneLine &&
    hasLineToGenerate
  /**
   * bao-CR-420 — nút "Tạo đơn mua hàng" chỉ còn MỘT đường, chọn sẵn thay người
   * bấm. Thứ tự ưu tiên không phải tùy ý:
   *
   * - Phiếu đã có phương án chốt và còn dòng gom được thì đường ĐÚNG là gom
   *   theo phương án. Lập tay lúc này bỏ qua đúng phần việc NSTM vừa làm — đơn
   *   ra thiếu nhà cung cấp và thiếu giá đã khảo sát.
   * - Không có đường phương án (phiếu cũ, hoặc chưa ai chốt xong) thì lập tay là
   *   đường duy nhất; ẩn nốt thì thu mua không lập nổi đơn từ màn này.
   *
   * Vai trò quyết định người nào thấy gì: cả hai đường đều đòi
   * `purchase_order.create`, nên người yêu cầu không thấy nút này.
   */
  const orderMode: 'options' | 'manual' | null = canGenerateFromOptions
    ? 'options'
    : canCreateManual
      ? 'manual'
      : null
  // Bản in theo NCC (H.6 bản B) — gác N-17: chỉ người có quyền xem NCC; trang in
  // tự gác lại lần nữa. Phiếu đã đóng vẫn in được để lưu hồ sơ.
  const canPrintBySupplier = !isNew && can('supplier', 'read') && hasDoneLine
  const canManageAttachments =
    editable && (can('purchase_request', 'write') || can('purchase_request', 'create'))
  const canManageLineAttachments =
    can('purchase_request', 'write') || can('purchase_request', 'create')
  const selectedLine = lineIndex === null ? null : loadedDraft.items[lineIndex] ?? null
  const canEditSelectedLine = selectedLine
    ? canAssign || canManage || (!!selectedLine.assignee && selectedLine.assignee === user?.emp_code)
    : false

  function patch(changes: Partial<PurchaseRequestDetail>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  function patchLine(index: number, item: PurchaseRequestItem) {
    patch({
      items: loadedDraft.items.map((current, currentIndex) =>
        currentIndex === index ? item : current,
      ),
    })
  }

  async function handleSave(submitAfterSave = false) {
    const validationMessage = validatePurchaseRequest(loadedDraft, submitAfterSave)
    if (validationMessage) {
      toast.error(validationMessage)
      return
    }
    const saved = await savePurchaseRequest.mutateAsync({
      id: isNew ? undefined : purchaseRequestId,
      payload: {
        company_id: loadedDraft.company_id,
        requester: loadedDraft.requester,
        requester_id: loadedDraft.requester_id,
        requester_position: loadedDraft.requester_position,
        department: loadedDraft.department,
        head_of_dept: loadedDraft.head_of_dept,
        head_of_dept_id: loadedDraft.head_of_dept_id,
        // bao-CR-488: lúc tạo, chưa tick «Nhờ phòng khác xử lý» thì không gửi để backend chọn mặc định.
        handler_dept_id: isNew ? handlingDeptForCreate(loadedDraft) : loadedDraft.handler_dept_id,
        purpose: loadedDraft.purpose,
        request_date: loadedDraft.request_date,
        need_date: loadedDraft.need_date,
        is_urgent: loadedDraft.is_urgent,
        vat_rate: loadedDraft.vat_rate,
        note: loadedDraft.note,
        show_code_on_print: loadedDraft.show_code_on_print,
        quote_filename: loadedDraft.quote_filename,
        quote_file_url: loadedDraft.quote_file_url,
        supplier_req: loadedDraft.supplier_req,
        supplier_pur: loadedDraft.supplier_pur,
        items: loadedDraft.items.filter((item) => item.product_name.trim()),
      },
    })
    if (isNew) {
      if (submitAfterSave) {
        try {
          await purchaseRequestApi.submit(saved.id)
          toast.success('Đã tạo và gửi duyệt')
          //  Gọi API trần (không qua mutation) thì phải TỰ nạp lại cache, kẻo
          //  danh sách/chi tiết còn giữ trạng thái Nháp cũ (lỗi QA 29/08).
          void queryClient.invalidateQueries({ queryKey: queryKeys.procurement.all })
        } finally {
          // Phiếu đã được tạo thành công: luôn sang bản ghi thật để tránh người
          // dùng bấm lại và vô tình tạo trùng nếu bước gửi duyệt bị lỗi.
          navigate(appRoutes.procurement.purchaseRequestDetail(saved.id), { replace: true })
        }
        return
      }
      navigate(appRoutes.procurement.purchaseRequestDetail(saved.id), { replace: true })
      return
    }
    // Phiếu có sẵn (nháp / bị trả) cũng đi được đường "Lưu & gửi duyệt" một
    // phát — trước đây nhánh này chỉ có cho phiếu mới, phiếu cũ bấm là chỉ lưu.
    if (submitAfterSave) {
      await runAction.mutateAsync({ action: 'submit' })
    }
  }

  //  bao-CR-498: hai đường «Trả về» gộp vào một nút. Đường luồng duyệt mở theo quyền + trạng
  //  thái; đường trả phòng lập theo cờ backend `can_return_dept` (bao-CR-414).
  const canReturnToRequester =
    (loadedData.can_approve || canManage) &&
    !['draft', 'rejected', 'cancelled', 'completed', 'done'].includes(loadedData.status)
  const canReturnToDepartment = !isNew && Boolean(loadedData.can_return_dept)
  const returnResolution = resolveReturnAction(canReturnToRequester, canReturnToDepartment)

  function runReturn(target: ReturnTarget) {
    if (target === 'department') setTransferMode('return')
    else void handleAction('return')
  }

  async function handleReturn() {
    if (returnResolution === 'choose') setReturnChoiceOpen(true)
    else if (returnResolution) runReturn(returnResolution)
  }

  async function handleAction(action: PurchaseRequestAction) {
    if (action === 'return' || action === 'cancel') {
      setReasonFor(action)
      setReason('')
      return
    }
    // Backend KHÔNG kiểm nội dung phiếu ở `submit_pr` — bộ trường bắt buộc của
    // dòng (mã hàng / SL / kho / ngày cần hàng) chỉ có màn này giữ, đúng như bản
    // `frontend` đang chạy. Bỏ nhánh này là phiếu rỗng ruột vẫn lên duyệt được.
    if (action === 'submit') {
      const message = validatePurchaseRequest(loadedData, true)
      if (message) {
        toast.error(message)
        return
      }
    }
    const result = await runAction.mutateAsync({ action })
    if (action === 'copy' && result?.id) {
      navigate(appRoutes.procurement.purchaseRequestDetail(result.id))
    }
  }

  /** Sang màn tạo ĐMH với dòng hàng điền sẵn — chưa ghi gì vào DB. */
  function goToNewPurchaseOrder(items: PurchaseOrderItem[]) {
    navigate(appRoutes.procurement.purchaseOrderNew, {
      state: { fromPurchaseRequest: toDraftFromRequest(loadedData, items) },
    })
  }

  function handleCreatePurchaseOrder() {
    const { remaining, exceeded, exceededMessages } = buildPurchaseOrderLines(
      loadedData.items,
      progress?.ordered,
    )
    // Không có dòng nào đã đặt đủ/vượt thì đi thẳng, khỏi hỏi.
    if (!exceeded.length) {
      goToNewPurchaseOrder(remaining)
      return
    }
    setOrderedWarning({
      message: exceededMessages.join('; '),
      remaining,
      all: [...remaining, ...exceeded],
    })
  }

  /**
   * Gom dòng đã chọn phương án thành các đơn nháp theo NCC (bao-CR-310 H.10.6).
   * Dời từ thẻ Phương án lên đây khi nhập nút — hành vi giữ nguyên.
   *
   * bao-CR-421 — phiếu ĐÃ CÓ đơn mua hàng thì hộp xác nhận phải nói thẳng điều đó
   * rồi mới hỏi có tạo thêm không. Lý do là nút này nằm ngay đầu trang và bấm một
   * cái là ra đơn nháp, nên người thu mua quay lại phiếu cũ rất dễ bấm lần nữa mà
   * không nhớ hôm trước đã gom rồi; câu xác nhận cũ chỉ tả việc sắp làm, không hề
   * cho biết phiếu đang ở tình trạng nào. Hệ thống KHÔNG đặt trùng — backend bỏ
   * qua dòng đã nằm trên đơn — nhưng thứ đại ca cần là người bấm được hỏi trước,
   * vì "tạo thêm" có khi đúng ý (đặt bổ sung, đổi NCC) mà có khi là bấm nhầm.
   * Đơn đang có lấy từ cùng truy vấn của thẻ "ĐMH liên quan"; truy vấn chưa về thì
   * rơi về câu xác nhận cũ chứ không chặn nút.
   */
  async function handleGenerateOrders() {
    if (generatingRef.current) return
    const existingOrders = relatedOrdersData?.items ?? []
    const orderCodeList = describeExistingOrders(existingOrders)
    const ok = await confirmDialog(
      existingOrders.length
        ? {
            title: 'Phiếu này đã có đơn mua hàng',
            message:
              `Phiếu ${data.code} đã có ${existingOrders.length} đơn mua hàng` +
              `${orderCodeList ? `: ${orderCodeList}` : ''}.\n\n` +
              'Hệ thống chỉ gom thêm những dòng CHƯA nằm trên đơn nào và đã chọn phương án, ' +
              'nên các đơn đang có không bị đụng tới và không có dòng nào bị đặt trùng. ' +
              'Vẫn tạo thêm đơn nháp cho phiếu này?',
            confirmLabel: 'Tạo thêm đơn nháp',
            tone: 'default',
          }
        : {
            title: 'Tạo đơn mua hàng theo phương án',
            message:
              'Hệ thống sẽ gom các dòng đã chọn phương án theo nhà cung cấp thành các đơn mua hàng NHÁP; ' +
              'dòng chưa có nhà cung cấp gom vào một đơn riêng để bổ sung sau. ' +
              'Dòng đã nằm trên đơn mua hàng sẽ được bỏ qua. Tiếp tục?',
            confirmLabel: 'Tạo đơn nháp',
            tone: 'default',
          },
    )
    if (!ok) return
    generatingRef.current = true
    generateOrders.mutate(undefined, {
      // Rà lại vòng 3 (bao-CR-310): tạo nháp xong đưa người dùng sang thẳng danh
      // sách ĐMH, mồi ô tìm kiếm bằng mã phiếu — ô đó tìm cả cột `pr_code` nên
      // danh sách hiện đúng các đơn của phiếu này, khỏi tự đi lọc lại.
      onSuccess: () => {
        const code = (loadedDraft.code || '').trim()
        navigate(
          code
            ? `${appRoutes.procurement.purchaseOrders}?q=${encodeURIComponent(code)}`
            : appRoutes.procurement.purchaseOrders,
        )
      },
      onSettled: () => {
        generatingRef.current = false
      },
    })
  }

  /**
   * Đổi NSTM ngay trên bảng. Phiếu còn ở chế độ SỬA (nháp) thì chỉ đổi nháp và
   * chờ nút Lưu; phiếu đã lưu thì ghi ngay để người phụ trách nhận việc liền.
   */
  function handleAssigneeChange(item: PurchaseRequestItem, assignee: string) {
    if (editing || !item.id) return
    void assignPurchaser.mutateAsync({ id: item.id, assignee })
  }

  /**
   * Ghi "TG dự kiến có hàng" khi rời ô. ĐỔI giá trị ĐÃ CÓ thì bắt buộc nêu lý
   * do (backend ghi vào nhật ký) — hủy nhập lý do sẽ trả ô về giá trị cũ.
   */
  function handleExpectedDateCommit(
    item: PurchaseRequestItem,
    expectedDate: string,
    originalDate: string,
  ) {
    if (editing || !item.id || expectedDate === originalDate) return

    const revert = () =>
      patch({
        items: loadedDraft.items.map((line) =>
          line.id === item.id ? { ...line, expected_date: originalDate } : line,
        ),
      })

    let reason = ''
    if (originalDate) {
      const answer = window.prompt(
        `Đổi thời gian dự kiến có hàng từ ${formatDate(originalDate)} sang ${
          formatDate(expectedDate) || '(để trống)'
        } — nhập lý do:`,
      )
      reason = answer?.trim() ?? ''
      if (!reason) {
        toast.error('Cần nhập lý do thay đổi thời gian dự kiến')
        revert()
        return
      }
    }

    void updateItemStatus.mutateAsync({
      id: item.id,
      line_status: item.line_status,
      progress_note: item.progress_note,
      note: item.note,
      expected_date: expectedDate,
      expected_date_reason: reason,
    })
  }

  async function handleOperationalLineSave(item: PurchaseRequestItem) {
    if (!item.id) return
    const original = loadedData.items.find((line) => line.id === item.id)
    let expectedDateReason = ''
    if (original?.expected_date && original.expected_date !== item.expected_date) {
      expectedDateReason = window.prompt('Nhập lý do thay đổi thời gian dự kiến có hàng:')?.trim() ?? ''
      if (!expectedDateReason) {
        toast.error('Cần nhập lý do thay đổi thời gian dự kiến')
        return
      }
    }
    if (canEditSelectedLine) {
      await updateItemStatus.mutateAsync({
        id: item.id,
        line_status: item.line_status,
        progress_note: item.progress_note,
        note: item.note,
        expected_date: item.expected_date,
        expected_date_reason: expectedDateReason,
      })
    }
    if (canAssign) {
      await assignPurchaser.mutateAsync({ id: item.id, assignee: item.assignee })
    }
  }

  /**
   * Lệnh CHÍNH của đầu trang — nút nền đặc, luôn ở ngoài.
   *
   * Chia theo DÁNG NÚT, không theo cảm tính: nền đặc là việc người mở trang
   * đang định làm (*Lưu* khi đang sửa, *Gửi duyệt* / *Duyệt* / *Duyệt điều
   * phối* / *Tạo đơn mua hàng* theo từng chặng). Giấu chúng sau `⋯` là bắt
   * thêm một chạm cho thao tác thường xuyên nhất.
   */
  const primaryActions = editing ? (
    <>
      <Button onClick={() => void handleSave()} disabled={savePurchaseRequest.isPending}>
        {savePurchaseRequest.isPending ? <Loader2 className="animate-spin" /> : <Save />}
        Lưu
      </Button>
    </>
  ) : (
    <>
      {editable && (
        <Button onClick={() => void handleAction('submit')} disabled={runAction.isPending}>
          <Send />
          Gửi duyệt
        </Button>
      )}
      {data.status === 'submitted' && data.can_approve && (
        <Button onClick={() => void handleAction('approve')} disabled={runAction.isPending}>
          <Check />
          Duyệt
        </Button>
      )}
      {data.status === 'approved' && data.can_dispatch && (
        <Button onClick={() => setConfirmAction('dispatch')} disabled={runAction.isPending}>
          <Check />
          Duyệt điều phối
        </Button>
      )}
      {/* bao-CR-420 (đại ca chốt 17/09/2026): MỘT nút, KHÔNG sổ xuống. Bản cũ
          (bao-CR-310 đợt 4) bày cả hai đường lập tay / gom theo phương án trong
          một menu, nên lần nào cũng mất hai chạm cho việc làm hằng ngày.
          Đường nào chạy là do trạng thái phiếu + quyền của người bấm quyết
          định, xem `orderMode` — không hỏi lại người dùng nữa.
          Nhãn là "Tạo đơn" ở MỌI khổ màn hình (đại ca chốt 17/09/2026): bản dài
          cũ ("Tạo đơn theo phương án" / "Tạo đơn mua hàng") tả cách chạy bên
          trong, thứ người bấm không chọn được và cũng không cần biết — đường nào
          chạy đã do trạng thái phiếu quyết định rồi. Hai nhánh dùng CHUNG một
          chữ nên nút không đổi tên theo vai trò người đăng nhập, và chữ ngắn thì
          khỏi cần đổi nhãn theo bề ngang nữa. Việc sắp làm nói ở hộp xác nhận
          (bao-CR-421), chỗ có đủ chỗ để nói cho tử tế. */}
      {orderMode === 'options' ? (
        <Button
          disabled={runAction.isPending || generateOrders.isPending}
          onClick={() => void handleGenerateOrders()}
        >
          {generateOrders.isPending ? <Loader2 className="animate-spin" /> : <ShoppingCart />}
          Tạo đơn
        </Button>
      ) : orderMode === 'manual' ? (
        <Button onClick={handleCreatePurchaseOrder} disabled={runAction.isPending}>
          <ShoppingCart />
          Tạo đơn
        </Button>
      ) : null}
    </>
  )

  /**
   * Lệnh PHỤ — khổ rộng bày thẳng, khổ hẹp gom vào nút `⋯`.
   *
   * ⚠️ Dựng thành BIẾN chứ không viết hai lần: mỗi nút kéo theo state hoặc
   * mutation riêng (`DeleteConfirmButton` có mutation của nó), chép ra hai bản
   * là hai bộ state song song cho cùng một lệnh.
   */
  const secondaryActions = editing ? (
    <>
      {/* Phiếu sửa được nay mở thẳng chế độ sửa, nên đường gửi duyệt
          phải có mặt ngay tại đây như v1 — bắt Lưu xong mới thấy nút
          Gửi duyệt là giấu mất một bước (QA 29/08). */}
      <Button
        // KHÔNG dùng `secondary`: token `--secondary` gần như trắng
        // và biến thể đó không có viền, nên nút chìm hẳn vào nền
        // thanh công cụ. `outline` cho viền rõ mà vẫn nhường bậc
        // nhấn mạnh cho nút Lưu.
        variant="outline"
        onClick={() => void handleSave(true)}
        disabled={savePurchaseRequest.isPending}
      >
        <Send />
        Lưu &amp; gửi duyệt
      </Button>
      <Button
        variant="outline"
        onClick={() => {
          if (isNew) {
            navigate(appRoutes.procurement.purchaseRequests)
          } else {
            setDraft(data)
            setEditing(false)
          }
        }}
      >
        <X />
        {isNew ? 'Hủy' : 'Hủy sửa'}
      </Button>
              
    </>
  ) : (
    <>
      {/* bao-CR-420 (đại ca chốt 17/09/2026): MỘT nút in, KHÔNG sổ xuống. Bản
          nào mở ra là do vai trò người bấm quyết định — người có quyền xem nhà
          cung cấp (thu mua) hằng ngày cần bản tách theo NCC để gửi từng nơi,
          người yêu cầu cần tờ phiếu gốc. Bản kia KHÔNG mất: thanh công cụ của
          chính trang in có lối bắc sang, xem hai trang in của YCMH.
          Nhãn là "In phiếu" cho cả hai bản (đại ca chốt 17/09/2026) — nút đổi
          tên theo quyền người đăng nhập thì hai người ngồi cạnh nhau mô tả cùng
          một nút bằng hai cái tên, gọi điện cho nhau không ai hiểu ai. Bản nào
          mở ra thì chính trang in nói, không phải cái nút. */}
      <Button variant="outline" asChild>
        <Link
          to={
            canPrintBySupplier
              ? appRoutes.procurement.purchaseRequestSupplierPrint(data.id)
              : appRoutes.procurement.purchaseRequestPrint(data.id)
          }
          target="_blank"
          rel="noreferrer"
        >
          <Printer />
          In phiếu
        </Link>
      </Button>
      {/* bao-CR-422: nút "ĐMH liên quan" ở đây đã bỏ. Nút TỰ ẨN khi phiếu chưa có
          đơn nào, nên đúng lúc người ta cần biết "phiếu này đã lập đơn chưa" thì
          màn hình không nói gì cả. Danh sách ĐMH nay nằm cố định trong thẻ
          "Chứng từ liên quan" bên dưới, cùng chỗ với danh sách YCBG nguồn. */}
      {/* bao-CR-310: mở từ lúc thu mua tiếp nhận phiếu; phiếu đóng vẫn
          vào được để XEM lại phương án đã chốt. Đợt 3b: màn đó là bàn
          làm việc của NSTM nên đòi thêm quyền ghi — người yêu cầu
          thường xem/chọn phương án ngay tại thẻ Phương án bên dưới. */}
      {/* bao-CR-468: công tắc tắt thì cả nút này lẫn thẻ Chọn phương án bên dưới biến mất. */}
      {!isNew && data.options_enabled && isDispatched(data.status) && can('purchase_request', 'write') && (
        <Button variant="outline" asChild>
          <Link to={appRoutes.procurement.purchaseRequestProcess(data.id)}>
            <ListChecks />
            Xử lý phương án
          </Link>
        </Button>
      )}
      {editable && (
        <Button variant="outline" onClick={() => setEditing(true)}>
          <Pencil />
          Sửa
        </Button>
      )}
      {/* bao-CR-498: MỘT nút «Trả về» cho hai đường (trả người lập sửa lại / trả phòng lập tự
          xử lý — bao-CR-414). Cả hai đường cùng mở thì hỏi; một đường thì đi thẳng. */}
      {returnResolution !== null && (
        <Button
          type="button"
          variant="outline"
          className="text-amber-700 hover:text-amber-700"
          title={
            returnResolution === 'department'
              ? 'Trả cả phiếu về phòng lập tự xử lý'
              : 'Trả về để người lập sửa và gửi duyệt lại'
          }
          onClick={() => void handleReturn()}
        >
          <CornerUpLeft />
          Trả về
        </Button>
      )}
      {/* bao-CR-414 GĐ5: backend đã tính sẵn hai cờ theo trạng thái phiếu, dòng
          chưa lên ĐMH và vai trò của người đang xem — giao diện chỉ bày nút. */}
      {!isNew && data.can_transfer_dept && (
        <Button
          type="button"
          variant="outline"
          title="Đẩy cả phiếu sang phòng khác xử lý"
          onClick={() => setTransferMode('transfer')}
        >
          <ArrowRightLeft />
          Chuyển phòng xử lý
        </Button>
      )}
      {data.status === 'submitted' && (data.can_approve || canManage) && (
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive"
          onClick={() => void handleAction('cancel')}
        >
          <Ban />
          Từ chối
        </Button>
      )}
      {canManage && workableStatuses.includes(data.status) && (
        <Button
          variant="outline"
          // KHÔNG disable: nút mờ chỉ nói "không bấm được" chứ không
          // nói vì sao. Cứ cho bấm rồi báo lý do bằng toast — giống v1.
          onClick={() => {
            if (!allItemsDone) {
              // Đỏ chứ không vàng: cam trên nền vàng nhạt đọc rất mệt.
              toast.error(
                'Chưa hoàn thành được phiếu: còn dòng hàng chưa ở trạng thái Hoàn thành hoặc Hủy đơn.',
              )
              return
            }
            setConfirmAction('complete')
          }}
        >
          <CheckCheck />
          Hoàn thành
        </Button>
      )}
      {canManage && !['draft', 'submitted', 'rejected', 'cancelled', 'completed', 'done'].includes(data.status) && (
        <Button
          variant="outline"
          className="text-destructive hover:text-destructive"
          onClick={() => void handleAction('cancel')}
        >
          <Ban />
          Từ chối
        </Button>
      )}
      <PermissionGate entity="purchase_request" action="create">
        <Button variant="outline" onClick={() => void handleAction('copy')}>
          <Copy />
          Nhân bản
        </Button>
      </PermissionGate>
      {['draft', 'rejected', 'cancelled'].includes(data.status) && (
        <PermissionGate entity="purchase_request" action="delete">
          <DeleteConfirmButton
            recordName={data.code || `#${data.id}`}
            pending={deletePurchaseRequest.isPending}
            warning="Phiếu và các dòng hàng kèm theo sẽ bị xóa."
            onConfirm={async () => {
              await deletePurchaseRequest.mutateAsync(data.id)
              navigate(appRoutes.procurement.purchaseRequests)
            }}
          />
        </PermissionGate>
      )}
              
    </>
  )

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <DetailPageHeader
        backTo={appRoutes.procurement.purchaseRequests}
        backLabel="Về danh sách yêu cầu mua hàng"
        title={isNew ? 'Tạo Yêu cầu mua hàng mới' : data.code || 'Phiếu nháp'}
        badges={
          <>
            {!isNew && <StatusBadge status={data.status} labels={PR_STATUS_LABELS} />}
            {loadedDraft.is_urgent && (
              <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
                Đơn gấp
              </Badge>
            )}
          </>
        }
        primaryActions={primaryActions}
        secondaryActions={secondaryActions}
      />

      {data.status === 'approved' && data.dispatch_enabled !== false && (
        <div className="mb-4 rounded-lg border border-amber-300 bg-amber-50 px-4 py-3 text-sm text-amber-900 dark:border-amber-800 dark:bg-amber-950/40 dark:text-amber-200">
          <b>Trưởng bộ phận đã duyệt, phiếu còn chờ thu mua duyệt điều phối.</b>{' '}
          {data.can_dispatch
            ? 'Bấm Duyệt điều phối để hệ thống phân bổ nhân sự thu mua phụ trách.'
            : 'Quản lý hoặc Admin thu mua cần duyệt lần hai trước khi tạo đơn mua hàng.'}
        </div>
      )}

      <div className="min-w-0 space-y-4">
          <PurchaseRequestInfoCard
            data={loadedDraft}
            editing={editing}
            isNew={isNew}
            companies={companiesData?.items}
            employees={employeesData?.items}
            departments={departmentsData?.items}
            deptHeadCandidates={deptHeadData?.items}
            defaultDeptHead={defaultDeptHead}
            urgentEditable={!closed && !editing && can('purchase_request', 'write')}
            onUrgentChange={(value) => void setUrgent.mutateAsync(value)}
            onChange={patch}
          />

          <Card className="gap-4 py-4">
            <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
              <CardTitle className="text-base text-navy dark:text-foreground">
                Danh sách Sản phẩm Yêu cầu
              </CardTitle>
              {editing ? (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    patch({
                      items: [...loadedDraft.items, { ...EMPTY_PURCHASE_REQUEST_ITEM }],
                    })
                  }
                >
                  <Plus />
                  Thêm SP
                </Button>
              ) : null}
            </CardHeader>
            <CardContent className="space-y-3 px-4">
              {/* Câu hướng dẫn để trong thân thẻ, không nhét vào tiêu đề: hai
                  dòng chữ ở tiêu đề làm thẻ này cao hơn hẳn các thẻ còn lại. */}
              {!editing && (
                <p className="text-xs text-muted-foreground">
                  Trạng thái và tiến độ tự đồng bộ từ ĐMH. Mở Chi tiết để xem ghi chú
                  và ảnh đối chiếu.
                </p>
              )}
              <PurchaseRequestItemsTable
                items={loadedDraft.items}
                editing={editing}
                showAssignee={showAssignee}
                onChange={(items) => patch({ items })}
                onOpenDetail={setLineIndex}
                orderedByCode={progress?.ordered}
                purchasers={purchasers}
                canAssign={canAssign}
                canEditLine={canEditLine}
                onAssigneeChange={handleAssigneeChange}
                onExpectedDateCommit={handleExpectedDateCommit}
              />
              <DocumentMoneyTotals {...calculatedTotals} />
            </CardContent>
          </Card>

          <PurchaseRequestSupplierCard data={loadedDraft} editing={editing} onChange={patch} />

          {/* bao-CR-310 đợt 3b: dòng nào NSTM đã "chốt hoàn thành xử lý" thì hiện
              ở đây cho người yêu cầu chọn phương án; thẻ tự ẩn khi chưa có dòng nào. */}
          {!isNew && !editing && data.options_enabled && (
            <PurchaseRequestChooseCard purchaseRequest={data} />
          )}

          {/* bao-CR-422: hai chiều liên kết của phiếu — YCBG nào đẻ ra nó, nó đẻ ra
              ĐMH nào. Thẻ đứng yên một chỗ kể cả khi chưa có gì để bày, vì "chưa có
              đơn nào" cũng là câu trả lời người dùng đang đi tìm. */}
          {!isNew && !editing && <PurchaseRequestLinkedDocumentsCard data={data} />}

          <DocumentAttachmentsCard
            entity="purchase_request"
            entityId={purchaseRequestId}
            canManage={canManageAttachments}
          />

          {/* Thẻ tự ẩn khi thiếu quyền / đang nạp / không có hồ sơ nào khớp
              điều kiện áp dụng. Cờ ngoài là công tắc TẠM ẨN cả phân hệ Hồ sơ
              (21/09/2026) — xem `DOSSIER_UI_ENABLED`. */}
          {DOSSIER_UI_ENABLED && (
            <RequiredDossiersCard
              docKind={DOC_KINDS.PURCHASE_REQUEST}
              docId={purchaseRequestId || undefined}
            />
          )}

          {!isNew && (
            <>
              <DocumentComments entity="purchase_request" entityId={purchaseRequestId} />
              <AuditTimeline
                entity="purchase_request"
                entityId={purchaseRequestId}
                showMessage
                dense
              />
            </>
          )}
      </div>

      <PurchaseRequestLineDetailDialog
        item={selectedLine}
        lineNumber={(lineIndex ?? 0) + 1}
        open={lineIndex !== null}
        editing={editing}
        documentEditable={editable}
        onStartEditing={() => setEditing(true)}
        showAssignee={showAssignee}
        canEditProgress={canEditSelectedLine}
        canAssign={canAssign}
        canManageAttachments={canManageLineAttachments}
        onOpenChange={(open) => {
          if (!open) setLineIndex(null)
        }}
        onChange={(item) => {
          if (lineIndex !== null) patchLine(lineIndex, item)
        }}
        onSaveOperational={handleOperationalLineSave}
      />

      <Dialog open={reasonFor !== null} onOpenChange={(open) => !open && setReasonFor(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>{reasonFor ? REASON_ACTIONS[reasonFor].title : ''}</DialogTitle>
            <DialogDescription>
              {reasonFor ? REASON_ACTIONS[reasonFor].description : ''}
            </DialogDescription>
          </DialogHeader>
          <Textarea
            rows={4}
            value={reason}
            placeholder="Nhập lý do bắt buộc..."
            onChange={(event) => setReason(event.target.value)}
          />
          <DialogFooter>
            <Button variant="outline" onClick={() => setReasonFor(null)}>
              Đóng
            </Button>
            <Button
              variant={reasonFor === 'cancel' ? 'destructive' : 'default'}
              disabled={!reason.trim() || runAction.isPending}
              onClick={async () => {
                if (!reasonFor) return
                await runAction.mutateAsync({ action: reasonFor, reason: reason.trim() })
                setReasonFor(null)
              }}
            >
              {runAction.isPending && <Loader2 className="animate-spin" />}
              Xác nhận
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <AlertDialog
        open={orderedWarning !== null}
        onOpenChange={(open) => !open && setOrderedWarning(null)}
      >
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Có sản phẩm đã đặt đủ hoặc vượt số yêu cầu</AlertDialogTitle>
            <AlertDialogDescription>
              {orderedWarning?.message}. Chọn "Chỉ SP còn thiếu" để bỏ qua các dòng này, hoặc
              "Mua thêm" nếu vẫn muốn đặt tiếp.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <Button
              variant="outline"
              onClick={() => {
                const picked = orderedWarning
                setOrderedWarning(null)
                if (!picked) return
                if (!picked.remaining.length) {
                  toast.info('Không còn sản phẩm nào cần đặt thêm')
                  return
                }
                goToNewPurchaseOrder(picked.remaining)
              }}
            >
              Chỉ SP còn thiếu
            </Button>
            <AlertDialogAction
              onClick={() => {
                const picked = orderedWarning
                setOrderedWarning(null)
                if (picked) goToNewPurchaseOrder(picked.all)
              }}
            >
              Mua thêm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <AlertDialog open={confirmAction !== null} onOpenChange={(open) => !open && setConfirmAction(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>
              {confirmAction ? CONFIRM_ACTIONS[confirmAction].title : ''}
            </AlertDialogTitle>
            <AlertDialogDescription>
              {confirmAction ? CONFIRM_ACTIONS[confirmAction].description : ''}
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Đóng</AlertDialogCancel>
            <AlertDialogAction
              onClick={() => {
                if (confirmAction) void handleAction(confirmAction)
                setConfirmAction(null)
              }}
            >
              Đồng ý
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      <ReturnChoiceDialog
        open={returnChoiceOpen}
        docLabel="yêu cầu mua hàng"
        onOpenChange={setReturnChoiceOpen}
        onPick={runReturn}
      />
      <TransferDeptDialog
        open={transferMode !== null}
        mode={transferMode ?? 'transfer'}
        docLabel="yêu cầu mua hàng"
        departments={departmentsData?.items ?? []}
        currentDeptId={data.handler_dept_id || 0}
        requestingDeptId={data.department_id ?? 0}
        pending={transferDept.isPending}
        onOpenChange={(open) => !open && setTransferMode(null)}
        onConfirm={async (handlerDeptId, transferReason) => {
          await transferDept.mutateAsync({ handlerDeptId, reason: transferReason })
          setTransferMode(null)
        }}
      />
    </PageContainer>
  )
}

function createEmptyPurchaseRequest(user?: AuthUser | null): PurchaseRequestDetail {
  return {
    id: 0,
    code: '',
    company_id: user?.company_id ?? 0,
    company_name: '',
    requester: user?.full_name ?? '',
    requester_id: user?.employee_id ?? 0,
    requester_position: user?.position ?? '',
    department: user?.department_name ?? '',
    head_of_dept: '',
    // Phiếu mới chưa chỉ định ai — backend tự điền theo Trưởng phòng của bộ phận
    // lúc tạo, lưu xong mới đổi người duyệt được (CR-071).
    head_of_dept_id: 0,
    // bao-CR-414: phiếu mới mặc định KHÔNG nhờ phòng nào — người lập chọn tay khi cần.
    handler_dept_id: 0,
    purpose: '',
    request_date: new Date().toISOString().slice(0, 10),
    // bao-CR-316: phiếu mới thì thu mua CHƯA tiếp nhận — để rỗng, backend điền lúc điều phối.
    received_date: '',
    need_date: '',
    status: 'draft',
    is_urgent: false,
    vat_rate: 0.08,
    assignee_id: 0,
    note: '',
    show_code_on_print: true,
    supplier_req: { name: '', tax_code: '', contact: '' },
    supplier_pur: { name: '', tax_code: '', contact: '' },
    supplier_from_survey: false,
    can_edit_supplier_pur: false,
    suggested_supplier: '',
    suggested_supplier_tax_code: '',
    suggested_supplier_contact: '',
    quote_filename: '',
    quote_file_url: '',
    dispatch_enabled: true,
    can_dispatch: false,
    can_approve: false,
    created_at: new Date().toISOString(),
    created_by_name: user?.full_name ?? '',
    requester_signature: '',
    approver_name: '',
    approver_signature: '',
    dispatcher_name: '',
    dispatcher_signature: '',
    purchasing_head_name: '',
    purchasing_head_signature: '',
    options_chosen_at: null,
    options_chosen_by_name: '',
    items: [],
    subtotal: 0,
    vat: 0,
    total: 0,
  }
}

/**
 * bao-CR-421 — kể tên các ĐMH phiếu đang có, để hộp xác nhận nói được "đã có đơn
 * nào" chứ không chỉ nói "đã có đơn rồi". Phiếu gom nhiều NCC ra cả chục đơn nên
 * chỉ đọc ba mã đầu; phần còn lại đếm gộp, không thì câu thông báo dài hơn cả hộp.
 */
function describeExistingOrders(orders: PurchaseOrder[]): string {
  const codes = orders.map((order) => order.code).filter(Boolean)
  const shown = codes.slice(0, 3).join(', ')
  const rest = codes.length - 3
  return rest > 0 ? `${shown} và ${rest} đơn khác` : shown
}

/**
 * Điền bản nháp Trợ lý AI vào phiếu rỗng. Dòng nháp thiếu trường nào thì giữ giá trị
 * mặc định của dòng rỗng (vat_pct 8, line_status 'no_po'); dòng chưa khớp mã hàng có
 * `product_code` rỗng — người dùng chọn lại trên form trước khi gửi duyệt.
 */
function applyPurchaseAssistantDraft(
  base: PurchaseRequestDetail,
  draft: PurchaseAssistantDraft | null,
): PurchaseRequestDetail {
  if (!draft) return base
  return {
    ...base,
    purpose: draft.purpose,
    note: draft.note,
    need_date: draft.need_date || base.need_date,
    // Người dùng nói mua cho pháp nhân khác thì trợ lý đã khớp danh mục -> đè công ty
    // mặc định (công ty của người hỏi); không nói thì giữ nguyên.
    company_id: draft.company_id > 0 ? draft.company_id : base.company_id,
    company_name: draft.company_id > 0 ? draft.company_name : base.company_name,
    items: draft.lines.map((line) => ({ ...EMPTY_PURCHASE_REQUEST_ITEM, ...line })),
  }
}
