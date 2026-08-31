import {
  AlertTriangle,
  ArrowLeft,
  Ban,
  Check,
  CircleCheck,
  Copy,
  CornerUpLeft,
  Loader2,
  LockOpen,
  Plus,
  Printer,
  Receipt,
  RotateCcw,
  Save,
  Send,
} from 'lucide-react'
import { useMemo, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { useSuppliers } from '@/modules/production/hooks/use-suppliers'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { Skeleton } from '@/shared/ui/skeleton'
import { DocumentAttachmentsCard } from '../components/document-attachments-card'
import { DocumentComments } from '../components/document-comments'
import { DocumentMoneyTotals } from '../components/document-money-totals'
import { StatusBadge } from '../components/document-status-badge'
import { PurchaseOrderInfoCard } from '../components/purchase-order-info-card'
import {
  orderLineAmount,
  PurchaseOrderItemsTable,
} from '../components/purchase-order-items-table'
import { PurchaseOrderLineDialog } from '../components/purchase-order-line-dialog'
import { PurchaseOrderPaymentDialog } from '../components/purchase-order-payment-dialog'
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
import { validatePurchaseOrder } from '../utils/required-fields'
import { summarizeShipping } from '../utils/purchase-order-shipping'
import {
  isDeliveryStage,
  isPurchaseOrderApproved,
  isPurchaseOrderLocked,
  PO_FIELDS_EDITABLE_AFTER_APPROVE,
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

  /** Tiền theo SL ĐẶT — tính tại chỗ để người dùng thấy ngay khi gõ. */
  const orderTotals = useMemo(() => {
    const items = draft?.items ?? []
    const subtotal = items.reduce((sum, item) => sum + item.qty_order * item.price, 0)
    const total = items.reduce((sum, item) => sum + orderLineAmount(item), 0)
    return { subtotal, vat: total - subtotal, total }
  }, [draft?.items])

  /** Cước vận chuyển gom từ các lần giao — để giải thích con số ở dưới bảng. */
  const shipping = useMemo(() => summarizeShipping(draft?.items ?? []), [draft?.items])

  /** Giỏ phiếu giao của riêng dòng đang mở, đổi về khóa theo chỉ số lần giao. */
  const linePendingFiles = useMemo(
    () => (lineIndex === null ? {} : pendingFilesOfLine(pendingFiles, lineIndex)),
    [pendingFiles, lineIndex],
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
    const result = await runAction.mutateAsync({ action })
    if (action === 'copy' && result?.id) {
      navigate(appRoutes.procurement.purchaseOrderDetail(result.id))
    }
  }

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách đơn mua hàng">
          <Link to={appRoutes.procurement.purchaseOrders}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {isNew ? 'Tạo Đơn mua hàng mới' : data.code || 'Đơn nháp'}
        </h1>
        {!isNew && <StatusBadge status={data.status} labels={PO_STATUS_LABELS} />}
        {data.is_urgent && (
          <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
            Đơn gấp
          </Badge>
        )}

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {!isNew && can('purchase_order', 'print') && (
            <Button variant="outline" asChild>
              <Link
                to={appRoutes.procurement.purchaseOrderPrint(data.id)}
                target="_blank"
                rel="noreferrer"
              >
                <Printer />
                In đơn
              </Link>
            </Button>
          )}

          {!isNew &&
            ['approved', 'partial', 'received', 'completed'].includes(data.status) &&
            can('payment_request', 'create') &&
            data.unpaid_total > 0.01 && (
              <Button variant="outline" onClick={() => setPaymentOpen(true)}>
                <Receipt />
                Tạo yêu cầu thanh toán
              </Button>
            )}

          {!isNew && ['draft', 'rejected'].includes(data.status) && canWrite && (
            <Button onClick={() => void handleAction('submit')} disabled={runAction.isPending}>
              <Send />
              Gửi duyệt
            </Button>
          )}

          {!isNew && data.status === 'submitted' && can('purchase_order', 'approve') && (
            <>
              <Button onClick={() => void handleAction('approve')} disabled={runAction.isPending}>
                <Check />
                Duyệt
              </Button>
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

          {/* Đơn đã duyệt vẫn cần nút Lưu: mấy ô mở sau khi duyệt nằm trong popup
              chi tiết dòng, sửa xong phải ghi xuống được. */}
          {(headerEditable || afterApproveEditable) && (
            <Button onClick={() => void handleSave()} disabled={savePurchaseOrder.isPending}>
              {savePurchaseOrder.isPending ? <Loader2 className="animate-spin" /> : <Save />}
              {isNew ? 'Tạo đơn' : 'Lưu'}
            </Button>
          )}
        </div>
      </div>

      <div className="min-w-0 space-y-4">
        <PurchaseOrderInfoCard
          data={data}
          editable={headerEditable}
          companies={companiesData?.items}
          suppliers={(suppliersData?.items ?? []).filter(
            (supplier) => supplier.supplier_type !== 'transport',
          )}
          employees={employeesData?.items}
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
                {PO_FIELDS_EDITABLE_AFTER_APPROVE}.
                {canUnapprove && ' Muốn đổi phần khác thì bấm Hủy duyệt để đưa đơn về Nháp.'}
              </p>
            )}
            <PurchaseOrderItemsTable
              items={data.items}
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
              {...orderTotals}
              subtotalLabel="Tiền hàng theo SL đặt (chưa VAT)"
              totalLabel="Tổng đơn đặt (gồm VAT)"
            />
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
              </div>
            )}
          </CardContent>
        </Card>

        <DocumentAttachmentsCard
          entity="purchase_order"
          entityId={purchaseOrderId}
          canManage={!locked && can('purchase_order', 'write')}
          documentStatus={data.document_status}
        />

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

      <PurchaseOrderPaymentDialog
        open={paymentOpen}
        purchaseOrderCode={data.code}
        onOpenChange={setPaymentOpen}
      />

      <PurchaseOrderLineDialog
        item={lineIndex === null ? null : (data.items[lineIndex] ?? null)}
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
    deliveries: [],
  }
}
