import { useEffect, useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { Button } from '@/shared/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Input } from '@/shared/ui/input'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/shared/ui/table'
import { formatDate } from '@/shared/utils/format-date'
import {
  formatMoney,
  formatQuantity,
  formatUnitPrice,
} from '@/shared/utils/format-money'
import type { PurchaseHistoryRow } from '../api/purchase-request-support-api'
import { useProductPurchaseHistory } from '../hooks/use-purchase-request-support'

const PAGE_SIZE = 20

interface PurchaseRequestHistoryDialogProps {
  open: boolean
  productCode: string
  productName: string
  onOpenChange: (open: boolean) => void
  onPick: (row: PurchaseHistoryRow) => void
}

/**
 * Các lần mua đã hoàn thành của đúng mã hàng. Chọn một dòng chỉ cập nhật bản nháp
 * hiện tại; người dùng vẫn phải bấm Lưu phiếu để ghi nhận.
 */
export function PurchaseRequestHistoryDialog({
  open,
  productCode,
  productName,
  onOpenChange,
  onPick,
}: PurchaseRequestHistoryDialogProps) {
  const [page, setPage] = useState(1)
  const [search, setSearch] = useState('')
  const debouncedSearch = useDebouncedValue(search, 300)
  const history = useProductPurchaseHistory(
    productCode,
    page,
    PAGE_SIZE,
    debouncedSearch,
    open,
  )

  useEffect(() => {
    setPage(1)
  }, [debouncedSearch, productCode])

  useEffect(() => {
    if (!open) {
      setPage(1)
      setSearch('')
    }
  }, [open])

  const rows = history.data?.items ?? []
  const total = history.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const start = total ? (page - 1) * PAGE_SIZE + 1 : 0
  const end = Math.min(page * PAGE_SIZE, total)

  function pick(row: PurchaseHistoryRow) {
    onPick(row)
    onOpenChange(false)
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="flex max-h-[92dvh] flex-col gap-0 overflow-hidden p-0 sm:max-w-6xl">
        <DialogHeader className="border-b px-5 py-4 pr-12">
          <DialogTitle>Lịch sử mua hàng gần nhất</DialogTitle>
          <DialogDescription className="truncate">
            {productCode}
            {productName ? ` · ${productName}` : ''} · {total} lần mua đã hoàn thành
          </DialogDescription>
        </DialogHeader>

        <div className="px-5 pt-4">
          <Input
            value={search}
            onChange={(event) => setSearch(event.target.value)}
            autoFocus
            placeholder="Tìm theo Mã PO / Nhà cung cấp / Công ty..."
          />
        </div>

        <div className="min-h-0 flex-1 overflow-auto px-5 py-4">
          <div className="overflow-hidden rounded-md border">
            <Table className="min-w-[940px] [&_td]:border-r [&_td:last-child]:border-r-0 [&_th]:border-r [&_th:last-child]:border-r-0">
              <TableHeader className="bg-muted">
                <TableRow>
                  <TableHead>Ngày đặt</TableHead>
                  <TableHead>Mã PO</TableHead>
                  <TableHead>Nhà cung cấp</TableHead>
                  <TableHead>ĐVT</TableHead>
                  <TableHead className="text-right">SL đặt</TableHead>
                  <TableHead className="text-right">Đơn giá</TableHead>
                  <TableHead className="text-right">VAT%</TableHead>
                  <TableHead className="text-right">Thành tiền</TableHead>
                  <TableHead>Công ty</TableHead>
                  <TableHead className="w-28 text-center">Chọn</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow
                    key={row.id}
                    className="cursor-pointer"
                    onClick={() => pick(row)}
                  >
                    <TableCell className="whitespace-nowrap">
                      {formatDate(row.order_date) || row.order_date || '—'}
                    </TableCell>
                    <TableCell>
                      {row.po_code || (
                        <span className="text-xs text-muted-foreground">Dữ liệu cũ</span>
                      )}
                    </TableCell>
                    <TableCell>{row.supplier_name || row.supplier_code || '—'}</TableCell>
                    <TableCell>{row.unit || '—'}</TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatQuantity(row.qty_order)}
                    </TableCell>
                    <TableCell className="text-right font-medium tabular-nums">
                      {formatUnitPrice(row.price)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatQuantity(row.vat)}
                    </TableCell>
                    <TableCell className="text-right tabular-nums">
                      {formatMoney(row.amount)}
                    </TableCell>
                    <TableCell>{row.company_name || '—'}</TableCell>
                    <TableCell className="text-center">
                      <Button
                        type="button"
                        variant="outline"
                        size="xs"
                        onClick={(event) => {
                          event.stopPropagation()
                          pick(row)
                        }}
                      >
                        Dùng giá này
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}

                {!rows.length && (
                  <TableRow>
                    <TableCell colSpan={10} className="h-24 text-center text-muted-foreground">
                      {history.isLoading ? (
                        <span className="inline-flex items-center gap-2">
                          <Loader2 className="size-4 animate-spin" /> Đang tải...
                        </span>
                      ) : history.isError ? (
                        'Không tải được lịch sử mua hàng.'
                      ) : debouncedSearch ? (
                        'Không có kết quả khớp từ khóa.'
                      ) : (
                        'Mã hàng này chưa có lịch sử mua hàng.'
                      )}
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </div>
        </div>

        <div className="border-t px-5 py-3">
          <div className="flex items-center justify-between gap-4 text-sm">
            <span className="text-muted-foreground">
              Hiển thị {start}–{end} / {total}
            </span>
            <div className="flex items-center gap-2">
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                aria-label="Trang trước"
                disabled={page <= 1 || history.isFetching}
                onClick={() => setPage((current) => Math.max(1, current - 1))}
              >
                <ChevronLeft />
              </Button>
              <span className="min-w-20 text-center tabular-nums">
                Trang {page}/{totalPages}
              </span>
              <Button
                type="button"
                variant="outline"
                size="icon-sm"
                aria-label="Trang sau"
                disabled={page >= totalPages || history.isFetching}
                onClick={() => setPage((current) => Math.min(totalPages, current + 1))}
              >
                <ChevronRight />
              </Button>
            </div>
          </div>
          <p className="mt-2 text-xs text-muted-foreground">
            Chọn một dòng để điền ĐVT, SL, đơn giá, VAT, phân loại, kho nhận và ghi chú
            tương thích. Phiếu chưa được lưu — bấm Lưu để ghi nhận.
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
