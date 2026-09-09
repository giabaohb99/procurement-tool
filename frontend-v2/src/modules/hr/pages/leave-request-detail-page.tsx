import { useState } from 'react'
import { useLocation, useNavigate, useParams } from 'react-router-dom'
import { ArrowLeft, Ban, Check, Save, Send, Trash2, X } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Button } from '@/shared/ui/button'
import { Card, CardContent } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import { formatDateTime } from '@/shared/utils/format-date'
import { LeaveApprovalTimeline } from '../components/leave-approval-timeline'
import { LeaveDetailDecisionActions } from '../components/leave-detail-decision-actions'
import { LeaveStatusBadge } from '../components/leave-status-badge'
import { LeaveRequestForm } from '../components/leave-request-form'
import {
  emptyLeaveForm,
  formValuesOf,
  toLeavePayload,
  type LeaveFormValues,
} from '../utils/leave-form-values'
import { LeaveRequestSummary } from '../components/leave-request-summary'
import {
  PRIMARY_ACTION_SLOT,
  SECONDARY_ACTION_SLOT,
} from '../utils/leave-detail-action-slots'
import {
  useDeleteLeaveRequest,
  useLeaveRequest,
  useLeaveRequestAction,
  useSaveLeaveRequest,
} from '../hooks/use-leave'
import { EDITABLE_LEAVE_STATUSES, LEAVE_STATUS } from '../types/leave'

/**
 * CHI TIẾT / TẠO MỚI đơn nghỉ phép — một trang cho cả hai, phân biệt bằng `:id`.
 *
 * Đơn còn sửa được (Nháp hoặc Trả về) thì dựng `LeaveRequestForm`; đã gửi duyệt
 * thì dựng `LeaveRequestSummary`. **Không** dựng form với cờ `disabled` —
 * xem docstring của `leave-request-summary.tsx`.
 */
export function LeaveRequestDetailPage() {
  const { id } = useParams<{ id: string }>()
  const requestId = Number(id) || 0
  const navigate = useNavigate()
  const location = useLocation()
  const { can } = usePermission()

  //  ⚠️ Nút «Về danh sách» phải LÙI THEO LỊCH SỬ, không điều hướng cứng về
  //  `/hr/leave-requests`. Đường cứng mất sạch trạng thái người dùng vừa đặt:
  //  màn danh sách có ba tab và mỗi tab một bộ lọc, mà URL sạch thì nó tự chọn
  //  lại tab mặc định — bấm từ tab «Đơn của tôi» lại rơi về «Cần tôi duyệt»
  //  (lỗi báo 04/09/2026), và bộ lọc vừa gõ cũng bay theo.
  //
  //  `location.key === 'default'` = đây là trang ĐẦU TIÊN của phiên (vào thẳng
  //  từ link trong thư báo việc, hoặc dán URL). Lùi lúc đó là đẩy người dùng ra
  //  khỏi ứng dụng, nên mới rơi về danh sách.
  const goBack = () => {
    if (location.key === 'default') navigate(appRoutes.hr.leaveRequests)
    else navigate(-1)
  }

  const { data: request, isLoading } = useLeaveRequest(requestId)
  const save = useSaveLeaveRequest()
  const remove = useDeleteLeaveRequest()
  const act = useLeaveRequestAction()

  const [form, setForm] = useState<LeaveFormValues>(emptyLeaveForm)

  //  Việc nào GHI LÝ DO vào sổ thì phải hỏi lý do. Trước đây hai nút này gửi
  //  câu cứng ("Người nộp hủy"), nên dòng thời gian của mọi tờ đơn hủy đều nói
  //  đúng một câu vô nghĩa như nhau.
  const [reasonFor, setReasonFor] = useState<'reject' | 'cancel' | null>(null)

  //  Nạp giá trị vào form khi đổi sang MỘT TỜ ĐƠN KHÁC — theo `id`, không theo
  //  tham chiếu của `request`. Theo tham chiếu thì mọi lượt nạp lại cache sẽ xóa
  //  những gì người dùng vừa gõ.
  //
  //  Đặt trong lúc render chứ không trong `useEffect`: effect chạy sau khi đã
  //  commit nên người dùng thấy một khung hình với form RỖNG rồi mới thấy dữ
  //  liệu. Xem `shared/hooks/use-has-changed.ts`.
  if (useHasChanged(request?.id ?? 0) && request) {
    setForm(formValuesOf(request))
  }

  const isNew = requestId === 0
  const editable = isNew || (request ? EDITABLE_LEAVE_STATUSES.includes(request.status) : false)
  const canWrite = can('leave_request', isNew ? 'create' : 'write')
  const canApprove = can('leave_request', 'approve')
  const canCancel = can('leave_request', 'cancel')

  const submitSave = () => {
    save.mutate(
      { id: isNew ? undefined : requestId, values: toLeavePayload(form) },
      {
        onSuccess: (saved) => {
          if (isNew) navigate(appRoutes.hr.leaveRequestDetail(saved.id), { replace: true })
        },
      },
    )
  }

  //  ⚠️ GỬI DUYỆT PHẢI LƯU TRƯỚC. Backend kiểm «đã nhập đủ» trên BẢN ĐÃ LƯU
  //  (`request_service.check_ready_to_submit`), còn người dùng thì đang nhìn
  //  chữ họ vừa gõ. Trước 07/09/2026 nút này gửi thẳng, nên gõ lý do rồi bấm
  //  Gửi duyệt ăn đúng câu «Thiếu Lý do nghỉ — nhập đủ trước khi gửi duyệt» —
  //  một câu chặn nói ngược lại thứ đang hiện trên màn hình, không cách nào
  //  đoán ra là phải bấm «Lưu nháp» trước.
  const saveThenSubmit = () => {
    save.mutate(
      { id: requestId, values: toLeavePayload(form) },
      { onSuccess: () => act.mutate({ id: requestId, action: 'submit' }) },
    )
  }

  if (!isNew && isLoading) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Đang tải đơn…</p>
      </PageContainer>
    )
  }

  if (!isNew && !request) {
    return (
      <PageContainer>
        <p className="text-sm text-muted-foreground">Không tìm thấy đơn nghỉ phép này.</p>
      </PageContainer>
    )
  }

  return (
    <PageContainer>
      {/*  Nhóm nút nằm TRÊN ĐẦU và dính khi cuộn: form dài hơn một màn, để nút
           «Lưu nháp» dưới đáy thì mỗi lần lưu là một lần cuộn xuống rồi cuộn
           ngược lên. Xem `sticky` của `PageHeader`. */}
      <PageHeader
        sticky
        leading={
          //  Chỉ icon: đứng sát tiêu đề thì mũi tên đã đủ nghĩa "lùi ra danh
          //  sách", thêm chữ chỉ đẩy tiêu đề đi xa.
          <Button
            variant="outline"
            size="icon"
            title="Về danh sách"
            aria-label="Về danh sách"
            onClick={goBack}
          >
            <ArrowLeft className="size-4" />
          </Button>
        }
        title={isNew ? 'Nộp đơn nghỉ phép' : `Đơn nghỉ phép ${request?.code}`}
        description={
          //  ⚠️ Huy hiệu trạng thái đi CÙNG DÒNG MÔ TẢ, không đứng chung với
          //  nhóm nút. Trên điện thoại nhóm nút chiếm trọn bề ngang và xuống
          //  dòng theo lưới; nhét một huy hiệu vào giữa thì nó ăn mất một ô của
          //  lưới đó và mọi nút sau nó lệch đi một nhịp (ảnh báo 09/09/2026:
          //  «Chờ duyệt» + 2 nút ở hàng trên, «Hủy đơn» rơi lẻ xuống hàng dưới).
          //  Trạng thái vốn là thông tin về tờ đơn, không phải một hành động.
          <>
            {request && <LeaveStatusBadge status={request.status} label={request.status_label} />}
            <span>
              {request?.submitted_at
                ? `Gửi duyệt lúc ${formatDateTime(request.submitted_at)}`
                : //  Nút «Gửi duyệt» nay tự lưu trước, nên câu cũ ("Lưu nháp rồi
                  //  gửi duyệt") mô tả một thao tác không còn bắt buộc.
                  'Gửi duyệt sẽ tự lưu những gì đang nhập.'}
            </span>
          </>
        }
        actions={
          /*  NHÓM NÚT — hàng ngang bám mép phải từ `md`; dưới `md` thì MỘT nút
              chính trải hết hàng trên, những nút còn lại chia đều hàng dưới.
              Việc ngắt hàng do chính các nút tự lo bằng `basis-full` /
              `flex-1` — xem `utils/leave-detail-action-slots.ts`, ở đó có cả lý
              do vì sao không xếp lưới đều tăm tắp nữa. */
          <div className="flex w-full flex-wrap items-center gap-2 md:w-auto md:justify-end">
            {editable && canWrite && (
              <>
                {!isNew && can('leave_request', 'delete') && (
                  <Button
                    variant="outline"
                    className={SECONDARY_ACTION_SLOT}
                    onClick={() =>
                      remove.mutate(requestId, {
                        onSuccess: () => navigate(appRoutes.hr.leaveRequests),
                      })
                    }
                    disabled={remove.isPending}
                  >
                    <Trash2 className="size-4" />
                    Xóa đơn
                  </Button>
                )}
                {/*  ⚠️ «Lưu nháp» chỉ là nút CHÍNH khi đơn chưa có id — lúc đó
                     nó là việc duy nhất làm được. Đơn đã lưu rồi thì việc người
                     ta định làm là GỬI DUYỆT, mà hai nút xanh đặc đứng cạnh nhau
                     thì chẳng nút nào còn là nút chính nữa. */}
                <Button
                  variant={isNew ? 'default' : 'outline'}
                  className={isNew ? PRIMARY_ACTION_SLOT : SECONDARY_ACTION_SLOT}
                  onClick={submitSave}
                  disabled={save.isPending}
                >
                  <Save className="size-4" />
                  Lưu nháp
                </Button>
                {/*  Gửi duyệt chỉ hiện khi đơn ĐÃ có id: gửi một tờ đơn chưa lưu
                     thì không có gì để trình. */}
                {!isNew && (
                  <Button
                    className={PRIMARY_ACTION_SLOT}
                    onClick={saveThenSubmit}
                    disabled={act.isPending || save.isPending}
                  >
                    <Send className="size-4" />
                    Gửi duyệt
                  </Button>
                )}
              </>
            )}

            {/*  Đơn ĐANG CHẠY TRONG LUỒNG: ba nút quyết định của bộ máy, và chỉ
                 hiện cho người đang thật sự phải ký (CR-260). Xem docstring của
                 `LeaveDetailDecisionActions`. */}
            {request && request.approval_instance_id > 0 && (
              <LeaveDetailDecisionActions requestId={requestId} />
            )}

            {/*  Duyệt / từ chối THẲNG — chỉ dùng khi môi trường CHƯA khai luồng
                 nhiều bước.

                 ⚠️ Điều kiện `approval_instance_id === 0` không được bỏ. Thiếu
                 nó thì đơn đang chạy trong luồng vẫn hiện hai nút này, và bấm
                 vào chỉ ăn *"Đơn này đang chạy trong luồng phê duyệt nhiều bước"*
                 — câu đúng luật nhưng vô nghĩa với người vừa bấm nút Duyệt, và
                 nó lại nằm ngay cạnh ba nút duyệt THẬT ở trên. */}
            {request?.status === LEAVE_STATUS.PENDING &&
              request.approval_instance_id === 0 &&
              canApprove && (
              <>
                <Button
                  variant="outline"
                  className={SECONDARY_ACTION_SLOT}
                  onClick={() => setReasonFor('reject')}
                  disabled={act.isPending}
                >
                  <X className="size-4" />
                  Từ chối
                </Button>
                <Button
                  className={PRIMARY_ACTION_SLOT}
                  onClick={() => act.mutate({ id: requestId, action: 'approve' })}
                  disabled={act.isPending}
                >
                  <Check className="size-4" />
                  Duyệt đơn
                </Button>
              </>
              )}

            {request &&
              (request.status === LEAVE_STATUS.PENDING ||
                request.status === LEAVE_STATUS.APPROVED) &&
              canCancel && (
                <Button
                  variant="outline"
                  className={SECONDARY_ACTION_SLOT}
                  onClick={() => setReasonFor('cancel')}
                  disabled={act.isPending}
                >
                  <Ban className="size-4" />
                  Hủy đơn
                </Button>
              )}
          </div>
        }
      />

      {/*  `PageContainer` KHÔNG tự chèn khoảng hở giữa các con — phải có lớp bọc
           `space-y-*` này, không thì thẻ đơn và thẻ luồng duyệt dính liền nhau
           thành một khối viền đôi. */}
      <div className="space-y-4">
        {/*  Form tự dựng thẻ của nó (`FormCard`) nên KHÔNG bọc thêm một `Card`
             nữa ở đây — thẻ lồng thẻ là hai lớp viền và hai lớp đệm. */}
        {editable && canWrite ? (
          <LeaveRequestForm value={form} onChange={setForm} request={request} />
        ) : (
          request && (
            <Card className="py-4 sm:py-6">
              {/*  Lề trong hẹp lại trên điện thoại: `px-6` mặc định ăn 48px của
                   một màn 390px, tức 12% bề ngang chỉ để lấy khoảng trắng. */}
              <CardContent className="px-3 sm:px-6">
                <LeaveRequestSummary request={request} />
              </CardContent>
            </Card>
          )
        )}

        {/*  Luồng duyệt đặt DƯỚI nội dung đơn: người mở màn này đọc tờ đơn trước,
             rồi mới hỏi "ai đang giữ nó". Đơn chưa lưu (`isNew`) thì chưa có gì
             để kể. */}
        {request && <LeaveApprovalTimeline request={request} />}
      </div>

      <ReasonConfirmDialog
        open={reasonFor !== null}
        onOpenChange={(open) => !open && setReasonFor(null)}
        title={reasonFor === 'cancel' ? 'Hủy đơn nghỉ phép' : 'Từ chối đơn nghỉ phép'}
        description={
          reasonFor === 'cancel'
            ? 'Đơn sẽ dừng lại và số ngày đang giữ chỗ được trả về quỹ phép. Lý do hiện trên dòng thời gian của đơn.'
            : 'Người nộp sẽ đọc đúng câu này để biết phải sửa gì.'
        }
        placeholder={reasonFor === 'cancel' ? 'Vì sao không nghỉ nữa?' : 'Vì sao không duyệt?'}
        confirmText={reasonFor === 'cancel' ? 'Hủy đơn' : 'Từ chối'}
        destructive
        pending={act.isPending}
        onConfirm={(reason) => {
          if (!reasonFor) return
          act.mutate(
            { id: requestId, action: reasonFor, reason },
            { onSuccess: () => setReasonFor(null) },
          )
        }}
      />
    </PageContainer>
  )
}
