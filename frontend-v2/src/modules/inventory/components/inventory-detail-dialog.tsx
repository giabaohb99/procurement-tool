import { SlidersHorizontal } from 'lucide-react'
import type { ReactNode } from 'react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { TONE_CLASS } from '@/shared/ui/status-tone'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { formatMoney, formatQuantity, formatUnitPrice } from '@/shared/utils/format-money'
import { useInventoryMoves } from '../hooks/use-inventory'
import { moveAmount, moveKindLabel, type InventoryItem } from '../types/inventory'

interface InventoryDetailDialogProps {
  /** `null` = đóng. Mở bằng cách truyền dòng tồn được bấm. */
  item: InventoryItem | null
  onOpenChange: (open: boolean) => void
  companyName: string
  /** Bỏ trống = người dùng không có quyền `inventory.write`, ẩn luôn nút điều chỉnh. */
  onAdjust?: () => void
}

/**
 * Chi tiết một dòng tồn + sổ phát sinh đã dẫn tới số dư đó.
 *
 * Khác v1 một chỗ: v1 có link "Chi tiết" sang trang sản phẩm. v2 chưa dời màn
 * Danh mục sản phẩm nên link sẽ dẫn vào trang trống — gắn lại khi màn đó lên.
 */
export function InventoryDetailDialog({
  item,
  onOpenChange,
  companyName,
  onAdjust,
}: InventoryDetailDialogProps) {
  const { data, isLoading } = useInventoryMoves(item)
  const moves = data?.items ?? []

  return (
    <Dialog open={!!item} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90vh] w-[96vw] overflow-y-auto sm:max-w-[900px]">
        <DialogHeader>
          <DialogTitle>Chi tiết tồn kho & lịch sử biến động</DialogTitle>
          <DialogDescription>
            Số dư dưới đây do hệ thống tính lại từ sổ phát sinh, không ai gõ tay trực tiếp.
          </DialogDescription>
        </DialogHeader>

        {item && (
          <>
            <div className="grid gap-4 rounded-lg border bg-muted/40 p-4 sm:grid-cols-2 lg:grid-cols-4">
              <Field label="Sản phẩm">
                <span className="font-semibold">{item.product_code}</span>
                <span className="block text-xs text-muted-foreground">{item.product_name}</span>
              </Field>
              <Field label="Đơn vị tính">{item.unit || '—'}</Field>
              <Field label="Công ty">{companyName}</Field>
              <Field label="Kho">{item.warehouse_code || '—'}</Field>
              <Field label="Tồn hiện tại">
                <span
                  className={cn(
                    'text-lg font-semibold tabular-nums',
                    item.qty < 0 && 'text-destructive',
                  )}
                >
                  {formatQuantity(item.qty)}
                </span>
              </Field>
              <Field label="Đơn giá bình quân">
                <span className="tabular-nums">{formatUnitPrice(item.avg_cost)} đ</span>
              </Field>
              <Field label="Giá trị tồn">
                <span className="font-semibold tabular-nums">{formatMoney(item.value)} đ</span>
              </Field>
            </div>

            <h3 className="text-sm font-semibold text-navy dark:text-foreground">
              Lịch sử giao dịch & cập nhật tồn kho
            </h3>

            {isLoading ? (
              <Skeleton className="h-40 w-full" />
            ) : (
              <div className="max-h-80 overflow-auto rounded-lg border">
                <Table>
                  <TableHeader className="bg-muted">
                    <TableRow>
                      <TableHead className="w-36">Thời gian</TableHead>
                      <TableHead className="w-44">Loại giao dịch</TableHead>
                      <TableHead className="w-28 text-right">Thay đổi</TableHead>
                      <TableHead className="w-32 text-right">Đơn giá</TableHead>
                      <TableHead className="w-36 text-right">Thành tiền</TableHead>
                      <TableHead className="w-40">Người thực hiện</TableHead>
                      <TableHead>Ghi chú / Lý do</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {moves.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={7} className="h-20 text-center text-muted-foreground">
                          Chưa có phát sinh kho nào cho sản phẩm này.
                        </TableCell>
                      </TableRow>
                    )}
                    {moves.map((move) => (
                      <TableRow key={move.id}>
                        <TableCell className="whitespace-nowrap">
                          {formatDateTime(move.at) || '—'}
                        </TableCell>
                        <TableCell>
                          <Badge
                            variant="secondary"
                            className={cn(
                              'border-0',
                              move.ref_type === 'gr' ? TONE_CLASS.done : TONE_CLASS.progress,
                            )}
                          >
                            {moveKindLabel(move.ref_type)}
                          </Badge>
                        </TableCell>
                        <TableCell
                          className={cn(
                            'text-right font-semibold tabular-nums',
                            move.qty < 0 ? 'text-destructive' : 'text-success',
                          )}
                        >
                          {move.qty >= 0 ? '+' : ''}
                          {formatQuantity(move.qty)}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {move.unit_price > 0 ? `${formatUnitPrice(move.unit_price)} đ` : '—'}
                        </TableCell>
                        <TableCell className="text-right tabular-nums">
                          {moveAmount(move) !== 0 ? `${formatMoney(moveAmount(move))} đ` : '—'}
                        </TableCell>
                        <TableCell>{move.operator_name || '—'}</TableCell>
                        <TableCell className="whitespace-normal">{move.note || '—'}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            )}
          </>
        )}

        <DialogFooter>
          {onAdjust && (
            <Button onClick={onAdjust}>
              <SlidersHorizontal />
              Điều chỉnh tồn kho này
            </Button>
          )}
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            Đóng
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <span className="block text-xs text-muted-foreground">{label}</span>
      <div className="mt-0.5 text-sm">{children}</div>
    </div>
  )
}
