import { AlertTriangle, Clock } from 'lucide-react'
import { Link } from 'react-router-dom'

import { useAuth } from '@/core/auth/use-auth'
import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance } from '@/modules/approval/types/approval'
import { appRoutes } from '@/shared/constants/app-routes'

interface DocumentApprovalBannerProps {
  instance: ApprovalInstance | null | undefined
}

/**
 * BĂNG TIẾN TRÌNH DUYỆT trên đầu trang chi tiết văn bản.
 *
 * Trước đây trang này chỉ hiện đúng hai chữ «Đang duyệt» — không nói phiếu đang
 * ở bước nào, ai đang giữ, và nhất là không nói khi có chuyện. Người soạn muốn
 * biết chờ ai thì phải đi hỏi người.
 *
 * Hai ca **bắt buộc** phải kêu lên, vì im lặng ở đây là văn bản nằm chết mà
 * không ai biết:
 *
 * - **KẸT** — không tìm được người duyệt, phiếu không tự đi tiếp được;
 * - **duyệt hết bước rồi mà chưa ban hành được** — ví dụ loại này phải kèm một
 *   Quyết định mà chưa khai. Phiên ghi «Đã duyệt» nhưng văn bản vẫn ở *chờ
 *   duyệt* và chưa có số; lý do nằm ở `finish_reason`.
 */
export function DocumentApprovalBanner({ instance }: DocumentApprovalBannerProps) {
  const { user } = useAuth()

  if (!instance) return null

  const dangCho = (instance.tasks ?? []).filter((row) => row.status === TASK_STATUS.pending)
  //  Việc này có phải của CHÍNH người đang đọc không. Quan trọng: «Việc của tôi»
  //  chỉ liệt kê việc của người đăng nhập, nên dẫn người ngoài cuộc sang đó là
  //  quăng họ vào một danh sách rỗng — họ tưởng hệ thống hỏng.
  const toiPhaiXuLy =
    Boolean(user?.employee_id) &&
    dangCho.some((row) => row.assignee_employee_id === user?.employee_id)
  const dangChay = instance.status === INSTANCE_STATUS.running
  const ket = instance.status === INSTANCE_STATUS.blocked
  //  Đã duyệt xong mà vẫn còn lý do ghi lại = có gì đó chưa hoàn tất được.
  const chuaHoanTat = instance.status === INSTANCE_STATUS.approved && Boolean(instance.finish_reason)

  if (ket || chuaHoanTat) {
    return (
      <div className="mb-3 flex gap-3 rounded-md border border-destructive/40 bg-destructive/5 px-4 py-3">
        <AlertTriangle className="mt-0.5 size-4 shrink-0 text-destructive" />
        <div className="text-sm">
          <p className="font-medium">
            {ket ? 'Phiếu duyệt đang kẹt.' : 'Đã duyệt hết các bước nhưng văn bản CHƯA ban hành.'}
          </p>
          {instance.finish_reason && (
            <p className="text-muted-foreground">{instance.finish_reason}</p>
          )}
        </div>
      </div>
    )
  }

  if (!dangChay) return null

  return (
    <div className="mb-3 flex gap-3 rounded-md border bg-muted/40 px-4 py-3">
      <Clock className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="text-sm">
        <p className="font-medium">
          Đang chạy luồng «{instance.flow_name}» — bước {instance.current_seq}
          {dangCho.length > 0 && ` · ${dangCho[0].node_name}`}
        </p>
        {/*  Hai câu khác hẳn nhau tùy người đọc là ai.

             Bản cũ nói với tất cả mọi người là "xử lý ở màn «Việc của tôi»" —
             sai với 9/10 người mở trang này, vì màn đó chỉ có việc của CHÍNH
             họ. Người soạn bấm sang chỉ thấy danh sách rỗng. */}
        {dangCho.length > 0 &&
          (toiPhaiXuLy ? (
            <p className="text-muted-foreground">
              <b className="text-foreground">Đang chờ bạn duyệt.</b>{' '}
              <Link to={appRoutes.approval.myTasks} className="font-medium underline">
                Mở «Việc của tôi» để xử lý
              </Link>
              .
            </p>
          ) : (
            <p className="text-muted-foreground">
              Chờ {dangCho.map((row) => row.assignee_name).join(', ')} duyệt. Bạn không phải
              làm gì — xem dấu vết ở tab <b>Phê duyệt</b>.
            </p>
          ))}
      </div>
    </div>
  )
}
