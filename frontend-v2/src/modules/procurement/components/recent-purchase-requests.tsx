import { Check, CornerUpLeft } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { ReasonConfirmDialog } from '@/shared/ui/reason-confirm-dialog'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import { formatMoney } from '@/shared/utils/format-money'
import type { RecentPurchaseRequest } from '../api/procurement-dashboard-api'
import { usePurchaseRequestAction } from '../hooks/use-purchase-request'
import { PR_STATUS_LABELS } from '../types/purchase-document'
import { StatusBadge } from './document-status-badge'

interface RecentPurchaseRequestsProps {
  rows: RecentPurchaseRequest[]
}

/**
 * Bảng "Yêu cầu mua gần đây" ở trang Tổng quan — duyệt / trả lại nhanh tại chỗ
 * khi có quyền `approve`.
 *
 * Không nhận `onRefresh`: `usePurchaseRequestAction` đã làm mất hiệu lực cả
 * nhánh `queryKeys.procurement`, mà số liệu trang này nằm đúng trong nhánh đó
 * (`['procurement', 'dashboard']`) nên bảng tự nạp lại. Gọi thêm `refetch` chỉ
 * tổ bắn hai lượt cùng một request.
 */
export function RecentPurchaseRequests({ rows }: RecentPurchaseRequestsProps) {
  const { can } = usePermission()
  const canApprove = can('purchase_request', 'approve')

  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Chưa có yêu cầu mua hàng nào.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <Table className="min-w-[850px]">
        <TableHeader>
          <TableRow>
            <TableHead className="w-36">Mã phiếu</TableHead>
            <TableHead className="min-w-56">Người yêu cầu / Nội dung</TableHead>
            <TableHead className="w-40">Bộ phận</TableHead>
            <TableHead className="w-28">Ngày</TableHead>
            <TableHead className="w-36 text-right">Giá trị</TableHead>
            <TableHead className="w-32">Trạng thái</TableHead>
            {canApprove && <TableHead className="w-28 text-center">Thao tác</TableHead>}
          </TableRow>
        </TableHeader>

        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-semibold text-sky-600 dark:text-sky-400">
                {row.code}
              </TableCell>
              <TableCell>
                <span className="block font-medium truncate">{row.requester}</span>
                <span
                  className="block truncate text-xs text-muted-foreground"
                  title={row.description}
                >
                  {row.description || '—'}
                </span>
              </TableCell>
              <TableCell>{row.department || '—'}</TableCell>
              <TableCell>{formatDate(row.date) || '—'}</TableCell>
              <TableCell className="text-right font-medium tabular-nums">
                {formatMoney(row.total)} đ
              </TableCell>
              <TableCell>
                <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
              </TableCell>
              {canApprove && (
                <TableCell className="text-center">
                  {row.status === 'submitted' ? (
                    <QuickActions id={row.id} code={row.code} />
                  ) : (
                    <span className="text-xs text-muted-foreground">—</span>
                  )}
                </TableCell>
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}

/**
 * Hai nút thao tác của MỘT dòng. Tách thành component riêng vì
 * `usePurchaseRequestAction` nhận `id` lúc dựng hook — không gọi được trong
 * vòng lặp của bảng.
 *
 * Không tự bắn toast lỗi: `httpClient` đã toast mọi lời gọi không phải GET, tự
 * thêm nữa là người dùng thấy hai thông báo chồng nhau. Câu báo thành công do
 * chính hook lo, dùng chung với màn chi tiết.
 */
function QuickActions({ id, code }: { id: number; code: string }) {
  const runAction = usePurchaseRequestAction(id)
  const [askReturn, setAskReturn] = useState(false)

  return (
    <div className="flex items-center justify-center gap-1.5">
      <ConfirmIconButton
        icon={Check}
        title="Duyệt nhanh"
        confirmTitle={`Duyệt phiếu ${code}?`}
        confirmDescription="Phiếu chuyển sang Đã duyệt và đi tiếp sang bước điều phối."
        confirmLabel="Duyệt"
        disabled={runAction.isPending}
        onConfirm={() => runAction.mutate({ action: 'approve' })}
      />

      {/* Nút này gọi `/reject`, mà backend đặt phiếu về `rejected` = "Bị trả
          lại" (người yêu cầu sửa rồi gửi lại được), KHÔNG phải "Đã từ chối"
          (`cancelled`, khóa hẳn). Nhãn phải nói đúng việc nó làm. */}
      <Button
        size="icon-sm"
        variant="ghost"
        title="Trả lại để sửa"
        aria-label="Trả lại để sửa"
        disabled={runAction.isPending}
        className="text-destructive hover:text-destructive"
        onClick={() => setAskReturn(true)}
      >
        <CornerUpLeft />
      </Button>

      <ReasonConfirmDialog
        open={askReturn}
        onOpenChange={setAskReturn}
        title={`Trả lại phiếu ${code}`}
        description="Phiếu chuyển sang Bị trả lại để người yêu cầu sửa và gửi duyệt lại. Lý do được gửi kèm thông báo cho họ."
        placeholder="Vì sao phiếu chưa duyệt được?"
        confirmText="Trả lại"
        destructive
        pending={runAction.isPending}
        onConfirm={(reason) => {
          setAskReturn(false)
          runAction.mutate({ action: 'reject', reason })
        }}
      />
    </div>
  )
}
