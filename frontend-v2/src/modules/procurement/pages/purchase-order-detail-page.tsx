import {
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
import { usePurchaseRequests } from '../hooks/use-purchase-documents'
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
  validatePurchaseOrder,
  type PurchaseOrderDraftFromRequest,
} from '../utils/purchase-order-draft'
import {
  isDeliveryStage,
  isPurchaseOrderLocked,
  type PurchaseOrderDetail,
  type PurchaseOrderItem,
} from '../types/purchase-order-detail'

/** Thao tác cần lý do — mở hộp nhập trước khi gọi API. */
type ReasonAction = Extract<PurchaseOrderAction, 'return' | 'reject' | 'cancel'>

const REASON_ACTIONS: Record<ReasonAction, { title: string; description: string }> = {
  return: {
    title: 'Trả đơn về cho người tạo',
    description: 'Đơn chuyển sang Bị trả lại để người tạo sửa và gửi duyệt lại.',
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

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-20 w-full" />
        <Skeleton className="h-[540px] w-full" />
      </PageContainer>
    )
  }

  if ((!isNew && (isError || !serverData)) || !draft) {
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

  const data = draft
  const locked = isPurchaseOrderLocked(data.status)
  const canWrite = can('purchase_order', isNew ? 'create' : 'write')
  const headerEditable = (isNew || !locked) && canWrite
  const progressEditable = !isNew && isDeliveryStage(data.status) && can('purchase_order', 'write')
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
    if (isNew) navigate(appRoutes.procurement.purchaseOrderDetail(saved.id), { replace: true })
  }

  async function handleAction(action: PurchaseOrderAction) {
    if (action === 'return' || action === 'reject' || action === 'cancel') {
      setReasonFor(action)
      return
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

          {!isNew && ['partial', 'received', 'approved'].includes(data.status) && canWrite && (
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

          {headerEditable && (
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
            <PurchaseOrderItemsTable
              items={data.items}
              editable={headerEditable}
              progressEditable={progressEditable}
              onChange={(items) => patch({ items })}
              onOpenDetail={setLineIndex}
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
              <p className="text-right text-xs text-muted-foreground">
                Đã nhận: {data.total.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ ·
                Cước vận chuyển:{' '}
                {data.shipping_total.toLocaleString('vi-VN', { maximumFractionDigits: 0 })} đ
              </p>
            )}
          </CardContent>
        </Card>

        <DocumentAttachmentsCard
          entity="purchase_order"
          entityId={purchaseOrderId}
          canManage={!locked && can('purchase_order', 'write')}
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
        onChange={(item) => {
          if (lineIndex === null) return
          patch({
            items: data.items.map((current, index) => (index === lineIndex ? item : current)),
          })
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
        destructive={reasonFor !== 'return'}
        onClose={() => setReasonFor(null)}
        onConfirm={async (reason) => {
          if (!reasonFor) return
          await runAction.mutateAsync({ action: reasonFor, reason })
          setReasonFor(null)
        }}
      />

      <PurchaseOrderReasonDialog
        open={progressFor !== null}
        title={progressFor?.status === 'Hủy đơn' ? 'Hủy dòng hàng' : 'Tạm ngưng dòng hàng'}
        description={`Sản phẩm: ${progressFor?.item.product_name || progressFor?.item.product_code || ''}`}
        pending={setItemProgress.isPending}
        destructive={progressFor?.status === 'Hủy đơn'}
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
