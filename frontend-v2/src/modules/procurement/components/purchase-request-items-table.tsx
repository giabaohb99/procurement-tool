import { Plus, Trash2 } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Input } from '@/shared/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import {
  formatMoney,
  formatQuantity,
  formatUnitPrice,
} from '@/shared/utils/format-money'
import type { PurchaseRequestItem } from '../types/purchase-request-detail'

interface ItemsTableProps {
  items: PurchaseRequestItem[]
  /** Bật chế độ sửa: hiện ô nhập + nút thêm/xóa dòng. */
  editing: boolean
  onChange: (items: PurchaseRequestItem[]) => void
  /** SL đã đặt theo MÃ HÀNG, gộp mọi ĐMH sinh từ phiếu (chỉ đọc). */
  orderedByCode?: Record<string, number>
}

/** Dòng trống khi bấm "Thêm dòng". */
const EMPTY_ITEM: PurchaseRequestItem = {
  product_code: '',
  product_name: '',
  item_group: '',
  group_desc: '',
  qty: 0,
  unit: '',
  price: 0,
  vat_pct: 8,
  amount: 0,
  warehouse: '',
  required_date: '',
  assignee: '',
  expected_date: '',
  line_status: 'Chưa đặt hàng',
  progress_note: '',
  note: '',
  qty_ordered: 0,
  qty_received: 0,
  product_id: 0,
  product_thumbnail_url: '',
}

/**
 * Bảng dòng hàng của phiếu YCMH.
 *
 * Thành tiền do BACKEND tính (`amount`), ở đây chỉ tính tạm để người nhập thấy
 * ngay trong lúc gõ — lưu xong sẽ lấy lại số của server.
 */
export function PurchaseRequestItemsTable({
  items,
  editing,
  onChange,
  orderedByCode,
}: ItemsTableProps) {
  function patch(index: number, changes: Partial<PurchaseRequestItem>) {
    onChange(items.map((item, i) => (i === index ? { ...item, ...changes } : item)))
  }

  const lineTotal = (item: PurchaseRequestItem) =>
    editing ? item.qty * item.price * (1 + (item.vat_pct || 0) / 100) : item.amount

  return (
    <div className="space-y-3">
      <div className="overflow-x-auto rounded-lg border">
        <Table className="min-w-[1500px]">
          <TableHeader className="bg-muted">
            <TableRow>
              <TableHead className="w-10 text-center">No.</TableHead>
              <TableHead className="w-44">Mã hàng *</TableHead>
              <TableHead className="min-w-60">Tên sản phẩm *</TableHead>
              <TableHead className="w-36">Kho nhận</TableHead>
              <TableHead className="w-36">Phân loại</TableHead>
              <TableHead className="w-20">ĐVT</TableHead>
              <TableHead className="w-20 text-right">SL</TableHead>
              <TableHead className="w-28 text-right">Đơn giá</TableHead>
              <TableHead className="w-16 text-right" title="% VAT theo dòng">
                VAT%
              </TableHead>
              <TableHead className="w-32 text-right" title="Thành tiền gồm VAT">
                Thành tiền
              </TableHead>
              <TableHead className="w-36 text-center">Trạng thái</TableHead>
              <TableHead
                className="w-28 text-center"
                title="Tổng SL đã nhận / đã đặt, đồng bộ từ Đơn mua hàng"
              >
                Tiến độ
                <span className="block text-[10.5px] font-normal text-muted-foreground">
                  nhận / đặt
                </span>
              </TableHead>
              <TableHead className="w-32 text-center">
                TG dự kiến
                <span className="block text-[10.5px] font-normal text-muted-foreground">
                  có hàng
                </span>
              </TableHead>
              <TableHead className="w-40">NSTM phụ trách</TableHead>
              {editing && <TableHead className="w-12 text-center">Thao tác</TableHead>}
            </TableRow>
          </TableHeader>

          <TableBody>
            {items.length === 0 && (
              <TableRow>
                <TableCell colSpan={15} className="py-10 text-center text-muted-foreground">
                  Phiếu chưa có dòng hàng nào.
                </TableCell>
              </TableRow>
            )}

            {items.map((item, index) => (
              <TableRow
                key={item.id ?? `new-${index}`}
                // Dòng đã hủy vẫn phải thấy được nhưng không nên tranh sự chú ý.
                className={cn(item.line_status === 'Hủy đơn' && 'opacity-60')}
              >
                <TableCell className="text-center text-muted-foreground">
                  {index + 1}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <Input
                      value={item.product_code}
                      onChange={(e) => patch(index, { product_code: e.target.value })}
                      placeholder="Mã hàng"
                    />
                  ) : (
                    item.product_code || '—'
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <Input
                      value={item.product_name}
                      onChange={(e) => patch(index, { product_name: e.target.value })}
                      placeholder="Tên hàng"
                    />
                  ) : (
                    <span className="font-medium">{item.product_name}</span>
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <Input
                      value={item.warehouse}
                      onChange={(e) => patch(index, { warehouse: e.target.value })}
                    />
                  ) : (
                    item.warehouse || '—'
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <Input
                      value={item.item_group}
                      onChange={(e) => patch(index, { item_group: e.target.value })}
                    />
                  ) : (
                    item.item_group || '—'
                  )}
                </TableCell>

                <TableCell>
                  {editing ? (
                    <Input
                      value={item.unit}
                      onChange={(e) => patch(index, { unit: e.target.value })}
                    />
                  ) : (
                    item.unit || '—'
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Input
                      className="text-right"
                      type="number"
                      min={0}
                      value={item.qty || ''}
                      onChange={(e) => patch(index, { qty: Number(e.target.value) })}
                    />
                  ) : (
                    <span className="tabular-nums">{formatQuantity(item.qty)}</span>
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Input
                      className="text-right"
                      type="number"
                      min={0}
                      // Đơn giá cho tới 4 số lẻ (migration d4b9e7c1a305).
                      step="0.0001"
                      value={item.price || ''}
                      onChange={(e) => patch(index, { price: Number(e.target.value) })}
                    />
                  ) : (
                    <span className="tabular-nums">{formatUnitPrice(item.price)}</span>
                  )}
                </TableCell>

                <TableCell className="text-right">
                  {editing ? (
                    <Input
                      className="text-right"
                      type="number"
                      min={0}
                      value={item.vat_pct || 0}
                      onChange={(e) => patch(index, { vat_pct: Number(e.target.value) })}
                    />
                  ) : (
                    <span className="tabular-nums">{item.vat_pct || 0}</span>
                  )}
                </TableCell>

                <TableCell className="text-right font-medium tabular-nums">
                  {formatMoney(lineTotal(item))}
                </TableCell>

                <TableCell className="text-center">
                  <Badge variant="outline">{item.line_status || '—'}</Badge>
                </TableCell>

                <TableCell className="text-center tabular-nums">
                  {formatQuantity(item.qty_received)} /{' '}
                  {formatQuantity(orderedByCode?.[item.product_code] ?? item.qty_ordered)}
                </TableCell>

                <TableCell className="text-center">
                  {formatDate(item.expected_date) || '—'}
                </TableCell>

                <TableCell>{item.assignee || '—'}</TableCell>

                {editing && (
                  <TableCell>
                    <Button
                      variant="ghost"
                      size="icon-sm"
                      className="text-destructive hover:text-destructive"
                      title="Xóa dòng"
                      onClick={() => onChange(items.filter((_, i) => i !== index))}
                    >
                      <Trash2 />
                    </Button>
                  </TableCell>
                )}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>

      {editing && (
        <Button variant="outline" onClick={() => onChange([...items, { ...EMPTY_ITEM }])}>
          <Plus />
          Thêm dòng
        </Button>
      )}
    </div>
  )
}
