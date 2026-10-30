import { FilePen, Info, Loader2, Undo2 } from 'lucide-react'
import { useRef, useState } from 'react'

import { ChangeRequestChangesList } from './change-request-changes-list'
import { EmployeeChangeRequestStatusBadge } from './employee-change-request-status-badge'
import { SelfChangeRequestDialog } from './self-change-request-dialog'
import {
  useMyChangeRequests,
  useMyFamilies,
  useWithdrawMyChangeRequest,
} from '../hooks/use-employee-change-requests'
import type { Employee } from '../types/employee'
import type { EmployeeChangeRequest } from '../types/employee-change-request'
import { CHANGE_REQUEST_STATUS } from '../utils/employee-change-request-status'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { FormCard } from '@/shared/ui/form-card'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime } from '@/shared/utils/format-date'

interface SelfChangeRequestCardProps {
  employee: Employee
}

/** Đề nghị mới nhất — không phụ thuộc thứ tự backend trả (id tăng dần theo thời gian gửi). */
function pickLatest(items: readonly EmployeeChangeRequest[] | undefined) {
  if (!items || items.length === 0) return null
  return items.reduce((latest, item) => (item.id > latest.id ? item : latest))
}

/**
 * Thẻ "Đề nghị sửa hồ sơ" ở Trang cá nhân (duoc-CR-676, C6) — đứng ngay dưới nhóm Liên hệ.
 *
 * Nhóm LIÊN HỆ tự sửa áp ngay (bao-CR-508); còn thông tin cá nhân, ngân hàng, giấy tờ và hộ gia
 * đình thì nhân viên chỉ ĐỀ NGHỊ, phòng Nhân sự duyệt rồi mới vào hồ sơ. Mỗi lúc chỉ một đề nghị
 * đang chờ (backend trả 409 nếu gửi thêm) — nên nút gửi tắt kèm câu giải thích khi đang có một cái.
 */
export function SelfChangeRequestCard({ employee }: SelfChangeRequestCardProps) {
  const [open, setOpen] = useState(false)
  const requests = useMyChangeRequests(true)
  //  Nạp sẵn hộ gia đình ngay khi thẻ hiện: mở hộp ra là tab "Hộ gia đình" có dữ liệu luôn.
  const families = useMyFamilies(true)
  const withdraw = useWithdrawMyChangeRequest()
  const withdrawingRef = useRef(false)

  const latest = pickLatest(requests.data)
  const hasPending = latest?.status === CHANGE_REQUEST_STATUS.PENDING

  async function handleWithdraw(id: number) {
    if (withdrawingRef.current) return
    withdrawingRef.current = true
    try {
      const ok = await confirm({
        title: 'Rút đề nghị?',
        message: 'Phòng Nhân sự sẽ không duyệt đề nghị này nữa. Bạn có thể gửi đề nghị mới sau.',
        confirmLabel: 'Rút đề nghị',
      })
      if (ok) await withdraw.mutateAsync(id)
    } catch {
      //  http-client đã toast lỗi (vd 409 — đề nghị vừa được duyệt xong).
    } finally {
      withdrawingRef.current = false
    }
  }

  return (
    <FormCard
      title="Đề nghị sửa hồ sơ"
      icon={FilePen}
      iconClassName="text-muted-foreground"
      actions={
        <Button
          type="button"
          size="sm"
          variant="outline"
          disabled={hasPending || requests.isLoading}
          title={hasPending ? 'Đang có một đề nghị chờ duyệt' : undefined}
          onClick={() => setOpen(true)}
        >
          <FilePen className="size-4" />
          Đề nghị sửa thông tin
        </Button>
      }
    >
      <p className="mb-3 flex gap-2 rounded-lg bg-accent px-3 py-2 text-xs text-muted-foreground">
        <Info className="mt-0.5 size-3.5 shrink-0" />
        <span>
          Thông tin cá nhân, ngân hàng, giấy tờ và hộ gia đình: phòng Nhân sự duyệt rồi mới cập nhật
          vào hồ sơ.
          {hasPending && ' Bạn đang có một đề nghị chờ duyệt — rút nó ra nếu muốn gửi lại.'}
        </span>
      </p>

      {requests.isLoading ? (
        <Skeleton className="h-20 w-full" />
      ) : !latest ? (
        <p className="text-sm text-muted-foreground">Bạn chưa gửi đề nghị nào.</p>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex flex-wrap items-center gap-x-3 gap-y-1.5 text-sm">
            <EmployeeChangeRequestStatusBadge status={latest.status} />
            <span className="text-muted-foreground">Gửi lúc {formatDateTime(latest.created_at)}</span>
            {latest.decided_at && (
              <span className="text-muted-foreground">
                · Xử lý {formatDateTime(latest.decided_at)}
                {latest.decided_by_name && ` bởi ${latest.decided_by_name}`}
              </span>
            )}
            {hasPending && (
              <Button
                type="button"
                size="sm"
                variant="ghost"
                className="ml-auto"
                disabled={withdraw.isPending}
                onClick={() => void handleWithdraw(latest.id)}
              >
                {withdraw.isPending ? <Loader2 className="animate-spin" /> : <Undo2 />}
                Rút đề nghị
              </Button>
            )}
          </div>

          <ChangeRequestChangesList request={latest} />

          {latest.note && (
            <p className="text-sm">
              <span className="text-muted-foreground">Ghi chú của bạn: </span>
              {latest.note}
            </p>
          )}
          {latest.status === CHANGE_REQUEST_STATUS.REJECTED && latest.reject_reason && (
            <p role="note" className="rounded-md border border-destructive/40 bg-destructive/10 px-3 py-2 text-sm">
              <span className="font-medium text-destructive">Lý do từ chối: </span>
              {latest.reject_reason}
            </p>
          )}
        </div>
      )}

      <SelfChangeRequestDialog
        open={open}
        onOpenChange={setOpen}
        employee={employee}
        families={{
          data: families.data,
          isLoading: families.isLoading,
          //  Nạp hỏng thì tab "Hộ gia đình" khóa lại + nút thử lại (review M4), không bày bảng rỗng.
          isError: families.isError,
          retry: () => void families.refetch(),
        }}
      />
    </FormCard>
  )
}
