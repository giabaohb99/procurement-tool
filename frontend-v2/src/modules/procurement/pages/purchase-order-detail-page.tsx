import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  Check,
  ChevronDown,
  CircleCheck,
  CornerUpLeft,
  FileText,
  Loader2,
  LockOpen,
  Plus,
  Printer,
  Receipt,
  ReceiptText,
  RotateCcw,
  Save,
  Send,
  Ship,
} from 'lucide-react'
import { useMemo, useRef, useState } from 'react'
import { Link, useLocation, useNavigate, useParams, useSearchParams } from 'react-router-dom'
import { useFormTelemetry } from '@/core/telemetry/use-form-telemetry'
import { UI_FORM_CODE } from '@/core/telemetry/ui-event-codes'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
// CR-268: mượn hook tiền treo của phân hệ Tài chính — báo đơn còn tiền trả trước.
import { usePrepayHanging } from '@/modules/finance/hooks/use-payment-requests'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { RequiredDossiersCard } from '@/modules/dossier/components/required-dossiers-card'
import { DOC_KINDS } from '@/modules/dossier/types/dossier-applicability'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { DOSSIER_UI_ENABLED } from '@/shared/constants/feature-flags'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { formatMoney } from '@/shared/utils/format-money'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { confirm as confirmDialog } from '@/shared/ui/confirm-dialog'
import { BulkDeleteButton } from '@/shared/ui/bulk-delete-button'
import { ACTION_TONE_CLASS } from '@/shared/ui/action-tone'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { DetailPageHeader, type HeaderActionList } from '@/shared/ui/detail-page-header'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { DocumentAttachmentsCard } from '../components/document-attachments-card'
import { DocumentComments } from '../components/document-comments'
import { DocumentMoneyTotals } from '../components/document-money-totals'
import { StatusBadge } from '../components/document-status-badge'
import { PurchaseOrderImportCostsCard } from '../components/purchase-order-import-costs-card'
import { PurchaseOrderInfoCard } from '../components/purchase-order-info-card'
import { PurchaseOrderItemsTable } from '../components/purchase-order-items-table'
import { PurchaseOrderLineDialog } from '../components/purchase-order-line-dialog'
import { PurchaseOrderPaymentDialog } from '../components/purchase-order-payment-dialog'
import { PurchaseOrderPaymentRequestsCard } from '../components/purchase-order-payment-requests-card'
import { PurchaseOrderReasonDialog } from '../components/purchase-order-reason-dialog'
import { PurchaseOrderAddManyLinesButton } from '../components/purchase-order-add-many-lines-button'
import {
  buildCompleteConfirmMessage,
  buildExpectedDateDiffMessage,
  findExpectedDateDiffs,
  PO_REOPEN_CONFIRM_MESSAGE,
} from '../components/purchase-order-detail-confirm-messages'
import {
  SurveyReportCard,
  type SurveyReportCardHandle,
} from '../components/survey-report/survey-report-card'
import { useSurveyRequestReport } from '../hooks/use-survey-request-report'
import { lineReportProgress } from '../utils/survey-report-helpers'
import {
  parseDeliveryFileKey,
  pendingFilesOfLine,
  setPendingDeliveryFiles,
  shiftPendingAfterDeliveryRemove,
  shiftPendingAfterLineInsert,
  shiftPendingAfterLineRemove,
  type PendingDeliveryFiles,
} from '../helpers/pending-delivery-files'
import { useApproverCandidates } from '../hooks/use-approver-candidates'
import { usePurchaseOrderLineSelection } from '../hooks/use-purchase-order-line-selection'
import { usePurchaseRequests } from '../hooks/use-purchase-documents'
import { useUploadDeliveryFiles } from '../hooks/use-purchase-request-support'
import {
  useDeletePurchaseOrder,
  usePurchaseOrder,
  usePurchaseOrderAction,
  useSavePurchaseOrder,
  useSetDocumentStatus,
  useSetItemProgress,
  type PurchaseOrderAction,
} from '../hooks/use-purchase-order'
import { PO_STATUS_LABELS } from '../types/purchase-document'
import {
  createEmptyPurchaseOrder,
  toPurchaseOrderPayload,
  type PurchaseOrderDraftFromRequest,
} from '../utils/purchase-order-draft'
import { describeOrdered, findOverOrders, formatQty } from '../utils/over-order'
import { duplicatePurchaseOrderCodes, validatePurchaseOrder } from '../utils/required-fields'
import {
  displayLineBaseAmount,
  isMissingExchangeRate,
  summarizeOrderTotals,
} from '../utils/purchase-order-import-cost'
import { summarizeShipping } from '../utils/purchase-order-shipping'
import {
  isDeliveryStage,
  isImportOrder,
  isPurchaseOrderApproved,
  isPurchaseOrderLocked,
  PO_FIELDS_EDITABLE_AFTER_APPROVE,
  PO_MISA_AFTER_APPROVE_HINT,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/** Mảng rỗng cố định — để lượt vẽ lúc đang tải không đẻ mảng mới mỗi lần. */
const NO_ITEMS: PurchaseOrderItem[] = []

/** Thao tác cần lý do — mở hộp nhập trước khi gọi API. */
type ReasonAction = Extract<PurchaseOrderAction, 'return' | 'reject' | 'unapprove' | 'cancel'>

/**
 * Tiêu đề + nút đồng ý theo đúng bản v1 (duoc-CR-741): hộp mang tên thao tác, nút đồng ý cũng
 * mang tên thao tác, nút còn lại là Hủy. Câu giải thích giữ bản v2 — nói rõ hậu quả hơn.
 */
const REASON_ACTIONS: Record<
  ReasonAction,
  { title: string; description: string; confirmLabel: string }
> = {
  return: {
    title: 'Trả về',
    confirmLabel: 'Trả về',
    description: 'Đơn chuyển sang Bị trả lại để người tạo sửa và gửi duyệt lại.',
  },
  unapprove: {
    title: 'Hủy duyệt',
    confirmLabel: 'Hủy duyệt',
    description:
      'Đơn về Nháp để sửa lại nội dung, sửa xong phải Gửi duyệt và Duyệt lại. Đơn đã nhận hàng hoặc đã có yêu cầu thanh toán thì không hủy duyệt được.',
  },
  reject: {
    title: 'Từ chối đơn',
    confirmLabel: 'Từ chối',
    description: 'Đơn bị khóa, không sửa hay gửi lại được — phải nhân bản thành đơn mới.',
  },
  cancel: {
    title: 'Hủy đơn',
    confirmLabel: 'Hủy đơn',
    description: 'Lý do hủy đơn là bắt buộc. Đơn bị khóa, không sửa lại được.',
  },
}

/** Nhãn của hai tiến độ dòng cần lý do — bản v1 lấy nhãn tiến độ làm tiêu đề lẫn chữ nút. */
const LINE_PROGRESS_REASON_LABELS: Record<string, string> = {
  paused: 'Tạm ngưng',
  cancelled: 'Hủy đơn',
}

/**
 * Chi tiết / tạo mới Đơn mua hàng (ĐMH).
 *
 * Trang giữ state nháp + quyền; phần trình bày nằm ở các component con. Tiến độ
 * nhận hàng theo từng lần giao chưa đưa lên màn này — xem ghi chú ở cuối file.
 */
export function PurchaseOrderDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()

  const isNew = !id || id === 'new'
  const purchaseOrderId = isNew ? 0 : Number(id)
  const { markSubmitted } = useFormTelemetry(UI_FORM_CODE.PURCHASE_ORDER, isNew) // duoc-CR-641

  const { data: serverData, isLoading, isError } = usePurchaseOrder(purchaseOrderId)
  //  bao-CR-602: khối Báo cáo thực hiện của đơn — cùng khóa cache với thẻ bên dưới nên
  //  không thêm request; bảng dòng hàng đọc % theo dòng từ đây.
  const { data: executionReport } = useSurveyRequestReport(purchaseOrderId, 'purchase_order')
  const lineReport = useMemo(() => lineReportProgress(executionReport), [executionReport])
  const reportCardRef = useRef<SurveyReportCardHandle>(null)
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })
  const { data: suppliersData } = useSuppliers(
    { page_size: 1000, is_active: true },
    { enabled: can('supplier', 'read') },
  )
  const { data: employeesData } = useEmployees({ page_size: 1000, is_active: true })
  // Chỉ để dò id của YCMH nguồn (backend lưu MÃ chứ không lưu id) cho nút mở nhanh.
  const { data: purchaseRequestsData } = usePurchaseRequests({ page_size: 1000 })

  const savePurchaseOrder = useSavePurchaseOrder()
  const runAction = usePurchaseOrderAction(purchaseOrderId)
  const deletePurchaseOrder = useDeletePurchaseOrder()
  const setDocumentStatus = useSetDocumentStatus(purchaseOrderId)
  const setItemProgress = useSetItemProgress(purchaseOrderId)
  const uploadDeliveryFiles = useUploadDeliveryFiles()

  /** Nháp đang sửa. Đơn mới có thể được điền sẵn từ YCMH (`state.fromPurchaseRequest`). */
  const [draft, setDraft] = useState<PurchaseOrderDetail | null>(() =>
    isNew
      ? createEmptyPurchaseOrder(
          (location.state as { fromPurchaseRequest?: PurchaseOrderDraftFromRequest } | null)
            ?.fromPurchaseRequest,
        )
      : null,
  )
  // bao-CR-619: tạo từ YCMH → nhắc mã nào làm tổng đặt (đã đặt + đang chờ duyệt + đơn này) vượt số
  // yêu cầu. Chỉ nhắc, không chặn — đại ca chốt 15/10: người lập tự sửa số, không sửa vẫn lưu được.
  const requestProgress = isNew
    ? (location.state as { fromPurchaseRequest?: PurchaseOrderDraftFromRequest } | null)
        ?.fromPurchaseRequest?.progress
    : undefined
  const overOrders = useMemo(
    () => findOverOrders(draft?.items ?? [], requestProgress),
    [draft?.items, requestProgress],
  )
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [progressFor, setProgressFor] = useState<{
    item: PurchaseOrderItem
    status: string
  } | null>(null)
  /** Dòng đang mở hộp chi tiết (thông tin đầy đủ + các lần giao). */
  const [lineIndex, setLineIndex] = useState<number | null>(null)
  //  duoc-CR-654 (D0b): "Nhận hàng" không có form riêng — đo dialog chi tiết dòng ĐMH (nơi nhập giao/nhận) khi người dùng có quyền ghi.
  const { markSubmitted: markLineSubmitted } = useFormTelemetry(
    UI_FORM_CODE.GOODS_RECEIPT,
    lineIndex !== null && can('purchase_order', 'write'),
  )
  const [paymentOpen, setPaymentOpen] = useState(false)
  /** Chặn bấm đúp "Gửi duyệt" ngay trong tick (bao-CR-590). */
  const submittingRef = useRef(false)

  //  Khổ hẹp: câu nhắc dưới bảng dòng hàng nói "chạm vào thẻ" thay vì "nút bút chì".
  //
  //  ⚠️ Khai TRÊN mọi `return` sớm (đang tải / lỗi / không thấy đơn). Hook gọi
  //  sau một nhánh thoát là thứ tự hook đổi giữa các lượt vẽ.
  const isMobile = useIsMobile()
  //  bao-CR-547 + duoc-CR-737: tick nhiều dòng rồi "Xóa đã chọn" — chỉ ở form tạo hoặc
  //  đơn Nháp (đại ca chốt 01/10/2026; đơn Bị trả lại vẫn xóa từng dòng). Trạng thái
  //  chọn giữ ở trang vì nút nằm ở tiêu đề thẻ Dòng hàng, cột tick nằm trong bảng.
  const lineSelection = usePurchaseOrderLineSelection(
    draft?.items ?? NO_ITEMS,
    (isNew || draft?.status === 'draft') && can('purchase_order', isNew ? 'create' : 'write'),
  )
  /**
   * Phiếu giao chọn cho lần giao CHƯA LƯU — giữ hộ tới khi bấm Lưu đơn. Không có
   * nó thì người nhập phải lưu đơn trước rồi mới quay lại đính từng phiếu.
   */
  const [pendingFiles, setPendingFiles] = useState<PendingDeliveryFiles>({})

  // Dữ liệu server về (hoặc đổi đơn) -> nạp lại bản nháp đang xem.
  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook thứ hai không chạy.
  const serverDataChanged = useHasChanged(serverData)
  const isNewChanged = useHasChanged(isNew)
  if ((serverDataChanged || isNewChanged) && !isNew) setDraft(serverData ?? null)

  //  ai-CR-237: link trợ lý AI gửi (`?delivery=<id lần giao>` hoặc `?line=<id dòng>`) mở sẵn hộp dòng hàng chứa lần
  //  giao đó — chỗ người dùng tự đính tệp hóa đơn. Chỉ mở MỘT lần khi dữ liệu đơn về.
  const [searchParams] = useSearchParams()
  const focusDeliveryId = Number(searchParams.get('delivery')) || 0
  const focusLineId = Number(searchParams.get('line')) || 0
  const [focusHandled, setFocusHandled] = useState(false)
  if (!focusHandled && serverData && (focusDeliveryId || focusLineId)) {
    setFocusHandled(true)
    const focusIndex = serverData.items.findIndex(
      (item) =>
        (focusLineId > 0 && item.id === focusLineId) ||
        (focusDeliveryId > 0 && item.deliveries.some((delivery) => delivery.id === focusDeliveryId)),
    )
    if (focusIndex >= 0) setLineIndex(focusIndex)
  }

  /**
   * Tiền theo SL ĐẶT — tính tại chỗ để người dùng thấy ngay khi gõ. bao-CR-364: tiền tệ
   * dán nhãn lấy từ các DÒNG (đầu phiếu chỉ là mặc định); trộn nhiều loại tiền thì ba
   * dòng tổng là bản quy đổi VNĐ.
   */
  const orderTotals = useMemo(
    () =>
      summarizeOrderTotals({
        currency: draft?.currency ?? '',
        exchange_rate: draft?.exchange_rate ?? 0,
        items: draft?.items ?? [],
      }),
    [draft?.currency, draft?.exchange_rate, draft?.items],
  )

  /** bao-CR-319: đơn nhập khẩu — tổng tiền hàng đã quy đổi VNĐ (dòng để trống thì theo đơn). */
  const baseTotal = useMemo(() => {
    if (!draft || !isImportOrder(draft)) return 0
    return draft.items.reduce((sum, item) => sum + displayLineBaseAmount(item, draft), 0)
  }, [draft])

  /** Đơn NK có dòng ngoại tệ chưa nhập tỷ giá thì tổng quy đổi đang thiếu — phải nói rõ. */
  const missingRateCount = useMemo(() => {
    if (!draft || !isImportOrder(draft)) return 0
    return draft.items.filter((item) => isMissingExchangeRate(item, draft)).length
  }, [draft])

  /** Cước vận chuyển gom từ các lần giao — để giải thích con số ở dưới bảng. */
  const shipping = useMemo(() => summarizeShipping(draft?.items ?? []), [draft?.items])

  // CR-268: đơn có tiền TRẢ TRƯỚC chưa đối trừ thì báo ngay dưới bảng dòng hàng.
  // Gác quyền `payment_request.read` kẻo người không xem được YCTT ăn toast 403.
  const { data: prepayHangingData } = usePrepayHanging(
    { supplier_code: serverData?.supplier_code ?? '', po_code: serverData?.code ?? '' },
    { enabled: !isNew && Boolean(serverData?.code) && can('payment_request', 'read') },
  )
  const prepayHangingTotal = prepayHangingData?.total ?? 0

  /** Giỏ phiếu giao của riêng dòng đang mở, đổi về khóa theo chỉ số lần giao. */
  const linePendingFiles = useMemo(
    () => (lineIndex === null ? {} : pendingFilesOfLine(pendingFiles, lineIndex)),
    [pendingFiles, lineIndex],
  )

  //  bao-CR-499: ô "Trưởng phòng phê duyệt" chỉ liệt kê người DUYỆT ĐƯỢC đơn này. Gọi TRƯỚC
  //  các nhánh return sớm bên dưới (luật hook).
  const approverSource = draft ?? serverData
  const { data: approverData } = useApproverCandidates(
    'purchase-orders',
    purchaseOrderId,
    {
      department: approverSource?.department ?? '',
      department_id: approverSource?.department_id ?? 0,
      company_id: approverSource?.company_id ?? 0,
      handler_dept_id: approverSource?.handler_dept_id ?? 0,
    },
    isNew || ['draft', 'rejected'].includes(approverSource?.status ?? ''),
  )

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-20 w-full" />
        <Skeleton className="h-[540px] w-full" />
      </PageContainer>
    )
  }

  if (!isNew && (isError || !serverData)) {
    return (
      <ErrorState
        title="Không mở được đơn mua hàng"
        description="Đơn có thể đã bị xóa, hoặc ngoài phạm vi dữ liệu bạn được xem."
      >
        <Button variant="outline" onClick={() => navigate(appRoutes.procurement.purchaseOrders)}>
          <ArrowLeft />
          Về danh sách
        </Button>
      </ErrorState>
    )
  }

  const data = draft ?? serverData ?? createEmptyPurchaseOrder()
  /** Đơn đã chốt/hủy — khóa cứng, kể cả hồ sơ chứng từ cũng theo mốc này. */
  const locked = isPurchaseOrderLocked(data.status)
  const approved = isPurchaseOrderApproved(data.status)
  const canWrite = can('purchase_order', isNew ? 'create' : 'write')
  /**
   * Sửa được nội dung đơn: chỉ khi đơn còn Nháp / Bị trả lại (CR-108). Gửi duyệt
   * xong là chốt nội dung — đang chờ duyệt mà vẫn sửa được thì người duyệt đọc
   * một đằng, ký một nẻo; duyệt rồi lại càng không.
   */
  const headerEditable = (isNew || ['draft', 'rejected'].includes(data.status)) && canWrite
  /** Đơn đã duyệt: chỉ mở các ô phát sinh sau khi duyệt, nằm trong popup chi tiết dòng. */
  const afterApproveEditable = !isNew && approved && canWrite
  const progressEditable = !isNew && isDeliveryStage(data.status) && can('purchase_order', 'write')
  /** Chưa nhận hàng thì mới hủy duyệt được — khớp điều kiện backend chặn. */
  const canUnapprove =
    !isNew &&
    approved &&
    can('purchase_order', 'approve') &&
    !data.items.some((item) => (item.qty_received ?? 0) > 0)
  const canDelete = !isNew && ['draft', 'rejected'].includes(data.status)
  const purchaseRequestId = purchaseRequestsData?.items.find(
    (request) => request.code === data.pr_code,
  )?.id

  function patch(changes: Partial<PurchaseOrderDetail>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  /**
   * Lưu đơn. `submitAfterSave` = "Gửi duyệt" khi đơn còn sửa được (bao-CR-590): LƯU phần
   * đang sửa trước rồi mới gửi. Trước đây nút Gửi duyệt chỉ gọi `/submit` — máy chủ gửi
   * bản CŨ, rồi trang nạp lại bản cũ đè lên bản nháp, người dùng mất trắng phần vừa sửa.
   * Trả `true` khi lưu (và gửi, nếu có) xong.
   */
  async function handleSave(submitAfterSave = false): Promise<boolean> {
    const message = validatePurchaseOrder(data, submitAfterSave)
    if (message) {
      toast.error(message)
      return false
    }
    // bao-CR-308: trùng mã được phép (tách dòng theo bộ chứng từ) — chỉ hỏi xác
    // nhận để chặn gõ nhầm mã, không chặn cứng nữa.
    const duplicated = duplicatePurchaseOrderCodes(data)
    if (duplicated.length) {
      const ok = await confirmDialog({
        title: 'Mã hàng trùng trên đơn',
        tone: 'default',
        confirmLabel: 'Vẫn lưu',
        cancelLabel: 'Quay lại sửa',
        message:
          `Các mã sau xuất hiện trên NHIỀU dòng: ${duplicated.join(', ')}.\n\n` +
          'Nếu cố ý tách dòng theo bộ chứng từ (cùng mã nhưng khác lô / khác Tên trên hóa đơn ' +
          '/ số hóa đơn) thì bấm Vẫn lưu — tiến độ trên YCMH vẫn cộng gộp đúng theo mã.\n\n' +
          'Nếu chỉ là gõ nhầm mã thì bấm Quay lại sửa.',
      })
      if (!ok) return false
    }
    //  duoc-CR-741 (bản v1): Ngày dự kiến có hàng lệch với YCMH nguồn thì nhắc — YCMH KHÔNG tự
    //  đổi theo, người lập đối chiếu rồi tự quyết. Chỉ nhắc, không chặn.
    const dateDiffs = findExpectedDateDiffs(data.items)
    if (dateDiffs.length) {
      const ok = await confirmDialog({
        title: 'Lệch ngày dự kiến có hàng',
        tone: 'default',
        confirmLabel: 'Vẫn lưu',
        cancelLabel: 'Quay lại sửa',
        message: buildExpectedDateDiffMessage(data.pr_code, dateDiffs),
      })
      if (!ok) return false
    }
    const saved = await savePurchaseOrder.mutateAsync({
      id: isNew ? undefined : purchaseOrderId,
      payload: toPurchaseOrderPayload(data),
    })
    markSubmitted()
    await flushPendingDeliveryFiles(saved)
    if (isNew) {
      navigate(appRoutes.procurement.purchaseOrderDetail(saved.id), { replace: true })
      return true
    }
    if (submitAfterSave) await runAction.mutateAsync({ action: 'submit' })
    return true
  }

  /**
   * Bấm "Gửi duyệt". Đơn còn sửa được thì đi đường LƯU RỒI GỬI (bao-CR-590). Chặn bấm đúp
   * bằng ref đổi ngay trong tick — `disabled={isPending}` chỉ có hiệu lực ở lượt vẽ sau.
   */
  async function handleSubmit() {
    if (submittingRef.current) return
    submittingRef.current = true
    try {
      if (headerEditable) await handleSave(true)
      else await handleAction('submit')
    } finally {
      submittingRef.current = false
    }
  }

  /** Đẩy phiếu giao đang chờ lên đúng lần giao vừa được server trả về. */
  async function flushPendingDeliveryFiles(saved: PurchaseOrderDetail) {
    const buckets = Object.entries(pendingFiles)
    if (!buckets.length) return

    const batches = buckets
      .map(([key, files]) => {
        const { lineIndex: line, deliveryIndex } = parseDeliveryFileKey(key)
        return { deliveryId: findSavedDeliveryId(data, saved, line, deliveryIndex), files }
      })
      .filter((batch) => batch.deliveryId > 0 && batch.files.length > 0)

    // Dọn giỏ trước: dù có lần giao nào không dò ra id thì cũng đừng để tệp cũ
    // treo lại rồi tải nhầm sang lần lưu sau.
    setPendingFiles({})
    if (!batches.length) return
    await uploadDeliveryFiles.mutateAsync({ purchaseOrderId: saved.id, batches })
  }

  async function handleAction(action: PurchaseOrderAction) {
    if (
      action === 'return' ||
      action === 'reject' ||
      action === 'unapprove' ||
      action === 'cancel'
    ) {
      setReasonFor(action)
      return
    }
    // Chặn trước ở màn thay vì để API trả 400: câu của backend gộp hết dòng
    // thiếu vào một dòng chữ dài, đọc trong hộp thoại lỗi rất khó dò. Đây chỉ là
    // bản sao cho êm — backend vẫn kiểm lại (CR-095).
    if (action === 'submit') {
      const message = validatePurchaseOrder(data, true)
      if (message) {
        toast.error(message)
        return
      }
    }
    // duoc-CR-741: Hoàn thành LUÔN hỏi lại như bản v1 (chốt xong là khóa đơn). Hai lời nhắc
    // cũ của v2 — chi phí thu mua còn nợ (bao-CR-319), dòng chi phí chưa quyết toán
    // (bao-CR-453) — nối vào cùng hộp thay vì bật hai hộp liền nhau; vẫn không chặn.
    if (action === 'complete') {
      const proceed = await confirmDialog({
        message: buildCompleteConfirmMessage(data),
        confirmLabel: 'Hoàn thành',
        tone: 'default',
      })
      if (!proceed) return
    }
    // duoc-CR-741: Mở lại đơn đã Hoàn thành cũng hỏi lại như bản v1. Tông đỏ là CỐ Ý: v1 gọi
    // `askConfirm` không truyền `danger`, mà mặc định của v1 là `danger: true` (nút đỏ).
    if (action === 'reopen') {
      const proceed = await confirmDialog({
        message: PO_REOPEN_CONFIRM_MESSAGE,
        confirmLabel: 'Mở lại',
      })
      if (!proceed) return
    }
    await runAction.mutateAsync({ action })
  }

  /**
   * Nút đầu trang theo ĐÚNG THỨ TỰ BẢN V1 (duoc-CR-737) — người dùng dời từ v1 sang tìm
   * nút ở chỗ cũ. Tiện ích (trái vạch ngăn): Tạo yêu cầu thanh toán · In · Hủy đơn ·
   * Xóa. Quy trình (phải): Gửi duyệt · Duyệt · Trả về · Từ chối · Hủy duyệt · Hoàn
   * thành · Mở lại · Lưu / Tạo đơn — Lưu LUÔN đứng cuối, mép phải. Nút Nhân bản cả đơn
   * đã bỏ khỏi đầu trang (duoc-CR-737) — chép đơn dùng biểu tượng chép ở màn danh sách.
   *
   * Nút viền mang MÀU của nút cùng tên ở v1 (`ACTION_TONE_CLASS`): Tạo yêu cầu thanh
   * toán, Hoàn thành chữ xanh; Trả về, Hủy duyệt hổ phách; Hủy đơn, Từ chối, Xóa đỏ;
   * In, Mở lại để trơn.
   *
   * `primary` = nút nền đặc (Gửi duyệt · Duyệt · Lưu): khổ hẹp vẫn để ngoài, còn lại vào
   * `⋯`. Mỗi nút dựng MỘT LẦN — nhiều nút kéo theo state / mutation riêng (hộp thanh
   * toán, `DeleteConfirmButton`), chép hai bản là hai bộ state song song cho một lệnh.
   */
  const headerActions: HeaderActionList = [
    /*
      CỐ Ý không gác theo `unpaid_total > 0.01`: đơn chưa nhận hàng thì chưa
      có công nợ, nhưng vẫn phải lập được phiếu THANH TOÁN TRƯỚC (CR-067) —
      hộp thoại tự đổi sang luồng đó. Bản v1 cũng đã bỏ điều kiện này.
    */
    !isNew &&
      ['approved', 'partial', 'received', 'completed'].includes(data.status) &&
      can('payment_request', 'create') && {
        key: 'payment-request',
        group: 'utility',
        node: (
          <Button
            variant="outline"
            className={ACTION_TONE_CLASS.accent}
            onClick={() => setPaymentOpen(true)}
          >
            <Receipt />
            Tạo yêu cầu thanh toán
          </Button>
        ),
      },
    /* bao-CR-498: gom mọi bản in vào MỘT nút "In" thả xuống như bản v1 — trước đó năm nút
       in rời chiếm cả hàng tiêu đề, người dùng phải đọc từng nút để tìm bản cần in. */
    !isNew &&
      can('purchase_order', 'print') && {
        key: 'print',
        group: 'utility',
        node: (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" className={ACTION_TONE_CLASS.neutral}>
                <Printer />
                In
                <ChevronDown className="size-4 opacity-60" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild>
                <Link to={appRoutes.procurement.purchaseOrderPrint(data.id)} onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)} target="_blank" rel="noreferrer">
                  <Printer />
                  In Đơn đặt hàng
                </Link>
              </DropdownMenuItem>
              {/* bao-CR-322: mẫu nội bộ / gửi kế toán. Cùng trang in với mục trên, vào bằng
                  đường dẫn riêng nên mở ra là đã đúng mẫu, không phải bấm công tắc. */}
              <DropdownMenuItem asChild>
                <Link to={appRoutes.procurement.purchaseOrderGoodsPrint(data.id)} onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)} target="_blank" rel="noreferrer">
                  <ReceiptText />
                  In Đơn mua hàng
                </Link>
              </DropdownMenuItem>
              {/* bao-CR-319: đơn nhập khẩu có bản in riêng — nguyên tệ + quy đổi + chi phí lô hàng.
                  bao-CR-357: báo cáo giá vốn của RIÊNG lô hàng này, lọc sẵn theo mã đơn. */}
              {isImportOrder(data) && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to={appRoutes.procurement.purchaseOrderImportPrint(data.id)} onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)} target="_blank" rel="noreferrer">
                      <Ship />
                      In Đơn nhập khẩu
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link
                      to={`${appRoutes.procurement.importLandedCostPrint}?codes=${encodeURIComponent(data.code || '')}`}
                      onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)}
                      target="_blank"
                      rel="noreferrer"
                    >
                      <Printer />
                      In Báo cáo giá vốn
                    </Link>
                  </DropdownMenuItem>
                </>
              )}
              {/* bao-CR-314: chỉ hiện khi đơn có gắn YCMH. Bản in chỉ gồm những dòng hàng
                  có trên đơn này — không cần quyền đọc YCMH vì cổng là quyền in ĐƠN. */}
              {(data.pr_code || '').trim() && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem asChild>
                    <Link to={appRoutes.procurement.purchaseRequestPrintFromPo(data.id)} onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)} target="_blank" rel="noreferrer">
                      <FileText />
                      In Phiếu yêu cầu
                    </Link>
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        ),
      },
    /* duoc-CR-741: như bản v1, đơn đã có dòng Hoàn thành thì không hiện nút Hủy (backend
       cũng chặn) — để nút ở đó chỉ mời người dùng gõ lý do rồi ăn lỗi. */
    !isNew &&
      isDeliveryStage(data.status) &&
      can('purchase_order', 'cancel') &&
      !data.items.some((item) => item.progress_status === 'completed') && {
        key: 'cancel',
        group: 'utility',
        node: (
          <Button
            variant="outline"
            className={ACTION_TONE_CLASS.danger}
            onClick={() => void handleAction('cancel')}
          >
            <Ban />
            Hủy
          </Button>
        ),
      },
    canDelete &&
      can('purchase_order', 'delete') && {
        key: 'delete',
        group: 'utility',
        node: (
          <DeleteConfirmButton
            recordName={data.code || `#${data.id}`}
            pending={deletePurchaseOrder.isPending}
            className={ACTION_TONE_CLASS.danger}
            label="Xóa đơn"
            title="Xác nhận"
            description="Xóa đơn mua hàng này?"
            confirmLabel="Đồng ý"
            onConfirm={async () => {
              await deletePurchaseOrder.mutateAsync(data.id)
              navigate(appRoutes.procurement.purchaseOrders)
            }}
          />
        ),
      },
    !isNew &&
      ['draft', 'rejected'].includes(data.status) &&
      canWrite && {
        key: 'submit',
        primary: true,
        node: (
          <Button
            onClick={() => void handleSubmit()}
            disabled={runAction.isPending || savePurchaseOrder.isPending}
          >
            <Send />
            Gửi duyệt
          </Button>
        ),
      },
    ...(!isNew && data.status === 'submitted' && can('purchase_order', 'approve')
      ? [
          {
            key: 'approve',
            primary: true,
            node: (
              <Button onClick={() => void handleAction('approve')} disabled={runAction.isPending}>
                <Check />
                Duyệt
              </Button>
            ),
          },
          {
            key: 'return',
            node: (
              <Button
                variant="outline"
                className={ACTION_TONE_CLASS.warning}
                onClick={() => void handleAction('return')}
              >
                <CornerUpLeft />
                Trả về
              </Button>
            ),
          },
          {
            key: 'reject',
            node: (
              <Button
                variant="outline"
                className={ACTION_TONE_CLASS.danger}
                onClick={() => void handleAction('reject')}
              >
                <Ban />
                Từ chối
              </Button>
            ),
          },
        ]
      : []),
    canUnapprove && {
      key: 'unapprove',
      node: (
        <Button
          variant="outline"
          className={ACTION_TONE_CLASS.warning}
          onClick={() => void handleAction('unapprove')}
        >
          <RotateCcw />
          Hủy duyệt
        </Button>
      ),
    },
    /* Chỉ hiện từ khi có hàng về. Đơn mới duyệt mà chưa nhận dòng nào thì
       backend chặn `/complete` (400 "Còn N dòng chưa Hoàn thành/Hủy") —
       để nút ở đó chỉ tổ mời người dùng bấm vào một lỗi. */
    !isNew &&
      ['partial', 'received'].includes(data.status) &&
      canWrite && {
        key: 'complete',
        node: (
          <Button
            variant="outline"
            className={ACTION_TONE_CLASS.accent}
            onClick={() => void handleAction('complete')}
          >
            <CircleCheck />
            Hoàn thành
          </Button>
        ),
      },
    !isNew &&
      data.status === 'completed' &&
      canWrite && {
        key: 'reopen',
        node: (
          <Button variant="outline" className={ACTION_TONE_CLASS.neutral} onClick={() => void handleAction('reopen')}>
            <LockOpen />
            Mở lại
          </Button>
        ),
      },
    /* Đơn đã duyệt vẫn cần nút Lưu: mấy ô mở sau khi duyệt nằm trong popup
       chi tiết dòng, sửa xong phải ghi xuống được. */
    (headerEditable || afterApproveEditable) && {
      key: 'save',
      primary: true,
      node: (
        <Button onClick={() => void handleSave()} disabled={savePurchaseOrder.isPending}>
          {savePurchaseOrder.isPending ? <Loader2 className="animate-spin" /> : <Save />}
          {isNew ? 'Tạo' : 'Lưu'}
        </Button>
      ),
    },
  ]

  /**
   * Đổi tiến độ một dòng — chung cho nút trên bảng lẫn trong hộp chi tiết dòng (duoc-CR-741).
   * Tạm ngưng / Hủy đơn bắt buộc nêu lý do; tiếp tục thì gọi thẳng.
   */
  function handleProgressChange(item: PurchaseOrderItem, status: string) {
    if (status === '__resume__') {
      void setItemProgress.mutateAsync({ itemId: item.id ?? 0, status })
      return
    }
    setProgressFor({ item, status })
  }

  /** Bỏ các dòng đang tick khỏi đơn (chỉ trên màn hình — bấm Lưu mới ghi xuống). */
  function removeSelectedLines() {
    const drop = new Set(lineSelection.selectedIndexes)
    patch({ items: data.items.filter((_, index) => !drop.has(index)) })
    //  Báo từng chỉ số từ CAO xuống THẤP: phiếu giao chờ lưu giữ theo chỉ số dòng.
    for (const index of [...lineSelection.selectedIndexes].sort((a, b) => b - a)) {
      setPendingFiles((current) => shiftPendingAfterLineRemove(current, index))
    }
    lineSelection.clear()
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      {/*  Khung dải đầu dùng chung — luật "cụm nút ở lại hàng đầu, huy hiệu mới là thứ
           xuống dòng" và "nhóm phụ dựng một lần" nằm ở `DetailPageHeader`. */}
      <DetailPageHeader
        backTo={appRoutes.procurement.purchaseOrders}
        backLabel="Về danh sách đơn mua hàng"
        title={isNew ? 'Tạo Đơn mua hàng mới' : data.code || 'Đơn nháp'}
        badges={
          <>
            {!isNew && <StatusBadge status={data.status} labels={PO_STATUS_LABELS} />}
            {data.is_urgent && (
              <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
                Đơn gấp
              </Badge>
            )}
          </>
        }
        actions={headerActions}
      />

      <div className="min-w-0 space-y-4">
        <PurchaseOrderInfoCard
          data={data}
          editable={headerEditable}
          misaEditable={afterApproveEditable}
          companies={companiesData?.items}
          suppliers={(suppliersData?.items ?? []).filter(
            (supplier) => supplier.supplier_type !== 'transport',
          )}
          employees={employeesData?.items}
          approverCandidates={approverData?.items}
          canPickNspt={can('purchase_order', 'approve')}
          purchaseRequestId={purchaseRequestId}
          onChange={patch}
        />

        <Card className="gap-4 py-4">
          {/* Cùng khuôn tiêu đề với mọi thẻ khác — xem ghi chú `pb-3!` ở
              `purchase-request-attachments-card.tsx`. */}
          <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">Dòng hàng</CardTitle>
            {/*  duoc-CR-737: cụm nút của bảng dòng ở góc phải tiêu đề thẻ như bản v1 —
                 Xóa đã chọn (n) · Thêm dòng. */}
            <div className="flex flex-wrap items-center justify-end gap-2">
              {lineSelection.selection && (
                <BulkDeleteButton
                  size="sm"
                  count={lineSelection.selectedIndexes.length}
                  unitLabel="dòng"
                  title="Xác nhận"
                  description={`Xóa ${lineSelection.selectedIndexes.length} dòng đã chọn? Dòng bỏ khỏi đơn ngay trên màn hình, bấm Lưu mới ghi xuống.`}
                  confirmLabel="Đồng ý"
                  onConfirm={removeSelectedLines}
                />
              )}
              {headerEditable && (
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() =>
                    patch({ items: [...data.items, createEmptyPurchaseOrderItem(data.vat_rate)] })
                  }
                >
                  <Plus />
                  Thêm dòng
                </Button>
              )}
              {headerEditable && (
                <PurchaseOrderAddManyLinesButton
                  onAdd={(count) =>
                    patch({
                      items: [
                        ...data.items,
                        ...Array.from({ length: count }, () =>
                          createEmptyPurchaseOrderItem(data.vat_rate),
                        ),
                      ],
                    })
                  }
                />
              )}
            </div>
          </CardHeader>
          <CardContent className="space-y-4 px-4">
            {overOrders.length > 0 && (
              <div className="rounded-md border border-warning/40 bg-warning/10 px-3 py-2 text-xs">
                <p className="flex items-center gap-1.5 font-medium">
                  <AlertTriangle className="size-3.5" />
                  Số lượng đặt vượt yêu cầu của YCMH {data.pr_code} — chỉ là nhắc, vẫn tạo đơn được
                </p>
                {overOrders.map((line) => (
                  <p key={line.code}>
                    {line.progress.name} ({line.code}): yêu cầu {formatQty(line.progress.requested)} ·{' '}
                    {describeOrdered(line.progress)} · đơn này {formatQty(line.qty)} →{' '}
                    <b>tổng vượt {formatQty(line.over)}</b>
                  </p>
                ))}
                <p className="text-muted-foreground">
                  Chỉ cần mua thêm phần thiếu thì sửa lại cột SL đặt NCC trước khi bấm Tạo.
                </p>
              </div>
            )}
            {afterApproveEditable && (
              <p className="rounded-md border border-info/30 bg-info/8 px-3 py-1.5 text-xs text-muted-foreground">
                {/*  Khổ điện thoại không còn cột Hành động — bảng đã thành thẻ, chạm thẻ mở hộp chi tiết dòng. */}
                Đơn đã duyệt — nội dung đã ký khóa lại.{' '}
                {isMobile ? 'Chạm vào thẻ dòng hàng' : 'Mở nút bút chì ở cột Hành động'} để sửa:{' '}
                {PO_FIELDS_EDITABLE_AFTER_APPROVE}.{PO_MISA_AFTER_APPROVE_HINT}
                {canUnapprove && ' Muốn đổi phần khác thì bấm Hủy duyệt để đưa đơn về Nháp.'}
              </p>
            )}
            <PurchaseOrderItemsTable
              items={data.items}
              order={data}
              editable={headerEditable}
              selection={lineSelection.selection}
              progressEditable={progressEditable}
              onChange={(items) => patch({ items })}
              onOpenDetail={setLineIndex}
              //  Dòng chưa lưu khóa tick theo chỉ số: chèn / bỏ một dòng làm dấu tick trôi sang
              //  dòng khác, *Xóa đã chọn* xóa nhầm (rà mã duoc-CR-741) — bỏ hết dấu tick.
              onLineRemoved={(index) => {
                setPendingFiles((current) => shiftPendingAfterLineRemove(current, index))
                lineSelection.clear()
              }}
              onLineDuplicated={(index) => {
                setPendingFiles((current) => shiftPendingAfterLineInsert(current, index))
                lineSelection.clear()
              }}
              lineReport={isNew ? undefined : lineReport}
              onOpenLineReport={(progress) => reportCardRef.current?.focusItem(progress.itemId)}
              onProgressChange={handleProgressChange}
            />
            <DocumentMoneyTotals
              subtotal={orderTotals.subtotal}
              vat={orderTotals.vat}
              total={orderTotals.total}
              subtotalLabel={
                !isImportOrder(data)
                  ? 'Tiền hàng theo SL đặt (chưa VAT)'
                  : orderTotals.mixed
                    ? 'Tiền hàng theo SL đặt (quy đổi VNĐ)'
                    : `Tiền hàng theo SL đặt (nguyên tệ ${orderTotals.currency})`
              }
              totalLabel={
                !isImportOrder(data)
                  ? 'Tổng đơn đặt (gồm VAT)'
                  : orderTotals.mixed
                    ? 'Tổng đơn đặt (quy đổi VNĐ)'
                    : `Tổng đơn đặt (nguyên tệ ${orderTotals.currency})`
              }
              currency={isImportOrder(data) ? orderTotals.currency : undefined}
            />
            {isImportOrder(data) && (
              <div className="ml-auto w-full max-w-sm space-y-1 text-sm">
                {orderTotals.mixed ? (
                  // Đơn trộn nhiều loại tiền: ba dòng tổng ở trên đã là bản quy đổi,
                  // lặp lại "Tổng quy đổi" là hai con số giống nhau — thay bằng câu nói rõ.
                  <p className="text-right text-xs text-muted-foreground">
                    Đơn có nhiều loại tiền — các dòng tổng đã quy đổi VNĐ theo tỷ giá từng
                    dòng (trống thì theo tỷ giá đơn).
                  </p>
                ) : (
                  <p className="flex justify-between gap-4">
                    <span className="text-muted-foreground">Tổng quy đổi (VNĐ)</span>
                    <span
                      className="font-semibold text-navy tabular-nums dark:text-foreground"
                      title="Cộng thành tiền quy đổi của từng dòng theo tỷ giá dòng (trống thì theo tỷ giá đơn)."
                    >
                      {formatMoney(baseTotal)} đ
                    </span>
                  </p>
                )}
                {missingRateCount > 0 && (
                  <p className="flex items-center justify-end gap-1.5 text-xs text-warning">
                    <AlertTriangle className="size-3.5" />
                    {missingRateCount} dòng ngoại tệ chưa có tỷ giá — nhập tỷ giá ở đầu đơn
                    hoặc trong chi tiết dòng để quy đổi.
                  </p>
                )}
              </div>
            )}
            {!isNew && (
              <div className="space-y-1 text-right text-xs text-muted-foreground">
                <p>
                  <span title="Tiền hàng tính theo SỐ LƯỢNG THỰC NHẬN (gồm VAT) — khác tổng đơn đặt ở trên khi chưa nhận đủ.">
                    Đã nhận: {data.total.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ
                  </span>{' '}
                  ·{' '}
                  <span title="Cộng cước ghi ở TỪNG LẦN GIAO của các dòng hàng. Đây là khoản trả cho nhà xe, không nằm trong tổng tiền đơn hàng.">
                    Cước vận chuyển:{' '}
                    {data.shipping_total.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ
                    {shipping.chargedCount > 0 && ` (${shipping.chargedCount} lần giao)`}
                  </span>
                </p>
                {shipping.missingCarrierCount > 0 && (
                  <p className="flex items-center justify-end gap-1.5 text-amber-600 dark:text-amber-500">
                    <AlertTriangle className="size-3.5" />
                    {shipping.missingCarrierCount} lần giao có cước nhưng chưa chọn Đơn vị vận
                    chuyển — cước đó chưa vào công nợ.
                  </p>
                )}
                {/* CR-268: tiền trả trước còn treo của đơn — nhận hàng sinh công nợ
                    tới đâu hệ thống tự đối trừ tới đó, hết treo thì dòng này biến mất. */}
                {prepayHangingTotal > 0.01 && (
                  <p className="flex items-center justify-end gap-1.5 text-warning">
                    <AlertTriangle className="size-3.5" />
                    <span title="Tiền phiếu thanh toán trước đã chi cho đơn này nhưng chưa đối trừ vào công nợ. Khi nhận hàng sinh công nợ, hệ thống tự trừ dần.">
                      Đã trả trước{' '}
                      {prepayHangingTotal.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ —
                      chưa đối trừ vào công nợ.
                    </span>
                  </p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* bao-CR-602: Báo cáo thực hiện của ĐƠN (riêng từng đơn, không nối YCBG) — nút
            dòng hàng bám theo dòng đơn; ai sửa được đơn thì sửa được báo cáo; đơn Hoàn
            thành / Hủy thì chỉ đọc (backend khóa). */}
        {!isNew && (
          <SurveyReportCard
            ref={reportCardRef}
            entity="purchase_order"
            ownerId={purchaseOrderId}
            canEdit={!locked && can('purchase_order', 'write')}
            itemsLocked
          />
        )}

        {/* bao-CR-453: thẻ chi phí thu mua hiện cho MỌI loại đơn (trước: chỉ nhập khẩu). */}
        <PurchaseOrderImportCostsCard
          order={data}
          // Bảng chi phí mở cả khi đơn đã duyệt (cước tàu, thuế về sau) — giống v1.
          editable={headerEditable || afterApproveEditable}
          isNew={isNew}
          suppliers={suppliersData?.items ?? []}
          onChange={(import_costs) => patch({ import_costs })}
        />

        {!isNew && <PurchaseOrderPaymentRequestsCard poCode={data.code} />}

        <DocumentAttachmentsCard
          entity="purchase_order"
          entityId={purchaseOrderId}
          canManage={!locked && can('purchase_order', 'write')}
          documentStatus={isNew ? '' : data.document_status || 'none'}
          //  duoc-CR-741: đổi tình trạng hồ sơ bằng menu ở tiêu đề thẻ này như bản v1. Sửa được
          //  cả khi đơn đã Hoàn thành (chứng từ thường về sau) — endpoint riêng, không qua Lưu.
          documentStatusEditable={!isNew && can('purchase_order', 'write')}
          onDocumentStatusChange={(value) => setDocumentStatus.mutate(value)}
          v1Wording
        />

        {/* Thẻ tự ẩn khi thiếu quyền / đang nạp / không có hồ sơ nào khớp
            điều kiện áp dụng. Cờ ngoài là công tắc TẠM ẨN cả phân hệ Hồ sơ
            (21/09/2026) — xem `DOSSIER_UI_ENABLED`. */}
        {DOSSIER_UI_ENABLED && (
          <RequiredDossiersCard
            docKind={DOC_KINDS.PURCHASE_ORDER}
            docId={purchaseOrderId || undefined}
          />
        )}

        {!isNew && (
          <>
            <DocumentComments entity="purchase_order" entityId={purchaseOrderId} />
            <AuditTimeline
              entity="purchase_order"
              entityId={purchaseOrderId}
              showMessage
              dense
            />
          </>
        )}
      </div>

      <PurchaseOrderPaymentDialog open={paymentOpen} order={data} onOpenChange={setPaymentOpen} />

      <PurchaseOrderLineDialog
        item={lineIndex === null ? null : (data.items[lineIndex] ?? null)}
        order={data}
        lineNumber={(lineIndex ?? 0) + 1}
        open={lineIndex !== null}
        editable={headerEditable}
        afterApproveEditable={afterApproveEditable}
        deliveryEditable={progressEditable}
        progressEditable={progressEditable}
        onProgressChange={handleProgressChange}
        // Đính kèm phiếu giao mở cả khi đơn đã hoàn thành (chỉ chặn khi hủy):
        // chứng từ thường về sau ngày chốt đơn.
        attachEditable={
          !isNew && data.status !== 'cancelled' && can('purchase_order', 'write')
        }
        purchaseOrderId={purchaseOrderId}
        carriers={(suppliersData?.items ?? []).filter(
          (supplier) => supplier.supplier_type === 'transport',
        )}
        orderDate={data.order_date || ''}
        pendingFiles={linePendingFiles}
        onChange={(item) => {
          if (lineIndex === null) return
          patch({
            items: data.items.map((current, index) => (index === lineIndex ? item : current)),
          })
        }}
        onPendingFilesChange={(deliveryIndex, files) => {
          if (lineIndex === null) return
          setPendingFiles((current) =>
            setPendingDeliveryFiles(current, lineIndex, deliveryIndex, files),
          )
        }}
        onDeliveryRemoved={(deliveryIndex) => {
          if (lineIndex === null) return
          setPendingFiles((current) =>
            shiftPendingAfterDeliveryRemove(current, lineIndex, deliveryIndex),
          )
        }}
        onOpenChange={(open) => {
          if (!open) setLineIndex(null)
        }}
        onSave={() => {
          //  Dialog đóng ngay khi bấm "Lưu đơn" nên không chờ API: chỉ tính "gửi" khi dữ liệu qua được bước kiểm ở màn.
          if (!validatePurchaseOrder(data, false)) markLineSubmitted()
          void handleSave()
        }}
      />

      <PurchaseOrderReasonDialog
        open={reasonFor !== null}
        title={reasonFor ? REASON_ACTIONS[reasonFor].title : ''}
        description={reasonFor ? REASON_ACTIONS[reasonFor].description : ''}
        confirmLabel={reasonFor ? REASON_ACTIONS[reasonFor].confirmLabel : undefined}
        pending={runAction.isPending}
        destructive={reasonFor === 'reject' || reasonFor === 'cancel'}
        onClose={() => setReasonFor(null)}
        onConfirm={async (reason) => {
          if (!reasonFor) return
          await runAction.mutateAsync({ action: reasonFor, reason })
          setReasonFor(null)
        }}
      />

      <PurchaseOrderReasonDialog
        open={progressFor !== null}
        title={LINE_PROGRESS_REASON_LABELS[progressFor?.status ?? ''] ?? ''}
        confirmLabel={LINE_PROGRESS_REASON_LABELS[progressFor?.status ?? '']}
        description={`Lý do ${(LINE_PROGRESS_REASON_LABELS[progressFor?.status ?? ''] ?? '').toLowerCase()} — sản phẩm: ${progressFor?.item.product_name || progressFor?.item.product_code || ''}`}
        pending={setItemProgress.isPending}
        destructive={progressFor?.status === 'cancelled'}
        onClose={() => setProgressFor(null)}
        onConfirm={async (reason) => {
          if (!progressFor) return
          await setItemProgress.mutateAsync({
            itemId: progressFor.item.id ?? 0,
            status: progressFor.status,
            reason,
          })
          setProgressFor(null)
        }}
      />
    </PageContainer>
  )
}

/**
 * Dò id của LẦN GIAO vừa lưu, ứng với lần giao thứ `deliveryIndex` của dòng thứ
 * `lineIndex` trên bản nháp.
 *
 * Không khớp theo chỉ số mảng: backend trả dòng và lần giao theo id tăng dần,
 * nên dòng mới chèn giữa bản nháp sẽ rơi xuống cuối danh sách trả về. Khớp theo
 * id (dòng đã lưu) rồi tới mã hàng, và chỉ xét những lần giao MỚI xuất hiện —
 * các lần giao cũ đã có id trên bản nháp thì không phải đích của tệp đang chờ.
 */
function findSavedDeliveryId(
  draft: PurchaseOrderDetail,
  saved: PurchaseOrderDetail,
  lineIndex: number,
  deliveryIndex: number,
): number {
  const draftItem = draft.items[lineIndex]
  const draftDelivery = draftItem?.deliveries?.[deliveryIndex]
  if (!draftItem || !draftDelivery) return 0

  const savedItem =
    (draftItem.id ? saved.items.find((item) => item.id === draftItem.id) : undefined) ??
    (draftItem.product_code
      ? saved.items.find((item) => item.product_code === draftItem.product_code)
      : undefined) ??
    saved.items[lineIndex]
  if (!savedItem) return 0

  const knownIds = new Set(
    draftItem.deliveries.map((delivery) => delivery.id).filter((id): id is number => !!id),
  )
  const fresh = savedItem.deliveries.filter((delivery) => !knownIds.has(delivery.id ?? 0))
  const rank = draftItem.deliveries
    .filter((delivery) => !delivery.id)
    .indexOf(draftDelivery)

  const match =
    fresh.find((delivery) => delivery.delivery_no === draftDelivery.delivery_no) ??
    (rank >= 0 ? fresh[rank] : undefined)
  return match?.id ?? 0
}

/** Dòng trống — VAT lấy theo mức mặc định của đơn (`vat_rate` là thập phân). */
function createEmptyPurchaseOrderItem(vatRate: number): PurchaseOrderItem {
  return {
    product_code: '',
    product_name: '',
    invoice_name: '',
    item_group: '',
    spec: '',
    fg_code: '',
    fg_name: '',
    invoice_no: '',
    invoice_date: '',
    document_delivery_date: '',
    supplier_ready: true,
    required_date: '',
    // Để rỗng có chủ đích: backend tự điền theo YCMH nguồn / thời gian chuẩn của
    // phân loại. Tự điền hụt thì người lập sửa tay trong popup chi tiết dòng.
    expected_date: '',
    unit: '',
    qty_request: 0,
    qty_order: 0,
    price: 0,
    vat: Math.round((vatRate || 0) * 100),
    warehouse_code: '',
    note: '',
    // bao-CR-319: rỗng / 0 = theo đồng tiền + tỷ giá của đơn.
    currency: '',
    exchange_rate: 0,
    weight_kg: 0,
    dimension: '',
    deliveries: [],
  }
}
