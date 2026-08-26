import { Check, CircleDashed, CircleDot, MinusCircle, ShieldCheck, X } from 'lucide-react'
import { useState } from 'react'

import { ApprovalActionDialog } from '@/modules/approval/components/approval-action-dialog'
import { ApprovalTrailCard } from '@/modules/approval/components/approval-trail-card'
import { INSTANCE_STATUS, TASK_STATUS } from '@/modules/approval/types/approval'
import type { ApprovalInstance, ApprovalTask } from '@/modules/approval/types/approval'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/shared/ui/card'
import { HelpHint } from '@/shared/ui/help-hint'
import { cn } from '@/shared/utils/cn'
import { useMyDocumentTask } from '../hooks/use-my-document-approvals'

interface DocumentApprovalTabProps {
  instance: ApprovalInstance | null | undefined
  /** Văn bản đang mở — để tìm việc duyệt của chính người đọc. */
  documentId: number
}

/**
 * NGƯỜI DUYỆT CỦA MỘT CHẶNG — mặc định hiện ĐÚNG MỘT người.
 *
 * ⚠️ Bỏ hẳn những lượt giao việc **đã hủy**. Trả phiếu về một bước phía trước
 * thì bộ máy hủy việc cũ rồi mở việc mới, nên chặng đó tích lại nhiều lượt giao
 * cho cùng những con người ấy. Bản cũ liệt kê tất — người dùng thấy bốn dòng,
 * ba dòng «Đã hủy», hai dòng trùng tên nhau, và không đọc ra ai mới là người
 * thật sự đã ký (ảnh người dùng gửi 24/08/2026). Dấu vết đầy đủ vẫn còn nguyên
 * ở thẻ «Dấu vết duyệt» ngay bên dưới — đó mới là chỗ để tra từng lượt bấm.
 *
 * Xếp người ĐÃ QUYẾT lên trước: câu người đọc cần là *"ai ký chặng này"*, không
 * phải *"ai được giao"*.
 */
function StageApprovers({ viec }: { viec: ApprovalTask[] }) {
  const [moRong, setMoRong] = useState(false)

  const stillActive = viec.filter((row) => row.status !== TASK_STATUS.cancelled)
  const decided = (row: ApprovalTask) =>
    row.status === TASK_STATUS.approved ||
    row.status === TASK_STATUS.rejected ||
    row.status === TASK_STATUS.skippedDuplicate
  const rank = [
    ...stillActive.filter(decided),
    ...stillActive.filter((row) => !decided(row)),
  ]
  if (rank.length === 0) return null

  const hien = moRong ? rank : rank.slice(0, 1)
  const remaining = rank.length - hien.length

  return (
    <div className="mt-1.5 text-sm leading-5">
      <span className="text-xs text-muted-foreground">
        {rank.length > 1 ? 'Người duyệt chặng này:' : 'Người duyệt:'}
      </span>
      <ul className="mt-0.5 space-y-1">
        {hien.map((row) => (
          <li key={row.id} className="text-muted-foreground">
            <span className="font-medium text-foreground">{row.assignee_name}</span>
            {/*  Nhiều người cùng chặng thì mỗi người một trạng thái riêng —
                 thấy ngay còn thiếu chữ ký nào. */}
            {rank.length > 1 && (
              <>
                <span aria-hidden="true"> · </span>
                {row.status_label}
              </>
            )}
          </li>
        ))}
      </ul>
      {(remaining > 0 || moRong) && (
        <Button
          type="button"
          variant="link"
          size="sm"
          className="h-auto p-0 text-xs"
          onClick={() => setMoRong((truoc) => !truoc)}
        >
          {moRong ? 'Thu gọn' : `Xem thêm ${remaining} người`}
        </Button>
      )}
    </div>
  )
}

/** Bộ mặt của một chặng, gộp từ trạng thái các việc thuộc chặng đó. */
function stageStatus(viec: ApprovalTask[], seq: number, instance: ApprovalInstance) {
  const cua = viec.filter((row) => row.node_seq === seq)
  if (cua.some((row) => row.status === TASK_STATUS.rejected)) return 'tu-choi'
  if (cua.some((row) => row.status === TASK_STATUS.pending)) return 'dang-cho'
  if (cua.length > 0 && cua.every((row) => row.status === TASK_STATUS.skippedDuplicate))
    return 'tu-qua'
  if (cua.some((row) => row.status === TASK_STATUS.approved)) return 'xong'
  //  Chưa có việc nào ở chặng này: hoặc chưa tới lượt, hoặc phiếu đã dừng trước
  //  khi tới đây. Cả hai đều vẽ như nhau — chặng chưa chạm tới.
  return instance.current_seq > seq ? 'khong-chay' : 'chua-toi'
}

/**
 * Bộ mặt của từng trạng thái chặng.
 *
 * `huy_hieu` tô CÙNG TÔNG với `nut` (chấm tròn trên đường kẻ) để hai thứ đọc ra
 * một trạng thái, không phải hai. Trước đây nhãn là chữ mờ 12px nằm cạnh tiêu đề
 * chặng, nên "Đã duyệt" và "Tự qua vì trùng người" — hai chuyện KHÁC HẲN nhau
 * về trách nhiệm — trông y như nhau khi lướt mắt.
 *
 * `giai_thich` là câu cho nút `?`: mấy nhãn này ngắn tới mức mơ hồ ("Không chạy"
 * là lỗi hay là bình thường?).
 */
const HINH = {
  xong: {
    icon: Check,
    nut: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    huy_hieu: 'border-emerald-200 bg-emerald-50 text-emerald-700',
    nhan: 'Đã duyệt',
    giai_thich: 'Người ở chặng này đã ký duyệt.',
  },
  'dang-cho': {
    icon: CircleDot,
    nut: 'border-sky-200 bg-sky-50 text-sky-700',
    huy_hieu: 'border-sky-200 bg-sky-50 text-sky-700',
    nhan: 'Đang chờ',
    giai_thich: 'Phiếu đang nằm ở chặng này, chờ người bên dưới xử lý.',
  },
  'tu-choi': {
    icon: X,
    nut: 'border-destructive/30 bg-destructive/5 text-destructive',
    huy_hieu: 'border-destructive/30 bg-destructive/5 text-destructive',
    nhan: 'Từ chối',
    giai_thich: 'Người ở chặng này đã từ chối, luồng dừng tại đây.',
  },
  'tu-qua': {
    icon: MinusCircle,
    nut: 'border-border bg-muted text-muted-foreground',
    huy_hieu: 'border-border bg-muted text-muted-foreground',
    nhan: 'Tự qua vì trùng người',
    giai_thich:
      'Người của chặng này đã ký ở một chặng trước, nên hệ thống bỏ qua — KHÔNG phải có thêm một người xem xét.',
  },
  'chua-toi': {
    icon: CircleDashed,
    nut: 'border-border bg-background text-muted-foreground',
    huy_hieu: 'border-border bg-background text-muted-foreground',
    nhan: 'Chưa tới lượt',
    giai_thich: 'Phiếu chưa đi tới chặng này.',
  },
  'khong-chay': {
    icon: CircleDashed,
    nut: 'border-border bg-muted text-muted-foreground',
    huy_hieu: 'border-border bg-muted text-muted-foreground',
    nhan: 'Không chạy',
    giai_thich: 'Luồng đã dừng trước khi tới chặng này — bình thường, không phải lỗi.',
  },
} as const

/**
 * Tab PHÊ DUYỆT của trang chi tiết văn bản: phiếu này đang đi tới đâu.
 *
 * Trang chi tiết trước đây không nói gì về luồng duyệt ngoài hai chữ «Đang
 * duyệt», nên người soạn không biết chờ ai còn người vừa ký không biết mình
 * đang đứng ở khúc nào của một luồng bốn bước.
 *
 * Hai kiểu bước dễ đọc nhầm nên phải phân biệt bằng mắt:
 *
 * - **nhiều người trong CÙNG một chặng** — mỗi người một dòng con, thấy ngay còn
 *   thiếu chữ ký nào;
 * - **tự qua vì trùng người duyệt** — KHÁC "đã duyệt", vẽ mờ và nói rõ, vì gộp
 *   làm một là bản in nói dối rằng có thêm một người đã xem xét.
 *
 * **Nút duyệt CÓ ở đây (21/08/2026)** — nhưng chỉ hiện với đúng người đang cầm
 * việc, và vẫn là hộp thoại chung của bộ máy duyệt chứ không phải một đường
 * riêng của phân hệ Văn bản. Bản trước cố ý không có nút và bắt sang «Việc của
 * tôi»: người duyệt phải rời văn bản đang đọc để đi bấm ở một danh sách, hoặc
 * ký mà chưa mở văn bản ra.
 */
export function DocumentApprovalTab({ instance, documentId }: DocumentApprovalTabProps) {
  const myTasks = useMyDocumentTask(documentId)
  const [dangXuLy, setDangXuLy] = useState(false)

  if (!instance) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-sm text-muted-foreground">
          Văn bản này chưa vào bộ máy duyệt nhiều bước.
          <br />
          Nó đi theo luồng duyệt một bước cũ, hoặc chưa được gửi duyệt lần nào.
        </CardContent>
      </Card>
    )
  }

  const viec = instance.tasks ?? []
  const chang = [...new Set((instance.steps ?? []).map((buoc) => buoc.seq))].sort((a, b) => a - b)

  return (
    <div className="space-y-4">
      <Card className="gap-0 py-0">
        <CardHeader className="flex min-h-16 flex-row items-start justify-between gap-4 border-b px-5 py-4">
          <div className="min-w-0">
            <CardTitle className="text-base">
              Luồng «{instance.flow_name}» bản {instance.flow_version}
            </CardTitle>
            <CardDescription className="mt-0.5">
              Đường đi của phiếu, đọc từ trên xuống theo thứ tự chặng.
            </CardDescription>
          </div>
          <div className="flex items-center gap-3">
            <Badge
              variant={
                instance.status === INSTANCE_STATUS.approved
                  ? 'default'
                  : instance.status === INSTANCE_STATUS.blocked ||
                      instance.status === INSTANCE_STATUS.rejected
                    ? 'destructive'
                    : 'outline'
              }
            >
              {instance.status_label}
            </Badge>
            {/*  Chỉ đúng người đang cầm việc mới thấy nút. Bày cho mọi người là
                 đẻ lại đúng cái đường tắt mà bộ máy duyệt vừa bịt. */}
            {myTasks && (
              <Button type="button" size="sm" onClick={() => setDangXuLy(true)}>
                <ShieldCheck className="size-4" />
                Duyệt / Trả lại
              </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="px-5 py-5">
          <ol aria-label="Các chặng phê duyệt" className="max-w-5xl">
            {chang.map((seq, index) => {
              const ten =
                (instance.steps ?? []).find((buoc) => buoc.seq === seq)?.name || `Bước ${seq}`
              const status = stageStatus(viec, seq, instance)
              const { icon: Icon, nut, huy_hieu, nhan, giai_thich } = HINH[status]
              const nguoi = viec.filter((row) => row.node_seq === seq)
              const current = instance.status === INSTANCE_STATUS.running && seq === instance.current_seq

              return (
                <li
                  key={seq}
                  className="relative flex gap-4 pb-6 last:pb-0"
                  aria-current={current ? 'step' : undefined}
                >
                  {index < chang.length - 1 && (
                    <span
                      data-testid="approval-flow-step-rail"
                      aria-hidden="true"
                      className="approval-flow-step-rail"
                    />
                  )}
                  <span
                    className={cn(
                      'relative z-10 grid size-8 shrink-0 place-items-center rounded-full border',
                      nut,
                    )}
                    aria-hidden="true"
                  >
                    <Icon className="size-4" strokeWidth={2.25} />
                  </span>

                  <div className="min-w-0 flex-1 pt-1">
                    <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
                      <h3 className="text-sm leading-5 font-semibold">
                        Chặng {seq} · {ten}
                      </h3>

                      {/*  Huy hiệu cùng tông với chấm tròn, không còn là chữ mờ
                           lẫn vào tiêu đề — xem ghi chú ở `HINH`. */}
                      <Badge variant="outline" className={cn('font-normal', huy_hieu)}>
                        {nhan}
                      </Badge>
                      <HelpHint label={`«${nhan}» nghĩa là gì`}>{giai_thich}</HelpHint>

                      {/*  `aria-current` ở `<li>` chỉ trình đọc màn hình mới nghe
                           thấy. Người nhìn bằng mắt cũng cần biết phiếu ĐANG nằm
                           ở đâu trong luồng bốn bước. */}
                      {current && (
                        <Badge className="font-normal">phiếu đang ở đây</Badge>
                      )}
                    </div>

                    {/*  Tên người phải có NHÃN. Đứng trơ một mình dưới tiêu đề
                         chặng thì không đọc ra được đó là người phải ký, người
                         đã ký, hay người soạn. */}
                    <StageApprovers viec={nguoi} />
                  </div>
                </li>
              )
            })}
          </ol>
        </CardContent>
      </Card>

      <ApprovalTrailCard instanceId={instance.id} />

      {dangXuLy && myTasks && (
        <ApprovalActionDialog task={myTasks} open onOpenChange={setDangXuLy} />
      )}
    </div>
  )
}
