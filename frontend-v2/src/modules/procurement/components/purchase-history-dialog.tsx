import { useState } from 'react'
import { ChevronLeft, ChevronRight, Loader2 } from 'lucide-react'

import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
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

interface PurchaseHistoryDialogProps {
  open: boolean
  productCode: string
  productName: string
  /**
   * Chỉ xem, không điền được giá.
   *
   * Dùng cho chứng từ đang khóa sửa — mà đơn CHỜ DUYỆT lại đúng là lúc người
   * duyệt cần đối chiếu giá cũ nhất, nên vẫn phải mở được. Chỉ bỏ đường "Dùng
   * giá này": điền vào đơn đang trình duyệt là đổi nội dung ngay dưới tay người
   * duyệt, mà backend cũng sẽ chặn lượt lưu đó.
   */
  readOnly?: boolean
  onOpenChange: (open: boolean) => void
  onPick: (row: PurchaseHistoryRow) => void
}

/**
 * Các lần mua đã hoàn thành của đúng mã hàng — dùng chung cho YCMH và ĐMH.
 *
 * Chọn một dòng chỉ cập nhật bản nháp hiện tại; người dùng vẫn phải bấm Lưu
 * phiếu để ghi nhận. KHÔNG lọc theo NCC của chứng từ đang lập: mục đích chính
 * của màn này là so giá giữa các NCC.
 */
export function PurchaseHistoryDialog({
  open,
  productCode,
  productName,
  readOnly = false,
  onOpenChange,
  onPick,
}: PurchaseHistoryDialogProps) {
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

  // Gọi hook ra biến riêng: `||` sẽ short-circuit, làm hook thứ hai không chạy.
  const searchChanged = useHasChanged(debouncedSearch)
  const productChanged = useHasChanged(productCode)
  const openChanged = useHasChanged(open)

  // Đổi từ khóa / đổi sản phẩm -> xem lại từ trang đầu.
  if (searchChanged || productChanged) setPage(1)

  // Đóng hộp thoại -> trả về trạng thái ban đầu cho lần mở sau.
  if (openChanged && !open) {
    setPage(1)
    setSearch('')
  }

  const rows = history.data?.items ?? []
  const total = history.data?.total ?? 0
  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE))
  const start = total ? (page - 1) * PAGE_SIZE + 1 : 0
  const end = Math.min(page * PAGE_SIZE, total)
  const columnCount = readOnly ? 9 : 10

  function pick(row: PurchaseHistoryRow) {
    if (readOnly) return
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
                  {!readOnly && <TableHead className="w-28 text-center">Chọn</TableHead>}
                </TableRow>
              </TableHeader>
              <TableBody>
                {rows.map((row) => (
                  <TableRow
                    key={row.id}
                    className={readOnly ? undefined : 'cursor-pointer'}
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
                    {!readOnly && (
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
                    )}
                  </TableRow>
                ))}

                {!rows.length && (
                  <TableRow>
                    <TableCell
                      colSpan={columnCount}
                      className="h-24 text-center text-muted-foreground"
                    >
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
            {readOnly
              ? 'Chỉ xem để tham khảo — chứng từ đang khóa sửa nên không điền giá từ đây được.'
              : 'Chọn một dòng để điền ĐVT, SL, đơn giá, VAT, phân loại, kho nhận và ghi chú tương thích. Phiếu chưa được lưu — bấm Lưu để ghi nhận.'}
          </p>
        </div>
      </DialogContent>
    </Dialog>
  )
}
