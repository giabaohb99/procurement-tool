import { AlertTriangle, Clock, ShieldCheck } from 'lucide-react'
import { useState } from 'react'

import { ApprovalActionDialog } from '@/modules/approval/components/approval-action-dialog'
import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance } from '@/modules/approval/types/approval'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'
import { useMyDocumentTask } from '../hooks/use-my-document-approvals'

interface DocumentApprovalBannerProps {
  instance: ApprovalInstance | null | undefined
  /** Văn bản đang mở — để tìm việc duyệt của chính người đọc. */
  documentId: number
}

/**
 * BĂNG TIẾN TRÌNH DUYỆT trên đầu trang chi tiết văn bản.
 *
 * Trước đây trang này chỉ hiện đúng hai chữ «Đang duyệt» — không nói phiếu đang
 * ở bước nào, ai đang giữ, và nhất là không nói khi có chuyện. Người soạn muốn
 * biết chờ ai thì phải đi hỏi người.
 *
 * **Người duyệt bấm NGAY TẠI ĐÂY (21/08/2026).** Bản trước chỉ dẫn họ sang màn
 * «Việc của tôi» rồi bấm trên dòng danh sách — nghĩa là ký một văn bản mà chưa
 * mở nó ra đọc, hoặc phải đi hai vòng: mở văn bản để đọc, rồi quay lại hộp việc
 * để bấm. Nút đặt ở đây thì thứ tự tự nhiên lại đúng: đọc xong, bấm ngay.
 *
 * Hai ca **bắt buộc** phải kêu lên, vì im lặng ở đây là văn bản nằm chết mà
 * không ai biết:
 *
 * - **KẸT** — không tìm được người duyệt, phiếu không tự đi tiếp được;
 * - **duyệt hết bước rồi mà chưa ban hành được** — ví dụ loại này phải kèm một
 *   Quyết định mà chưa khai. Phiên ghi «Đã duyệt» nhưng văn bản vẫn ở *chờ
 *   duyệt* và chưa có số; lý do nằm ở `finish_reason`.
 */
export function DocumentApprovalBanner({ instance, documentId }: DocumentApprovalBannerProps) {
  //  Việc của CHÍNH người đang đọc — `null` là không phải lượt họ. Hỏi hộp việc
  //  chứ không tự suy từ `instance.tasks`: chỉ hộp việc mới biết ai đang được
  //  ủy quyền bấm thay, mà bấm thay người khác là chuyện phải nói trước khi ký.
  const viecCuaToi = useMyDocumentTask(documentId)
  const [dangXuLy, setDangXuLy] = useState(false)

  if (!instance) return null

  const dangCho = (instance.tasks ?? []).filter((row) => row.status === TASK_STATUS.pending)
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

  //  ĐANG CHỜ TÔI: băng đổi hẳn màu và mọc thêm nút. Cùng một màu xám với ca
  //  "chờ người khác" thì thứ duy nhất phân biệt là một dòng chữ nhỏ — mà đây
  //  đúng là dòng người ta cần thấy khi liếc qua trang.
  if (viecCuaToi) {
    return (
      <>
        <div className="mb-3 flex flex-wrap items-center gap-3 rounded-md border border-primary/40 bg-primary/5 px-4 py-3">
          <ShieldCheck className="size-5 shrink-0 text-primary" />
          <div className="min-w-0 flex-1 text-sm">
            <p className="font-semibold">Đang chờ bạn duyệt.</p>
            <p className="text-muted-foreground">
              Bước «{viecCuaToi.node_name || `Bước ${viecCuaToi.node_seq}`}» của luồng «
              {instance.flow_name}»
              {viecCuaToi.started_by_name && ` · ${viecCuaToi.started_by_name} trình`}
              {viecCuaToi.due_at && (
                <span className={viecCuaToi.is_overdue ? 'font-medium text-destructive' : undefined}>
                  {' · '}
                  {viecCuaToi.is_overdue ? 'quá hạn ' : 'hạn '}
                  {formatDate(viecCuaToi.due_at)}
                </span>
              )}
              {/*  Bấm THAY người khác phải hiện TRƯỚC cú bấm: nhật ký sẽ ghi cả
                   hai tên, biết sau khi ký thì đã muộn. */}
              {viecCuaToi.on_behalf_of_name && ` · bạn bấm thay ${viecCuaToi.on_behalf_of_name}`}
            </p>
          </div>
          <Button type="button" onClick={() => setDangXuLy(true)}>
            <ShieldCheck className="size-4" />
            Duyệt / Trả lại
          </Button>
        </div>

        {/*  Dựng hộp thoại KHI MỞ, không dựng sẵn rồi ẩn: nó cắm sẵn một
             mutation duyệt phiếu, mà băng này nằm trên mọi tab của trang chi
             tiết — treo sẵn ở đó cả buổi cho một cú bấm hiếm là thừa. */}
        {dangXuLy && (
          <ApprovalActionDialog task={viecCuaToi} open onOpenChange={setDangXuLy} />
        )}
      </>
    )
  }

  return (
    <div className="mb-3 flex gap-3 rounded-md border bg-muted/40 px-4 py-3">
      <Clock className="mt-0.5 size-4 shrink-0 text-muted-foreground" />
      <div className="text-sm">
        <p className="font-medium">
          Đang chạy luồng «{instance.flow_name}» — bước {instance.current_seq}
          {dangCho.length > 0 && ` · ${dangCho[0].node_name}`}
        </p>
        {dangCho.length > 0 && (
          <p className="text-muted-foreground">
            Chờ {dangCho.map((row) => row.assignee_name).join(', ')} duyệt. Bạn không phải
            làm gì — xem dấu vết ở tab <b>Phê duyệt</b>.
          </p>
        )}
      </div>
    </div>
  )
}
