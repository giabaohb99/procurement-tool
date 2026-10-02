// Nút «Xuất Excel» của mục «Thuốc BVTV» — hai lựa chọn: trang đang xem (kèm đúng bộ lọc /
// phân trang màn đang dùng để gọi `GET /pesticides`) hoặc cả danh mục. Quyền `customs_price.export`
// — giống nút Xuất Excel của thẻ Danh sách, KHÁC quyền sửa danh mục `customs_pesticide` của nút
// «Nạp danh mục» cạnh nó. `useSingleFlight` chặn bấm dồn (xem ghi chú ở hook đó).
import { useState } from 'react'
import { FileSpreadsheet, Loader2 } from 'lucide-react'
import { toast } from 'sonner'

import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'

import { exportCustomsPesticides } from '../../api/customs-pesticide-api'

type PesticideExportScope = 'page' | 'all'

interface CustomsPesticideExportMenuProps {
  /** Bộ lọc ĐÃ ÁP dựng sẵn bằng `buildPesticideParams` — KHÔNG kèm `page`/`page_size`. */
  filterParams: Record<string, string>
  page: number
  pageSize: number
  /** Số dòng của trang đang xem — hiện trong nhãn mục menu. */
  pageRowCount: number
  /** Chưa có thuốc nào trong danh mục (lọc hay không) → khóa cả nút, xuất tệp trống vô nghĩa. */
  disabled?: boolean
}

export function CustomsPesticideExportMenu({
  filterParams,
  page,
  pageSize,
  pageRowCount,
  disabled,
}: CustomsPesticideExportMenuProps) {
  const [exporting, setExporting] = useState(false)
  const singleFlight = useSingleFlight()

  function runExport(scope: PesticideExportScope) {
    void singleFlight(async () => {
      setExporting(true)
      try {
        const params: Record<string, string> =
          scope === 'all'
            ? { scope }
            : { scope, ...filterParams, page: String(page), page_size: String(pageSize) }
        await exportCustomsPesticides(params)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })
  }

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="outline" disabled={disabled || exporting}>
          {exporting ? (
            <Loader2 className="size-4 animate-spin" />
          ) : (
            <FileSpreadsheet className="size-4" />
          )}
          {exporting ? 'Đang xuất…' : 'Xuất Excel'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuItem onSelect={() => runExport('page')}>
          <span className="flex min-w-0 flex-col gap-0.5">
            <span>Trang hiện tại ({pageRowCount} dòng)</span>
            <span className="text-xs font-normal text-muted-foreground">
              Chỉ các dòng đang xem theo bộ lọc hiện tại. Nạp lại tệp này qua «Nạp danh mục» chỉ
              cập nhật đúng các thuốc có trong tệp, phần còn lại giữ nguyên.
            </span>
          </span>
        </DropdownMenuItem>
        <DropdownMenuItem onSelect={() => runExport('all')}>
          <span className="flex min-w-0 flex-col gap-0.5">
            <span>Toàn bộ danh mục</span>
            <span className="text-xs font-normal text-muted-foreground">
              Xuất hết, không theo bộ lọc. Nạp lại tệp này qua «Nạp danh mục» sẽ thay toàn bộ danh
              mục; thuốc thêm tay không có trong lần nạp (vẫn giữ trên hệ thống).
            </span>
          </span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
