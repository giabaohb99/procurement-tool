import { Copy, Loader2, Printer, Send } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { DeleteConfirmButton } from '@/shared/ui/delete-confirm-button'
import { PageContainer } from '@/shared/ui/page-container'
import { SealApprovalPanel } from '../components/seal-approval-panel'
import { SealDetailBody } from '../components/seal-detail-body'
import { SealDetailHeader } from '../components/seal-detail-header'
import { SealRequestForm, type SealFormHandle } from '../components/seal-request-form'
import { SealWorkflowActions } from '../components/seal-workflow-actions'
import { useDeleteSealRequest, useSealRequest } from '../hooks/use-seal-requests'
import { EDITABLE_SEAL_STATUSES } from '../types/seal-request'

/**
 * Trang CHI TIẾT phiếu đóng dấu (`/approval-seal/:id`) — xem + thao tác theo vai trò.
 *
 * Bố cục cải tiến:
 * - Header dính đỉnh màn hình (`sticky top-0`) hiển thị mã phiếu, tiêu đề, trạng thái
 *   và cụm nút thao tác nghiệp vụ.
 * - Thân trang chia 2 cột:
 *   + Cột trái: Thông tin văn bản, công ty đóng dấu, người tạo, tiến trình duyệt & chứng từ đính kèm.
 *   + Cột phải (Sticky scroll): Ghim cố định và cuộn độc lập cho Luồng duyệt nhiều bước,
 *     Trao đổi bình luận (`DocumentComments`) và Lịch sử thao tác (`AuditTimeline`).
 */
export function SealRequestDetailPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { id } = useParams()
  const requestId = Number(id)
  const { data, isLoading, isError } = useSealRequest(Number.isFinite(requestId) ? requestId : null)

  const deleteMutation = useDeleteSealRequest()

  const editable = Boolean(data) && EDITABLE_SEAL_STATUSES.has(data!.status)
  const canEdit = editable && can('seal_request', 'write')
  const canDelete = Boolean(data) && can('seal_request', 'delete')
  const canCreate = can('seal_request', 'create')

  // Nút Lưu nháp / Gửi duyệt do FORM bên dưới thực thi qua `ref`
  const formRef = useRef<SealFormHandle>(null)
  const [saving, setSaving] = useState(false)
  const onPendingChange = useCallback((p: boolean) => setSaving(p), [])

  const headerActions = data ? (
    <>
      <SealWorkflowActions request={data} />
      {canEdit && (
        <>
          <Button
            variant="outline"
            onClick={() => formRef.current?.save(false)}
            disabled={saving}
          >
            Lưu nháp
          </Button>
          <Button onClick={() => formRef.current?.save(true)} disabled={saving}>
            {saving ? <Loader2 className="size-4 animate-spin" /> : <Send className="size-4" />}
            Gửi duyệt
          </Button>
        </>
      )}
      {canCreate && (
        <Button
          variant="outline"
          onClick={() => navigate(`${appRoutes.approvalSeal.new}?from=${data.id}`)}
        >
          <Copy className="size-4" />
          Nhân bản
        </Button>
      )}
      <Button variant="outline" onClick={() => navigate(appRoutes.approvalSeal.print(data.id))}>
        <Printer className="size-4" />
        In phiếu
      </Button>
      {canDelete && (
        <DeleteConfirmButton
          recordName={data.title || data.purpose || data.code}
          pending={deleteMutation.isPending}
          onConfirm={async () => {
            await deleteMutation.mutateAsync(data.id)
            navigate(appRoutes.approvalSeal.requests)
          }}
          warning="Phiếu và chứng từ đính kèm sẽ bị gỡ."
        />
      )}
    </>
  ) : null

  return (
    <PageContainer className="w-full">
      {data && (
        <SealDetailHeader
          request={data}
          onBack={() => navigate(appRoutes.approvalSeal.requests)}
          actions={headerActions}
        />
      )}

      {isLoading && (
        <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
          Đang tải yêu cầu đóng dấu…
        </div>
      )}

      {isError && (
        <div className="rounded-lg border border-destructive/20 bg-destructive/10 p-4 text-sm text-destructive">
          Không tải được yêu cầu. Kiểm tra kết nối mạng hoặc quyền truy cập.
        </div>
      )}

      {data && (
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
          {/* Cột trái: Nội dung chi tiết phiếu hoặc Form chỉnh sửa */}
          <div className="flex min-w-0 flex-col gap-6">
            {canEdit ? (
              <SealRequestForm
                ref={formRef}
                request={data}
                title=""
                embedded
                hideActions
                onPendingChange={onPendingChange}
                onSaved={() => {}}
                onCancel={() => navigate(appRoutes.approvalSeal.requests)}
              />
            ) : (
              <>
                <SealDetailBody request={data} />
                <DocumentAttachmentsCard
                  entity="seal_request"
                  entityId={data.id}
                  canManage={false}
                  maxSizeMb={50}
                  defaultDocType="signed_doc"
                />
              </>
            )}
          </div>

          {/* Cột phải: Sticky scroll theo header */}
          <div className="flex flex-col gap-5 lg:sticky lg:top-[calc(var(--seal-header-h,0px)+0.75rem)] lg:max-h-[calc(100dvh-3.5rem-var(--seal-header-h,0px)-2rem)] lg:self-start lg:overflow-y-auto pr-0.5">
            {/*  Gác bằng `approval_instance_id` (phiên gần nhất, kể cả đã xong) chứ
                 KHÔNG bằng `approval_running`: thẻ này chứa cả Lịch sử phê duyệt,
                 gác bằng cờ "đang chạy" thì duyệt xong là dấu vết biến mất. */}
            {data.approval_instance_id != null && <SealApprovalPanel requestId={data.id} />}
            <DocumentComments entity="seal_request" entityId={data.id} />
            <AuditTimeline entity="seal_request" entityId={data.id} showMessage dense />
          </div>
        </div>
      )}
    </PageContainer>
  )
}
