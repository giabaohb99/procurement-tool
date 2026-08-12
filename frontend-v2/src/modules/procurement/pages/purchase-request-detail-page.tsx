import { ArrowLeft, Check, Copy, Loader2, Pencil, Save, Send, X } from 'lucide-react'
import { useEffect, useState } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'

import { PermissionGate } from '@/core/authorization/permission-gate'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Skeleton } from '@/shared/ui/skeleton'
import { Textarea } from '@/shared/ui/textarea'
import { formatMoney } from '@/shared/utils/format-money'
import { StatusBadge } from '../components/document-status-badge'
import { PurchaseRequestInfoCard } from '../components/purchase-request-info-card'
import { PurchaseRequestItemsTable } from '../components/purchase-request-items-table'
import {
  useOrderProgress,
  usePurchaseRequest,
  usePurchaseRequestAction,
  useSavePurchaseRequest,
  type PurchaseRequestAction,
} from '../hooks/use-purchase-request'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import {
  isEditable,
  type PurchaseRequestDetail,
} from '../types/purchase-request-detail'

/** Ba thao tác dưới đây bắt buộc nêu lý do (backend cũng chặn nếu bỏ trống). */
const REASON_ACTIONS: Record<string, string> = {
  reject: 'Trả lại phiếu cho người yêu cầu sửa',
  cancel: 'Từ chối phiếu',
  return: 'Trả phiếu đã duyệt về để sửa',
}

/**
 * Chi tiết phiếu Yêu cầu mua hàng: xem, sửa (khi còn nháp / bị trả lại) và các
 * thao tác chuyển trạng thái.
 *
 * Quyền được lấy theo HAI nguồn: `can()` cho hành động chung, và cờ
 * `can_approve` / `can_dispatch` do backend tính riêng cho từng phiếu (ai là
 * người duyệt của phòng đó) — không tự suy ở frontend.
 */
export function PurchaseRequestDetailPage() {
  const { id } = useParams()
  const navigate = useNavigate()
  const purchaseRequestId = Number(id)

  const { data, isLoading, isError } = usePurchaseRequest(purchaseRequestId)
  const { data: progress } = useOrderProgress(purchaseRequestId)
  const savePurchaseRequest = useSavePurchaseRequest()
  const runAction = usePurchaseRequestAction(purchaseRequestId)

  const [editing, setEditing] = useState(false)
  const [draft, setDraft] = useState<PurchaseRequestDetail | null>(null)
  const [reasonFor, setReasonFor] = useState<PurchaseRequestAction | null>(null)
  const [reason, setReason] = useState('')

  // Rời chế độ sửa mỗi khi nạp lại phiếu (lưu xong, đổi trạng thái…).
  useEffect(() => {
    setDraft(data ?? null)
    setEditing(false)
  }, [data])

  if (isLoading) {
    return (
      <PageContainer>
        <Skeleton className="mb-4 h-20 w-full" />
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }

  if (isError || !data || !draft) {
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

  const canEdit = isEditable(data.status)

  function patch(changes: Partial<PurchaseRequestDetail>) {
    setDraft((current) => (current ? { ...current, ...changes } : current))
  }

  async function handleSave() {
    if (!draft) return
    await savePurchaseRequest.mutateAsync({
      id: purchaseRequestId,
      payload: {
        company_id: draft.company_id,
        requester: draft.requester,
        requester_id: draft.requester_id,
        requester_position: draft.requester_position,
        department: draft.department,
        head_of_dept: draft.head_of_dept,
        purpose: draft.purpose,
        request_date: draft.request_date,
        need_date: draft.need_date,
        is_urgent: draft.is_urgent,
        vat_rate: draft.vat_rate,
        note: draft.note,
        show_code_on_print: draft.show_code_on_print,
        supplier_req: draft.supplier_req,
        items: draft.items,
      },
    })
  }

  async function handleAction(action: PurchaseRequestAction) {
    if (REASON_ACTIONS[action]) {
      setReasonFor(action)
      setReason('')
      return
    }
    const result = await runAction.mutateAsync({ action })
    // Nhân bản trả về phiếu nháp MỚI -> nhảy sang phiếu đó luôn.
    if (action === 'copy' && result?.id) {
      navigate(appRoutes.procurement.purchaseRequestDetail(result.id))
    }
  }

  return (
    <PageContainer>
      <div className="mb-4 flex flex-wrap items-center gap-3">
        <Button variant="ghost" size="sm" asChild>
          <Link to={appRoutes.procurement.purchaseRequests}>
            <ArrowLeft />
            Yêu cầu mua hàng
          </Link>
        </Button>
      </div>

      <PageHeader
        title={data.code || 'Phiếu nháp'}
        description={`${data.department || '—'} · ${data.requester || '—'}`}
        actions={
          <div className="flex flex-wrap items-center gap-2">
            {editing ? (
              <>
                <Button onClick={handleSave} disabled={savePurchaseRequest.isPending}>
                  {savePurchaseRequest.isPending ? (
                    <Loader2 className="animate-spin" />
                  ) : (
                    <Save />
                  )}
                  Lưu
                </Button>
                <Button
                  variant="outline"
                  onClick={() => {
                    setDraft(data)
                    setEditing(false)
                  }}
                >
                  <X />
                  Hủy sửa
                </Button>
              </>
            ) : (
              <>
                {canEdit && (
                  <PermissionGate entity="purchase_request" action="write">
                    <Button variant="outline" onClick={() => setEditing(true)}>
                      <Pencil />
                      Sửa
                    </Button>
                  </PermissionGate>
                )}

                {canEdit && (
                  <PermissionGate entity="purchase_request" action="write">
                    <Button onClick={() => handleAction('submit')} disabled={runAction.isPending}>
                      <Send />
                      Gửi duyệt
                    </Button>
                  </PermissionGate>
                )}

                {/* `can_approve` do backend tính theo phiếu — chỉ trưởng bộ phận
                    của đúng phòng đó mới thấy nút này. */}
                {data.status === 'submitted' && data.can_approve && (
                  <>
                    <Button onClick={() => handleAction('approve')} disabled={runAction.isPending}>
                      <Check />
                      Duyệt
                    </Button>
                    <Button
                      variant="outline"
                      className="text-destructive hover:text-destructive"
                      onClick={() => handleAction('reject')}
                    >
                      <X />
                      Trả lại
                    </Button>
                  </>
                )}

                {data.status === 'approved' && data.can_dispatch && (
                  <Button onClick={() => handleAction('dispatch')} disabled={runAction.isPending}>
                    <Check />
                    Điều phối
                  </Button>
                )}

                <PermissionGate entity="purchase_request" action="create">
                  <Button variant="outline" onClick={() => handleAction('copy')}>
                    <Copy />
                    Nhân bản
                  </Button>
                </PermissionGate>
              </>
            )}
          </div>
        }
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <StatusBadge status={data.status} labels={PR_STATUS_LABELS} />
        {data.is_urgent && (
          <Badge variant="secondary" className="border-0 bg-warning/10 text-warning">
            Đơn gấp
          </Badge>
        )}
        <span className="text-sm text-muted-foreground">
          Tổng cộng: <b className="text-foreground">{formatMoney(data.total)} đ</b>
        </span>
      </div>

      <div className="space-y-4">
        <PurchaseRequestInfoCard data={draft} editing={editing} onChange={patch} />

        <Card>
          <CardHeader>
            <CardTitle className="text-base text-navy dark:text-foreground">
              Danh sách sản phẩm yêu cầu
            </CardTitle>
          </CardHeader>
          <CardContent>
            <PurchaseRequestItemsTable
              items={draft.items}
              editing={editing}
              onChange={(items) => patch({ items })}
              orderedByCode={progress?.ordered}
            />
          </CardContent>
        </Card>

        {reasonFor && (
          <Card>
            <CardHeader>
              <CardTitle className="text-base text-destructive">
                {REASON_ACTIONS[reasonFor]}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                rows={3}
                placeholder="Nêu rõ lý do — nội dung này vào nhật ký thao tác."
                value={reason}
                onChange={(e) => setReason(e.target.value)}
              />
              <div className="flex gap-2">
                <Button
                  variant="destructive"
                  disabled={!reason.trim() || runAction.isPending}
                  onClick={async () => {
                    await runAction.mutateAsync({ action: reasonFor, reason: reason.trim() })
                    setReasonFor(null)
                  }}
                >
                  Xác nhận
                </Button>
                <Button variant="outline" onClick={() => setReasonFor(null)}>
                  Hủy
                </Button>
              </div>
            </CardContent>
          </Card>
        )}

        <Card>
          <CardHeader>
            <CardTitle className="text-base text-navy dark:text-foreground">
              Lịch sử thao tác
            </CardTitle>
          </CardHeader>
          <CardContent>
            <AuditTimeline entity="purchase_request" entityId={purchaseRequestId} />
          </CardContent>
        </Card>
      </div>
    </PageContainer>
  )
}
