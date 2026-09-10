import { ArrowLeft, Copy, Loader2, Printer, Send } from 'lucide-react'
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
import { SealRequestForm, type SealFormHandle } from '../components/seal-request-form'
import { SealStatusBadge } from '../components/status-pill'
import { SealWorkflowActions } from '../components/seal-workflow-actions'
import { useDeleteSealRequest, useSealRequest } from '../hooks/use-seal-requests'
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

  const deleteMutation = useDeleteSealRequest()

  const editable = Boolean(data) && EDITABLE_SEAL_STATUSES.has(data!.status)
  const canEdit = editable && can('seal_request', 'write')
  const canDelete = Boolean(data) && can('seal_request', 'delete')
  const canCreate = can('seal_request', 'create')

  //  Nút Lưu nháp / Gửi duyệt nằm ở thanh công cụ trên (cạnh In phiếu) nhưng do FORM
  //  bên dưới thực thi — điều khiển qua `ref`; `saving` để khóa nút khi đang lưu.
  const formRef = useRef<SealFormHandle>(null)
  const [saving, setSaving] = useState(false)
  const onPendingChange = useCallback((p: boolean) => setSaving(p), [])

  return (
    <PageContainer className="w-full">
      <div className="mb-3 flex flex-wrap items-center gap-3">
        <Button
          variant="outline"
          size="icon"
          aria-label="Về danh sách yêu cầu đóng dấu"
          onClick={() => navigate(appRoutes.approvalSeal.requests)}
        >
          <ArrowLeft className="size-4" />
        </Button>
        {/*  Tiêu đề + badge gom vào một nhóm co giãn (`flex-1 min-w-0`): tiêu đề DÀI bị
            `truncate` cắt "…" trong khoảng cho phép, KHÔNG đẩy cụm nút (Duyệt…) tràn khỏi
            màn hình. `min-w-0` trên cả nhóm LẪN h1 để chữ co được dưới bề rộng nội dung. */}
        <div className="flex min-w-0 flex-1 items-center gap-3">
          <h1
            className="min-w-0 truncate text-xl font-semibold tracking-tight text-navy dark:text-foreground"
            title={data ? data.purpose || `Yêu cầu đóng dấu ${data.code}` : undefined}
          >
            {data ? data.purpose || `Yêu cầu đóng dấu ${data.code}` : 'Chi tiết yêu cầu đóng dấu'}
          </h1>
          {data && <SealStatusBadge status={data.status} label={data.status_label} />}
        </div>
        <div className="flex flex-wrap items-center justify-end gap-2">
          {data && <SealWorkflowActions request={data} />}
          {/*  Phiếu sửa được: Lưu nháp / Gửi duyệt nằm CHUNG hàng với In phiếu, BÊN TRÁI
              Nhân bản; nút do FORM bên dưới thực thi qua `formRef`. */}
          {canEdit && data && (
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
          {canCreate && data && (
            <Button
              variant="outline"
              onClick={() => navigate(`${appRoutes.approvalSeal.new}?from=${data.id}`)}
            >
              <Copy className="size-4" />
              Nhân bản
            </Button>
          )}
          {data && (
            <Button variant="outline" onClick={() => navigate(appRoutes.approvalSeal.print(data.id))}>
              <Printer className="size-4" />
              In phiếu
            </Button>
          )}
          {canDelete && data && (
            <DeleteConfirmButton
              recordName={data.purpose || data.code}
              pending={deleteMutation.isPending}
              onConfirm={async () => {
                await deleteMutation.mutateAsync(data.id)
                navigate(appRoutes.approvalSeal.requests)
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
        //  2 cột như trang Đặt xe: nội dung bên trái, Trao đổi + Lịch sử dồn cột phải
        //  (đổi breakpoint lg + 360px cho khớp `/vehicle-booking/:id`).
        <div className="grid gap-5 lg:grid-cols-[minmax(0,1fr)_360px]">
          <div className="flex min-w-0 flex-col gap-5">
            {canEdit ? (
              //  Sửa được thì cả trang là biểu mẫu (kèm đính kèm bên trong form);
              //  lưu/gửi duyệt xong query tự nạp lại nên trang chuyển đúng trạng thái.
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
          <div className="flex flex-col gap-5">
            {/* Luồng duyệt nhiều bước — chỉ hiện khi phiếu đang chạy trong bộ máy
                (bật ApprovalSwitch); cụm nút cổng-1 (TBP) ở đầu trang đã tự ẩn. */}
            {data.approval_running && <SealApprovalPanel requestId={data.id} />}
            {/*  Trao đổi trên phiếu — dùng chung widget bình luận (entity/entityId). */}
            <DocumentComments entity="seal_request" entityId={data.id} />
            {/*  AuditTimeline tự dựng thẻ có tiêu đề — không bọc thêm Card kẻo lặp tiêu đề. */}
            <AuditTimeline entity="seal_request" entityId={data.id} showMessage dense />
          </div>
        </div>
      )}
    </PageContainer>
  )
}
