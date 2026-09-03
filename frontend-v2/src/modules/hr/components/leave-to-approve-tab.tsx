import { Check, Undo2, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { formatDateTime } from '@/shared/utils/format-date'
import {
  useLeaveApprovalDecision,
  useLeaveToApprove,
  type ApprovalDecision,
} from '../hooks/use-leave'
import type { LeaveInboxRow } from '../types/leave'
import { LeaveDecisionDialog } from './leave-decision-dialog'
import {
  codeColumn,
  dateColumns,
  employeeColumn,
  flowColumn,
  leaveTypeColumn,
  reasonColumn,
} from './leave-request-columns'

/**
 * Tab «CẦN TÔI DUYỆT» — hàng đợi việc, quyết được ngay trên dòng (CR-260).
 *
 * ⚠️ **Đơn chỉ hiện khi ĐÃ TỚI LƯỢT mình.** Người ở chặng 2 không thấy đơn đang
 * nằm ở chặng 1: thấy sớm thì họ bấm Duyệt rồi ăn câu "bạn không có việc nào
 * đang chờ ở phiếu này" — đúng luật nhưng vô nghĩa với thao tác vừa làm. Luật
 * lọc nằm ở backend (`task_service.my_tasks` chỉ lấy việc `TASK_PENDING`).
 *
 * ⚠️ **Không có cột Trạng thái.** Mọi dòng ở đây đều là «Chờ duyệt» — một cột
 * lặp đúng một giá trị chỉ ăn chỗ của cột Luồng duyệt, thứ thật sự nói phiếu
 * đang ở đâu.
 */
export function LeaveToApproveTab() {
  const navigate = useNavigate()
  const { data, isLoading, isError } = useLeaveToApprove()
  const decide = useLeaveApprovalDecision()

  //  Một ô trạng thái cho cả hộp thoại: tờ đơn đang hỏi + quyết định đang chọn.
  //  Tách hai ô thì lúc đóng hộp có một nhịp render mà đơn đã rỗng còn quyết
  //  định thì chưa — hộp nháy sang tiêu đề khác trước khi biến mất.
  const [asking, setAsking] = useState<{ row: LeaveInboxRow; decision: ApprovalDecision } | null>(
    null,
  )

  const columns = useMemo<DataTableColumn<LeaveInboxRow>[]>(
    () => [
      codeColumn(),
      employeeColumn(),
      leaveTypeColumn(),
      ...dateColumns(),
      flowColumn((row) => row.flow),
      {
        key: 'task_node',
        header: 'Việc của tôi',
        cell: (row) => (
          <div className="min-w-0">
            <span className="block truncate">
              {row.task.node_name || `Chặng ${row.task.node_seq}`}
            </span>
            {/*  Bấm THAY người khác phải nói ra TRƯỚC khi bấm, không phải sau:
                 chữ ký đi vào dấu vết mang cả hai tên. */}
            {row.task.on_behalf_of_name && (
              <span className="block truncate text-xs text-muted-foreground">
                Bấm thay {row.task.on_behalf_of_name}
              </span>
            )}
            {row.task.is_overdue && (
              <Badge variant="outline" className="mt-0.5 border-destructive/40 text-destructive">
                Quá hạn
              </Badge>
            )}
          </div>
        ),
        width: 170,
      },
      reasonColumn(),
      {
        key: 'actions',
        header: 'Thao tác',
        cell: (row) => (
          //  `stopPropagation`: dòng bảng có `onRowClick` mở trang chi tiết, nên
          //  không chặn thì bấm Duyệt vừa mở hộp thoại vừa điều hướng đi mất.
          <div
            className="flex items-center gap-1"
            onClick={(e) => e.stopPropagation()}
            role="presentation"
          >
            <Button size="sm" onClick={() => setAsking({ row, decision: 'approve' })}>
              <Check className="size-4" />
              Duyệt
            </Button>
            <Button
              size="sm"
              variant="outline"
              onClick={() => setAsking({ row, decision: 'return' })}
            >
              <Undo2 className="size-4" />
              Trả về
            </Button>
            <Button
              size="sm"
              variant="outline"
              className="text-destructive hover:text-destructive"
              onClick={() => setAsking({ row, decision: 'reject' })}
            >
              <X className="size-4" />
              Từ chối
            </Button>
          </div>
        ),
        width: 280,
        hideable: false,
      },
      {
        key: 'due_at',
        header: 'Hạn xử lý',
        cell: (row) =>
          row.task.due_at ? (
            <span className="tabular-nums">{formatDateTime(row.task.due_at)}</span>
          ) : (
            '—'
          ),
        width: 150,
        compactHidden: true,
      },
    ],
    [],
  )

  return (
    <>
      <DataTable
        fillHeight
        columns={columns}
        rows={data?.items}
        getRowId={(r) => r.id}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Không có đơn nào đang chờ bạn duyệt."
        storageKey="hr.leave-to-approve"
        onRowClick={(r) => navigate(appRoutes.hr.leaveRequestDetail(r.id))}
      />

      <LeaveDecisionDialog
        row={asking?.row ?? null}
        decision={asking?.decision ?? 'approve'}
        isPending={decide.isPending}
        onClose={() => setAsking(null)}
        onConfirm={(reason) => {
          if (!asking) return
          decide.mutate(
            {
              instanceId: asking.row.task.instance_id,
              decision: asking.decision,
              reason,
            },
            //  Đóng hộp trong `onSuccess`, KHÔNG đóng ngay lúc bấm: gọi hỏng
            //  (mất mạng, người khác vừa ký trước) mà hộp đã đóng thì người
            //  dùng chỉ thấy một dòng lỗi trôi qua và tưởng mình đã ký xong.
            { onSuccess: () => setAsking(null) },
          )
        }}
      />
    </>
  )
}
