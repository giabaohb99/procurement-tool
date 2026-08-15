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
import { PR_STATUS_LABELS } from '../types/purchase-document'
import { StatusBadge } from './document-status-badge'

/** Bảng "Yêu cầu mua gần đây" ở trang Tổng quan — chỉ đọc, 8 phiếu mới nhất. */
export function RecentPurchaseRequests({ rows }: { rows: RecentPurchaseRequest[] }) {
  if (rows.length === 0) {
    return (
      <p className="py-8 text-center text-sm text-muted-foreground">
        Chưa có yêu cầu mua hàng nào.
      </p>
    )
  }

  return (
    <div className="overflow-x-auto">
      <Table className="min-w-[820px]">
        <TableHeader>
          <TableRow>
            <TableHead className="w-40">Mã phiếu</TableHead>
            <TableHead className="min-w-64">Người yêu cầu / Nội dung</TableHead>
            <TableHead className="w-44">Bộ phận</TableHead>
            <TableHead className="w-32">Ngày</TableHead>
            <TableHead className="w-40 text-right">Giá trị</TableHead>
            <TableHead className="w-36">Trạng thái</TableHead>
          </TableRow>
        </TableHeader>

        <TableBody>
          {rows.map((row) => (
            <TableRow key={row.id}>
              <TableCell className="font-medium">{row.code}</TableCell>
              <TableCell>
                <span className="block truncate">{row.requester}</span>
                <span
                  className="block truncate text-xs text-muted-foreground"
                  title={row.description}
                >
                  {row.description || '—'}
                </span>
              </TableCell>
              <TableCell>{row.department || '—'}</TableCell>
              <TableCell>{formatDate(row.date) || '—'}</TableCell>
              <TableCell className="text-right tabular-nums">
                {formatMoney(row.total)} đ
              </TableCell>
              <TableCell>
                <StatusBadge status={row.status} labels={PR_STATUS_LABELS} />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </div>
  )
}
