import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  Check,
  ChevronDown,
  CircleCheck,
  Copy,
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
import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
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
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { HeaderActionsPopover } from '@/shared/ui/header-actions-popover'
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
import { duplicatePurchaseOrderCodes, validatePurchaseOrder } from '../utils/required-fields'
import {
  displayLineBaseAmount,
  isMissingExchangeRate,
  summarizeOrderTotals,
} from '../utils/purchase-order-import-cost'
import { summarizeShipping } from '../utils/purchase-order-shipping'
import {
  COST_STAGE_ESTIMATE,
  COST_STAGE_FINAL,
  isDeliveryStage,
  isImportOrder,
  isPurchaseOrderApproved,
  isPurchaseOrderLocked,
  PO_FIELDS_EDITABLE_AFTER_APPROVE,
  PO_MISA_AFTER_APPROVE_HINT,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/** Thao tác cần lý do — mở hộp nhập trước khi gọi API. */
type ReasonAction = Extract<PurchaseOrderAction, 'return' | 'reject' | 'unapprove' | 'cancel'>

const REASON_ACTIONS: Record<ReasonAction, { title: string; description: string }> = {
  return: {
    title: 'Trả đơn về cho người tạo',
    description: 'Đơn chuyển sang Bị trả lại để người tạo sửa và gửi duyệt lại.',
  },
  unapprove: {
    title: 'Hủy duyệt đơn',
    description:
      'Đơn về Nháp để sửa lại nội dung, sửa xong phải Gửi duyệt và Duyệt lại. Đơn đã nhận hàng hoặc đã có yêu cầu thanh toán thì không hủy duyệt được.',
  },
  reject: {
    title: 'Từ chối đơn',
    description: 'Đơn bị khóa, không sửa hay gửi lại được — phải nhân bản thành đơn mới.',
  },
  cancel: {
    title: 'Hủy đơn',
    description: 'Đơn bị khóa. Đơn có dòng đã Hoàn thành thì hệ thống không cho hủy.',
  },
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

  const { data: serverData, isLoading, isError } = usePurchaseOrder(purchaseOrderId)
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
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [progressFor, setProgressFor] = useState<{
    item: PurchaseOrderItem
    status: string
  } | null>(null)
  /** Dòng đang mở hộp chi tiết (thông tin đầy đủ + các lần giao). */
  const [lineIndex, setLineIndex] = useState<number | null>(null)
  const [paymentOpen, setPaymentOpen] = useState(false)

  //  Chọn khung bọc cho nhóm lệnh phụ của đầu trang — xem `HeaderActionsPopover`.
  //
  //  ⚠️ Khai TRÊN mọi `return` sớm (đang tải / lỗi / không thấy đơn). Hook gọi
  //  sau một nhánh thoát là thứ tự hook đổi giữa các lượt vẽ.
  const isMobile = useIsMobile()
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

  //  bao-CR-499: ô «Trưởng phòng phê duyệt» chỉ liệt kê người DUYỆT ĐƯỢC đơn này. Gọi TRƯỚC
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

  async function handleSave() {
    const message = validatePurchaseOrder(data)
    if (message) {
      toast.error(message)
      return
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
      if (!ok) return
    }
    const saved = await savePurchaseOrder.mutateAsync({
      id: isNew ? undefined : purchaseOrderId,
      payload: toPurchaseOrderPayload(data),
    })
    await flushPendingDeliveryFiles(saved)
    if (isNew) navigate(appRoutes.procurement.purchaseOrderDetail(saved.id), { replace: true })
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
    // bao-CR-319: chi phí thu mua còn nợ thì nhắc trước — Hoàn thành không chặn,
    // nhưng người dùng hay tưởng "xong đơn" là "xong tiền".
    if (action === 'complete' && (data.import_cost_summary?.remaining_total ?? 0) > 0.01) {
      const proceed = await confirmDialog({
        title: 'Chi phí thu mua còn nợ',
        message: `Đơn còn ${(data.import_cost_summary?.remaining_total ?? 0).toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ chi phí thu mua chưa thanh toán. Vẫn đánh dấu Hoàn thành? Công nợ đó vẫn theo dõi được ở phân hệ Tài chính.`,
        confirmLabel: 'Vẫn hoàn thành',
        cancelLabel: 'Để sau',
      })
      if (!proceed) return
    }
    // bao-CR-453: còn dòng chi phí chưa quyết toán thì nhắc — vẫn không chặn.
    if (
      action === 'complete' &&
      (data.cost_stage ?? COST_STAGE_ESTIMATE) < COST_STAGE_FINAL &&
      (data.import_cost_summary?.lines_not_final ?? 0) > 0
    ) {
      const proceed = await confirmDialog({
        title: 'Chi phí chưa quyết toán',
        message: `Còn ${data.import_cost_summary?.lines_not_final ?? 0} dòng chi phí chưa quyết toán. Nên chốt Quyết toán trước khi Hoàn thành. Vẫn tiếp tục?`,
        confirmLabel: 'Vẫn hoàn thành',
        cancelLabel: 'Để sau',
      })
      if (!proceed) return
    }
    const result = await runAction.mutateAsync({ action })
    if (action === 'copy' && result?.id) {
      navigate(appRoutes.procurement.purchaseOrderDetail(result.id))
    }
  }

  /**
   * Lệnh PHỤ của đầu trang — khổ rộng bày thẳng, khổ hẹp gom vào nút `⋯`.
   *
   * Dựng thành BIẾN chứ không viết thẳng hai lần: mỗi nút ở đây kéo theo state
   * hoặc mutation riêng (hộp thanh toán, `DeleteConfirmButton`), chép ra hai bản
   * là hai bộ state song song cho cùng một lệnh.
   */
  const secondaryActions = (
    <>
        {/* bao-CR-498: gom mọi bản in vào MỘT nút «In» thả xuống như bản v1 — trước đó năm nút
            in rời chiếm cả hàng tiêu đề, người dùng phải đọc từng nút để tìm bản cần in. */}
        {!isNew && can('purchase_order', 'print') && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                <Printer />
                In
                <ChevronDown className="size-4 opacity-60" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuItem asChild>
                <Link to={appRoutes.procurement.purchaseOrderPrint(data.id)} target="_blank" rel="noreferrer">
                  <Printer />
                  In Đơn đặt hàng
                </Link>
              </DropdownMenuItem>
              {/* bao-CR-322: mẫu nội bộ / gửi kế toán. Cùng trang in với mục trên, vào bằng
                  đường dẫn riêng nên mở ra là đã đúng mẫu, không phải bấm công tắc. */}
              <DropdownMenuItem asChild>
                <Link to={appRoutes.procurement.purchaseOrderGoodsPrint(data.id)} target="_blank" rel="noreferrer">
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
                    <Link to={appRoutes.procurement.purchaseOrderImportPrint(data.id)} target="_blank" rel="noreferrer">
                      <Ship />
                      In Đơn nhập khẩu
                    </Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link
                      to={`${appRoutes.procurement.importLandedCostPrint}?codes=${encodeURIComponent(data.code || '')}`}
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
                    <Link to={appRoutes.procurement.purchaseRequestPrintFromPo(data.id)} target="_blank" rel="noreferrer">
                      <FileText />
                      In Phiếu yêu cầu
                    </Link>
                  </DropdownMenuItem>
                </>
              )}
            </DropdownMenuContent>
          </DropdownMenu>
        )}

        {/*
          CỐ Ý không gác theo `unpaid_total > 0.01`: đơn chưa nhận hàng thì chưa
          có công nợ, nhưng vẫn phải lập được phiếu THANH TOÁN TRƯỚC (CR-067) —
          hộp thoại tự đổi sang luồng đó. Bản v1 cũng đã bỏ điều kiện này.
        */}
        {!isNew &&
          ['approved', 'partial', 'received', 'completed'].includes(data.status) &&
          can('payment_request', 'create') && (
            <Button variant="outline" onClick={() => setPaymentOpen(true)}>
              <Receipt />
              Tạo yêu cầu thanh toán
            </Button>
          )}


        {!isNew && data.status === 'submitted' && can('purchase_order', 'approve') && (
          <>
            <Button variant="outline" onClick={() => void handleAction('return')}>
              <CornerUpLeft />
              Trả về
            </Button>
            <Button
              variant="outline"
              className="text-destructive hover:text-destructive"
              onClick={() => void handleAction('reject')}
            >
              <Ban />
              Từ chối
            </Button>
          </>
        )}

        {canUnapprove && (
          <Button variant="outline" onClick={() => void handleAction('unapprove')}>
            <RotateCcw />
            Hủy duyệt
          </Button>
        )}

        {/* Chỉ hiện từ khi có hàng về. Đơn mới duyệt mà chưa nhận dòng nào thì
            backend chặn `/complete` (400 "Còn N dòng chưa Hoàn thành/Hủy") —
            để nút ở đó chỉ tổ mời người dùng bấm vào một lỗi. */}
        {!isNew && ['partial', 'received'].includes(data.status) && canWrite && (
          <Button variant="outline" onClick={() => void handleAction('complete')}>
            <CircleCheck />
            Hoàn thành
          </Button>
        )}

        {!isNew && data.status === 'completed' && canWrite && (
          <Button variant="outline" onClick={() => void handleAction('reopen')}>
            <LockOpen />
            Mở lại
          </Button>
        )}

        {!isNew && isDeliveryStage(data.status) && can('purchase_order', 'cancel') && (
          <Button
            variant="outline"
            className="text-destructive hover:text-destructive"
            onClick={() => void handleAction('cancel')}
          >
            <Ban />
            Hủy đơn
          </Button>
        )}

        {!isNew && can('purchase_order', 'create') && (
          <Button variant="outline" onClick={() => void handleAction('copy')}>
            <Copy />
            Nhân bản
          </Button>
        )}

        {canDelete && can('purchase_order', 'delete') && (
          <DeleteConfirmButton
            recordName={data.code || `#${data.id}`}
            pending={deletePurchaseOrder.isPending}
            warning="Đơn và các dòng hàng kèm theo sẽ bị xóa."
            onConfirm={async () => {
              await deletePurchaseOrder.mutateAsync(data.id)
              navigate(appRoutes.procurement.purchaseOrders)
            }}
          />
        )}
    </>
  )

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      {/*  ⚠️ **Cụm nút ở LẠI hàng đầu, huy hiệu mới là thứ được phép xuống
           dòng.** Bản trước để tiêu đề và huy hiệu nằm chung một hàng `flex-wrap`
           với cụm nút, nên số huy hiệu quyết định nút rơi đi đâu: đơn một huy
           hiệu thì nút ở hàng đầu, đơn vừa *Đã nhận một phần* vừa *Đơn gấp* (như
           PO00143) thì đẩy nút xuống hàng hai. Vị trí nút Lưu đổi theo DỮ LIỆU
           là thứ người dùng không đoán được — mở hai đơn liền nhau, quen tay bấm
           một chỗ thì trúng chỗ khác.

           Gom tiêu đề + huy hiệu vào MỘT ô `flex-1 min-w-0` tự xuống dòng bên
           trong; cụm nút là anh em của ô đó nên luôn ở hàng đầu. `items-start`
           để nó bám mép trên chứ không trôi xuống giữa khi huy hiệu xuống dòng. */}
      <div className="mb-4 flex flex-wrap items-start gap-3">
        <Button
          variant="outline"
          size="icon"
          asChild
          className="shrink-0"
          aria-label="Về danh sách đơn mua hàng"
        >
          <Link to={appRoutes.procurement.purchaseOrders}>
            <ArrowLeft />
          </Link>
        </Button>

        {/*  ⚠️ KHÔNG `min-w-0` ở ô tiêu đề. `min-w-0` cho nó co về 0, nên khi
             cụm nút rộng (nút chính *Tạo đơn mua hàng* ~210px) trình duyệt chọn
             CO TIÊU ĐỀ thay vì đẩy cụm nút xuống hàng — mã phiếu bị cắt cụt
             ngay giữa chữ. Để min-content của mã phiếu được tôn trọng thì lớp
             ngoài `flex-wrap` mới có cớ xuống dòng, và mã phiếu luôn đọc đủ. */}
        <div className="flex flex-1 flex-wrap items-center gap-x-3 gap-y-1.5">
          <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
            {isNew ? 'Tạo Đơn mua hàng mới' : data.code || 'Đơn nháp'}
          </h1>
          {!isNew && <StatusBadge status={data.status} labels={PO_STATUS_LABELS} />}
          {data.is_urgent && (
            <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
              Đơn gấp
            </Badge>
          )}
        </div>

        {/*  ⚠️ Nhóm phụ dựng MỘT LẦN, `useIsMobile` chỉ chọn khung BỌC — đừng
             dựng hai bản rồi ẩn một bằng CSS. Mấy nút này mang hộp xác nhận và
             mutation riêng (`DeleteConfirmButton`, hộp thanh toán): bản bị ẩn
             vẫn gắn kết, vẫn giữ state, vẫn bắn được request. Cùng luật
             `detail-page-shell` của phân hệ Văn bản.

             Chia chính/phụ ĐÚNG THEO DÁNG NÚT: nút nền đặc là việc người mở
             trang đang định làm — *Gửi duyệt* khi còn nháp, *Duyệt* khi đang
             cầm đơn chờ duyệt, *Lưu* khi sửa được. Đầu trang này có tới ~15
             lệnh; bày hết ra thì ở khổ hẹp chúng tràn BA hàng ngay dưới tiêu
             đề. */}
        <div className="ml-auto flex shrink-0 flex-wrap items-center justify-end gap-2">
          {!isNew && ['draft', 'rejected'].includes(data.status) && canWrite && (
            <Button onClick={() => void handleAction('submit')} disabled={runAction.isPending}>
              <Send />
              Gửi duyệt
            </Button>
          )}

          {!isNew && data.status === 'submitted' && can('purchase_order', 'approve') && (
            <Button onClick={() => void handleAction('approve')} disabled={runAction.isPending}>
              <Check />
              Duyệt
            </Button>
          )}

          {/* Đơn đã duyệt vẫn cần nút Lưu: mấy ô mở sau khi duyệt nằm trong popup
              chi tiết dòng, sửa xong phải ghi xuống được. */}
          {(headerEditable || afterApproveEditable) && (
            <Button onClick={() => void handleSave()} disabled={savePurchaseOrder.isPending}>
              {savePurchaseOrder.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              {isNew ? 'Tạo đơn' : 'Lưu'}
            </Button>
          )}

          {isMobile ? (
            <HeaderActionsPopover>{secondaryActions}</HeaderActionsPopover>
          ) : (
            secondaryActions
          )}
        </div>
      </div>

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
          documentStatusEditable={!isNew && can('purchase_order', 'write')}
          onDocumentStatusChange={(value) => void setDocumentStatus.mutateAsync(value)}
        />

        <Card className="gap-4 py-4">
          {/* Cùng khuôn tiêu đề với mọi thẻ khác — xem ghi chú `pb-3!` ở
              `purchase-request-attachments-card.tsx`. */}
          <CardHeader className="min-h-9 flex flex-row items-center justify-between gap-3 border-b px-4 pb-3!">
            <CardTitle className="text-base text-navy dark:text-foreground">Dòng hàng</CardTitle>
            {headerEditable && (
              <Button
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
          </CardHeader>
          <CardContent className="space-y-4 px-4">
            {afterApproveEditable && (
              <p className="rounded-md border border-info/30 bg-info/8 px-3 py-1.5 text-xs text-muted-foreground">
                Đơn đã duyệt — nội dung đã ký khóa lại. Mở nút bút chì ở cột Hành động để sửa:{' '}
                {PO_FIELDS_EDITABLE_AFTER_APPROVE}.{PO_MISA_AFTER_APPROVE_HINT}
                {canUnapprove && ' Muốn đổi phần khác thì bấm Hủy duyệt để đưa đơn về Nháp.'}
              </p>
            )}
            <PurchaseOrderItemsTable
              items={data.items}
              order={data}
              editable={headerEditable}
              progressEditable={progressEditable}
              onChange={(items) => patch({ items })}
              onOpenDetail={setLineIndex}
              onLineRemoved={(index) =>
                setPendingFiles((current) => shiftPendingAfterLineRemove(current, index))
              }
              onLineDuplicated={(index) =>
                setPendingFiles((current) => shiftPendingAfterLineInsert(current, index))
              }
              onProgressChange={(item, status) => {
                // Tạm ngưng / Hủy đơn bắt buộc nêu lý do; tiếp tục thì gọi thẳng.
                if (status === '__resume__') {
                  void setItemProgress.mutateAsync({ itemId: item.id ?? 0, status })
                  return
                }
                setProgressFor({ item, status })
              }}
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
          documentStatus={data.document_status}
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
        onSave={() => void handleSave()}
      />

      <PurchaseOrderReasonDialog
        open={reasonFor !== null}
        title={reasonFor ? REASON_ACTIONS[reasonFor].title : ''}
        description={reasonFor ? REASON_ACTIONS[reasonFor].description : ''}
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
        title={progressFor?.status === 'cancelled' ? 'Hủy dòng hàng' : 'Tạm ngưng dòng hàng'}
        description={`Sản phẩm: ${progressFor?.item.product_name || progressFor?.item.product_code || ''}`}
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
