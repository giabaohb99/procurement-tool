import { Loader2, Send } from 'lucide-react'
import { useCallback, useRef, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'
import { DocumentComments } from '@/modules/procurement/components/document-comments'
import { AuditTimeline } from '@/shared/audit/audit-timeline'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { PageContainer } from '@/shared/ui/page-container'
import { SealApprovalPanel } from '../components/seal-approval-panel'
import { SealDetailBody } from '../components/seal-detail-body'
import { SealDetailHeader } from '../components/seal-detail-header'
import { SealNoteCard } from '../components/seal-note-card'
import { SealProgressCard } from '../components/seal-progress-card'
import { SealRequestForm, type SealFormHandle } from '../components/seal-request-form'
import { SealRequestMoreMenu } from '../components/seal-request-more-menu'
import { SealRequesterCard } from '../components/seal-requester-card'
import { SealWorkflowActions } from '../components/seal-workflow-actions'
import { useSealRequest } from '../hooks/use-seal-requests'
import { SEAL_OUTLINE_BTN } from '../utils/action-button-class'
import { EDITABLE_SEAL_STATUSES } from '../types/seal-request'

/**
 * Trang CHI TIẾT phiếu đóng dấu (`/approval-seal/:id`) — xem + thao tác theo vai trò.
 *
 * Bố cục cải tiến:
 * - Header dính đỉnh màn hình (`sticky top-0`) hiển thị mã phiếu, tiêu đề, trạng thái
 *   và cụm nút thao tác nghiệp vụ.
 * - Thân trang chia 2 cột:
 *   + Cột trái: Thông tin văn bản, pháp nhân đóng dấu, chứng từ đính kèm, rồi Trao đổi
 *     bình luận (`DocumentComments`) và Lịch sử thao tác (`AuditTimeline`).
 *   + Cột phải (cuộn theo trang, KHÔNG ghim): Luồng duyệt nhiều bước, Người yêu cầu
 *     & Đơn vị (`SealRequesterCard`), Tiến trình duyệt & Đóng dấu
 *     (`SealProgressCard`) và Ghi chú người gửi (`SealNoteCard`).
 * - Đang sửa (nháp / trả về chỉnh sửa): cột trái thành biểu mẫu, cột phải rút còn
 *   Luồng duyệt (nếu có) + Người yêu cầu & Đơn vị — hai thẻ kia trùng ô nhập nên ẩn.
 */
export function SealRequestDetailPage() {
  const navigate = useNavigate()
  const { can } = usePermission()
  const { id } = useParams()
  const requestId = Number(id)
  const { data, isLoading, isError } = useSealRequest(Number.isFinite(requestId) ? requestId : null)

  const editable = Boolean(data) && EDITABLE_SEAL_STATUSES.has(data!.status)
  const canEdit = editable && can('seal_request', 'write')
  const canDelete = Boolean(data) && can('seal_request', 'delete')
  const canCreate = can('seal_request', 'create')

  // Nút Lưu nháp / Gửi duyệt do FORM bên dưới thực thi qua `ref`
  const formRef = useRef<SealFormHandle>(null)
  const [saving, setSaving] = useState(false)
  const onPendingChange = useCallback((p: boolean) => setSaving(p), [])

  //  ⚠️ Thứ tự và trọng lượng của dải nút này là CÓ CHỦ Ý (xếp lại 22/09/2026):
  //  trước hết là việc PHẢI LÀM với phiếu (duyệt / gửi duyệt), rồi tới vạch ngăn,
  //  cuối cùng là menu «…» chứa mấy việc lúc nào làm cũng được (in · nhân bản ·
  //  xóa). Bày cả sáu thành nút ngang thì người duyệt phải đọc hết sáu nhãn mới
  //  tìm ra nút của mình, mà tên văn bản — thứ đáng đọc trước khi bấm — bị bóp
  //  còn một nửa.
  const headerActions = data ? (
    <>
      <SealWorkflowActions request={data} />
      {canEdit && (
        <>
          <Button
            variant="outline"
            className={SEAL_OUTLINE_BTN}
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

      {/*  ⚠️ ĐỪNG chèn vạch ngăn dọc vào giữa dải nút này (đã thử rồi bỏ,
          22/09/2026). Vạch `w-px` + `mx-0.5` nằm trong hàng `gap-2` làm khoảng
          hở chỗ đó thành **21px** trong khi mọi khoảng khác là 8px — đo trên
          trình duyệt. Bản thân vạch màu `border` trên nền tiêu đề gần như không
          thấy, nên mắt không đọc ra "ngăn nhóm", chỉ đọc ra một lỗ trống giữa
          dải nút. Nút «…» vốn đã khác hẳn phần còn lại (vuông, chỉ có biểu
          tượng) nên tự nó đã tách nhóm; nhịp đều 8px đáng giá hơn. */}
      <SealRequestMoreMenu request={data} canCreate={canCreate} canDelete={canDelete} />
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
        //  ⚠️ Rãnh 380px này phải LUÔN có thứ để bày. Bản 22/09/2026 từng gác cả ba
        //  thẻ chỉ-đọc bằng `!canEdit`, nên phiếu NHÁP ra một dải trắng 380px bên
        //  phải — người dùng đọc ra "màn hình hỏng", không đọc ra "chưa có gì".
        //  Thêm thẻ vào cột này thì nhớ tự hỏi nó còn gì để nói khi phiếu mới lập.
        <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_380px]">
          {/*  Cột trái — mạch *văn bản này là gì* (văn bản → pháp nhân → chứng từ),
               rồi tới hai khung DÀI RA THEO THỜI GIAN: Trao đổi và Lịch sử thao tác.
               Cả hai ở đây (22/09/2026) vì cần bề ngang: Trao đổi có ô để gõ vào —
               ô nhập rộng 380px thì một câu ba dòng đọc như cột báo; Lịch sử thì
               mỗi dòng là một câu tự mô tả kèm mốc giờ, cột hẹp là gãy đôi. */}
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
            <DocumentComments entity="seal_request" entityId={data.id} />
            <AuditTimeline entity="seal_request" entityId={data.id} showMessage dense />
          </div>

          {/*  Cột phải — mạch *phiếu đang ở đâu, ai dặn gì*: luồng duyệt → người
               yêu cầu → dấu vết duyệt/đóng dấu → ghi chú người gửi.

               ⚠️ **KHÔNG có vùng cuộn riêng** (đại ca chốt 22/09/2026, cùng luật
               đã áp cho phiếu đặt xe ở CR-439): không `sticky`, không `max-h`,
               không `overflow-y-auto` — cả cột cuộn theo trang. Bản trước ghim cột
               này dưới tiêu đề rồi cho nó tự cuộn bên trong, nên trang có HAI vùng
               cuộn cạnh nhau: bánh xe chuột đổi nghĩa tùy con trỏ đang đậu ở nửa
               nào, mà thanh cuộn con trong một cột 380px thì vừa khó thấy vừa khó
               bấm. Đừng dựng lại; muốn thấy khung nào trong lúc đọc phiếu thì xếp
               nó lên ĐẦU cột, đừng ghim cả cột. */}
          <div className="flex flex-col gap-5">
            {/*  Gác bằng `approval_instance_id` (phiên gần nhất, kể cả đã xong) chứ
                 KHÔNG bằng `approval_running`: thẻ này chứa cả Lịch sử phê duyệt,
                 gác bằng cờ "đang chạy" thì duyệt xong là dấu vết biến mất. */}
            {data.approval_instance_id != null && <SealApprovalPanel requestId={data.id} />}
            {/*  Người yêu cầu & Đơn vị dựng ở MỌI chế độ, kể cả đang sửa nháp: bốn
                 dòng của nó (tên · chức danh · email · điện thoại) lấy từ hồ sơ người
                 lập, KHÔNG phải ô nhập của biểu mẫu nên không có chuyện hai bản lệch
                 nhau. Tiêu đề phiếu chỉ có tên + chức danh, người văn thư còn cần
                 email/điện thoại để gọi lại khi văn bản thiếu trang. */}
            <SealRequesterCard request={data} />
            {/*  Tiến trình «ai lập → ai duyệt → ai đóng dấu» — dựng ở mọi chế độ; lúc
                 đang sửa nó tự bỏ TÊN người sẽ duyệt (giá trị đó là ô chọn bên trái),
                 xem chú thích trong `utils/build-seal-stages.ts`. */}
            <SealProgressCard request={data} editing={canEdit} />
            {/*  Ghi chú thì KHÔNG: nó là đúng cái ô nhập ở cuối biểu mẫu bên trái, dựng
                 thêm bản chỉ-đọc ở đây là hai bản của cùng một chuỗi, lệch nhau ngay
                 khi người ta gõ. */}
            {!canEdit && <SealNoteCard request={data} />}
          </div>
        </div>
      )}
    </PageContainer>
  )
}
