import {
  ArrowLeft,
  Ban,
  Check,
  CheckCheck,
  Copy,
  CornerUpLeft,
  Loader2,
  Pencil,
  Printer,
  Save,
  Send,
  X,
} from 'lucide-react'
import { useEffect, useMemo, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { toast } from 'sonner'

import { useAuth } from '@/core/auth/use-auth'
import type { AuthUser } from '@/core/auth/auth-types'
import { PermissionGate } from '@/core/authorization/permission-gate'
import { usePermission } from '@/core/authorization/use-permission'
import { useCompanies } from '@/modules/hr/hooks/use-companies'
import { useEmployees } from '@/modules/hr/hooks/use-employees'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
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
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
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
import { StatusBadge } from '../components/document-status-badge'
import { PurchaseRequestAttachmentsCard } from '../components/purchase-request-attachments-card'
import { PurchaseRequestComments } from '../components/purchase-request-comments'
import { PurchaseRequestInfoCard } from '../components/purchase-request-info-card'
import { PurchaseRequestItemsTable } from '../components/purchase-request-items-table'
import { PurchaseRequestLineDetailDialog } from '../components/purchase-request-line-detail-dialog'
import { PurchaseRequestSupplierCard } from '../components/purchase-request-supplier-card'
import { PurchaseRequestTotals } from '../components/purchase-request-totals'
import { RelatedPurchaseOrdersCard } from '../components/related-purchase-orders-card'
import {
  useAssignPurchaser,
  useDeletePurchaseRequest,
  useOrderProgress,
  usePurchaseRequest,
  usePurchaseRequestAction,
  useSavePurchaseRequest,
  useSetUrgent,
  useUpdateItemStatus,
  type PurchaseRequestAction,
} from '../hooks/use-purchase-request'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import { purchaseRequestApi } from '../api/purchase-request-api'
import {
  isClosed,
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
  const isNew = id === 'new'
  const purchaseRequestId = isNew ? 0 : Number(id)
  const { user } = useAuth()
  const { can } = usePermission()

  const { data: serverData, isLoading, isError } = usePurchaseRequest(purchaseRequestId)
  const { data: progress } = useOrderProgress(purchaseRequestId)
  const { data: companiesData } = useCompanies({ page_size: 500, is_active: true })
  const { data: employeesData } = useEmployees({ page_size: 1000, is_active: true })
  const savePurchaseRequest = useSavePurchaseRequest()
  const runAction = usePurchaseRequestAction(purchaseRequestId)
  const deletePurchaseRequest = useDeletePurchaseRequest()
  const assignPurchaser = useAssignPurchaser(purchaseRequestId)
  const updateItemStatus = useUpdateItemStatus(purchaseRequestId)
  const setUrgent = useSetUrgent(purchaseRequestId)

  const [editing, setEditing] = useState(isNew)
  const [draft, setDraft] = useState<PurchaseRequestDetail | null>(() =>
    isNew ? createEmptyPurchaseRequest(user) : null,
  )
  const [reasonFor, setReasonFor] = useState<ReasonAction | null>(null)
  const [reason, setReason] = useState('')
  const [confirmAction, setConfirmAction] = useState<ConfirmAction | null>(null)
  const [lineIndex, setLineIndex] = useState<number | null>(null)

  useEffect(() => {
    if (isNew) {
      setDraft((current) => current ?? createEmptyPurchaseRequest(user))
      setEditing(true)
      return
    }
    setDraft(serverData ?? null)
    setEditing(false)
  }, [isNew, serverData, user])

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

  if ((!isNew && (isError || !serverData)) || !draft) {
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
  const data = serverData ?? draft
  const loadedData = data
  const loadedDraft = draft

  const editable = isEditable(data.status)
  const closed = isClosed(data.status)
  const canManage = can('purchase_request', 'cancel')
  const canAssign = can('purchase_request', 'approve') && !closed
  const showAssignee = can('survey_request', 'process')
  const workableStatuses = data.dispatch_enabled === false
    ? ['approved', 'dispatched', 'processing']
    : ['dispatched', 'processing']
  const allItemsDone =
    data.items.length > 0 &&
    data.items.every((item) => ['Hoàn thành', 'Hủy đơn'].includes(item.line_status))
  const canManageAttachments =
    editable && (can('purchase_request', 'write') || can('purchase_request', 'create'))
  const canManageLineAttachments =
    can('purchase_request', 'write') || can('purchase_request', 'create')
  const selectedLine = lineIndex === null ? null : draft.items[lineIndex] ?? null
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
    const validationMessage = validatePurchaseRequest(loadedDraft)
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
        } finally {
          // Phiếu đã được tạo thành công: luôn sang bản ghi thật để tránh người
          // dùng bấm lại và vô tình tạo trùng nếu bước gửi duyệt bị lỗi.
          navigate(appRoutes.procurement.purchaseRequestDetail(saved.id), { replace: true })
        }
        return
      }
      navigate(appRoutes.procurement.purchaseRequestDetail(saved.id), { replace: true })
    }
  }

  async function handleAction(action: PurchaseRequestAction) {
    if (action === 'return' || action === 'cancel') {
      setReasonFor(action)
      setReason('')
      return
    }
    const result = await runAction.mutateAsync({ action })
    if (action === 'copy' && result?.id) {
      navigate(appRoutes.procurement.purchaseRequestDetail(result.id))
    }
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

  return (
    <PageContainer className="bg-slate-50/70 lg:p-4">
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="outline" size="icon" asChild aria-label="Về danh sách yêu cầu mua hàng">
          <Link to={appRoutes.procurement.purchaseRequests}>
            <ArrowLeft />
          </Link>
        </Button>
        <h1 className="text-xl font-semibold tracking-tight text-navy dark:text-foreground">
          {isNew ? 'Tạo Yêu cầu mua hàng mới' : data.code || 'Phiếu nháp'}
        </h1>
        {!isNew && <StatusBadge status={data.status} labels={PR_STATUS_LABELS} />}
        {draft.is_urgent && (
          <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
            Đơn gấp
          </Badge>
        )}

        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
            {editing ? (
              <>
                <Button onClick={() => void handleSave()} disabled={savePurchaseRequest.isPending}>
                  {savePurchaseRequest.isPending ? <Loader2 className="animate-spin" /> : <Save />}
                  Lưu
                </Button>
                {isNew && (
                  <Button
                    variant="secondary"
                    onClick={() => void handleSave(true)}
                    disabled={savePurchaseRequest.isPending}
                  >
                    <Send />
                    Lưu &amp; gửi duyệt
                  </Button>
                )}
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
                <Button variant="outline" asChild>
                  <Link
                    to={appRoutes.procurement.purchaseRequestPrint(data.id)}
                    target="_blank"
                    rel="noreferrer"
                  >
                    <Printer />
                    In phiếu
                  </Link>
                </Button>
                {!isNew && <RelatedPurchaseOrdersCard purchaseRequestCode={data.code} />}
                {editable && (
                  <Button variant="outline" onClick={() => setEditing(true)}>
                    <Pencil />
                    Sửa
                  </Button>
                )}
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
                {(data.can_approve || canManage) &&
                  !['draft', 'rejected', 'cancelled', 'completed', 'done'].includes(data.status) && (
                  <Button variant="outline" onClick={() => void handleAction('return')}>
                    <CornerUpLeft />
                    Trả về
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
                {data.status === 'approved' && data.can_dispatch && (
                  <Button onClick={() => setConfirmAction('dispatch')} disabled={runAction.isPending}>
                    <Check />
                    Duyệt điều phối
                  </Button>
                )}
                {canManage && workableStatuses.includes(data.status) && (
                  <Button
                    variant="outline"
                    disabled={!allItemsDone}
                    title={allItemsDone ? undefined : 'Mọi dòng phải Hoàn thành hoặc Hủy đơn'}
                    onClick={() => setConfirmAction('complete')}
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
            )}
        </div>
      </div>

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
            data={draft}
            editing={editing}
            companies={companiesData?.items}
            employees={employeesData?.items}
            urgentEditable={!closed && !editing && can('purchase_request', 'write')}
            onUrgentChange={(value) => void setUrgent.mutateAsync(value)}
            onChange={patch}
          />

          <Card className="gap-4 py-4">
            <CardHeader className="flex flex-row items-center justify-between border-b px-4 pb-3">
              <CardTitle className="text-base text-navy dark:text-foreground">
                Danh sách Sản phẩm Yêu cầu
              </CardTitle>
              {!editing && (
                <p className="text-right text-xs text-muted-foreground">
                  Trạng thái và tiến độ tự đồng bộ từ ĐMH. Mở Chi tiết để xem ngày cần hàng, ghi chú và ảnh đối chiếu.
                </p>
              )}
            </CardHeader>
            <CardContent className="space-y-4 px-4">
              <PurchaseRequestItemsTable
                items={draft.items}
                editing={editing}
                showAssignee={showAssignee}
                onChange={(items) => patch({ items })}
                onOpenDetail={setLineIndex}
                orderedByCode={progress?.ordered}
              />
              <PurchaseRequestTotals {...calculatedTotals} />
            </CardContent>
          </Card>

          <PurchaseRequestSupplierCard data={draft} editing={editing} onChange={patch} />

          {!isNew && (
            <>
              <PurchaseRequestAttachmentsCard
                purchaseRequestId={purchaseRequestId}
                canManage={canManageAttachments}
              />
              <PurchaseRequestComments purchaseRequestId={purchaseRequestId} />
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
    </PageContainer>
  )
}

function validatePurchaseRequest(data: PurchaseRequestDetail): string {
  if (!data.company_id) return 'Vui lòng chọn Công ty'
  if (!data.requester) return 'Vui lòng chọn Nhân sự yêu cầu'
  const validItems = data.items.filter((item) => item.product_name.trim())
  if (!validItems.length) return 'Cần ít nhất một sản phẩm'
  return ''
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
    purpose: '',
    request_date: new Date().toISOString().slice(0, 10),
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
    items: [],
    subtotal: 0,
    vat: 0,
    total: 0,
  }
}
