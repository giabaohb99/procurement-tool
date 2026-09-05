import { ArrowLeft, Pencil, Send } from 'lucide-react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { PageContainer } from '@/shared/ui/page-container'
import { SealDetailBody } from '../components/seal-detail-body'
import { SealStatusBadge } from '../components/status-pill'
import { SealWorkflowActions } from '../components/seal-workflow-actions'
import {
  useDeleteSealRequest,
  useSealRequest,
  useSubmitSealRequest,
} from '../hooks/use-seal-requests'
import { EDITABLE_SEAL_STATUSES } from '../types/seal-request'

/**
 * Trang CHI TIẾT phiếu đóng dấu (`/approval-seal/:id`) — xem + thao tác theo vai
 * trò. Sửa mở TRANG riêng `/:id/edit`.
 */
export function SealRequestDetailPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { id } = useParams()
  const requestId = Number(id)
  const { data, isLoading, isError } = useSealRequest(Number.isFinite(requestId) ? requestId : null)

  const submitMutation = useSubmitSealRequest()
  const deleteMutation = useDeleteSealRequest()

  const editable = Boolean(data) && EDITABLE_SEAL_STATUSES.has(data!.status)
  const canEdit = editable && can('seal_request', 'write')
  const canDelete = Boolean(data) && can('seal_request', 'delete')

  return (
    <PageContainer className="w-full">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          aria-label="Về danh sách yêu cầu đóng dấu"
          onClick={() => navigate(appRoutes.approvalSeal.root)}
        >
          <ArrowLeft className="size-4" />
        </Button>
        <div className="min-w-0">
          <h1 className="truncate text-xl font-semibold tracking-tight text-navy dark:text-foreground">
            {data ? data.purpose || `Yêu cầu đóng dấu ${data.code}` : 'Chi tiết yêu cầu đóng dấu'}
          </h1>
          {data && <p className="text-sm text-muted-foreground">Yêu cầu đóng dấu {data.code}</p>}
        </div>
        {data && <SealStatusBadge status={data.status} label={data.status_label} />}
        <div className="min-w-4 flex-1" />
        <div className="flex flex-wrap items-center justify-end gap-2">
          {data && <SealWorkflowActions request={data} />}
          {canEdit && data && (
            <Button
              onClick={() => submitMutation.mutate({ id: data.id })}
              disabled={submitMutation.isPending}
            >
              <Send className="size-4" />
              Gửi duyệt
            </Button>
          )}
          {canEdit && data && (
            <Button variant="outline" onClick={() => navigate(appRoutes.approvalSeal.edit(data.id))}>
              <Pencil className="size-4" />
              Sửa
            </Button>
          )}
          {canDelete && data && (
            <DeleteConfirmButton
              recordName={data.purpose || data.code}
              pending={deleteMutation.isPending}
              onConfirm={async () => {
                await deleteMutation.mutateAsync(data.id)
                navigate(appRoutes.approvalSeal.root)
              }}
              warning="Phiếu và chứng từ đính kèm sẽ bị gỡ."
            />
          )}
        </div>
      </div>

      {isLoading && <p className="text-sm text-muted-foreground">Đang tải…</p>}
      {isError && (
        <p className="text-sm text-destructive">
          Không tải được yêu cầu. Kiểm tra kết nối hoặc quyền truy cập.
        </p>
      )}

      {data && (
        <div className="grid gap-5 xl:grid-cols-[minmax(0,1fr)_380px]">
          <div className="flex min-w-0 flex-col gap-5">
            <SealDetailBody request={data} />
            <DocumentAttachmentsCard
              entity="seal_request"
              entityId={data.id}
              canManage={canEdit}
              maxSizeMb={50}
            />
          </div>
          <div className="flex flex-col gap-5">
            <Card className="flex flex-col gap-3 p-5">
              <h3 className="border-b pb-1 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
                Lịch sử thao tác
              </h3>
              <AuditTimeline entity="seal_request" entityId={data.id} />
            </Card>
          </div>
        </div>
      )}
    </PageContainer>
  )
}
