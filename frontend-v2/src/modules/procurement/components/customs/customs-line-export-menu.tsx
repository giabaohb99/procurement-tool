// bao-CR-718 — nút "Xuất dữ liệu" của thẻ Danh sách (Tra cứu thị trường), thành menu ba mục:
//   (a) Xuất ngay — hành vi cũ, tải thẳng tối đa 50.000 dòng (`GET /lines/export`);
//   (b) Xuất toàn bộ theo bộ lọc — tạo LÔ chạy nền chia nhiều tệp, có hộp xác nhận nêu bộ lọc, số dòng,
//       số tệp dự kiến; xong chuyển sang màn chi tiết lô;
//   (c) Lô xuất của tôi — màn danh sách lô.
// Quyền `customs_price.export` do trang gác (chỉ vẽ menu khi `canExport`). `useSingleFlight` chặn bấm dồn —
// với (b) bấm đúp là hai lô, backend chặn lô thứ hai bằng 409 nhưng người dùng ăn một toast đỏ vô cớ.
import { Download, FileStack, ListChecks, Loader2 } from 'lucide-react'
import { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { appRoutes } from '@/shared/constants/app-routes'
import { fromHere } from '@/shared/hooks/use-back-target'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'

import { exportCustomsLines } from '../../api/customs-api'
import { useCreateCustomsExportBatch } from '../../hooks/use-customs'
import {
  buildFullExportConfirmMessage,
  CUSTOMS_EXPORT_ROWS_PER_FILE,
  estimateExportFileCount,
} from '../../utils/customs-export'

interface CustomsLineExportMenuProps {
  /** Bộ lọc ĐÃ ÁP dựng bằng `buildCustomsParams` — KHÔNG kèm `page`/`page_size`. */
  filterParams: Record<string, string>
  /** Câu mô tả bộ lọc cho hộp xác nhận (`describeCustomsFilters`). */
  filterSummary: string
  /** Tổng dòng khớp bộ lọc (`lines.data.total`); chưa về thì `undefined`. */
  totalRows: number | undefined
}

function isConflict(error: unknown): boolean {
  return (error as { response?: { status?: number } } | null)?.response?.status === 409
}

export function CustomsLineExportMenu({ filterParams, filterSummary, totalRows }: CustomsLineExportMenuProps) {
  const navigate = useNavigate()
  const location = useLocation()
  //  Nút lùi của màn lô quay về ĐÚNG chỗ đang đứng (bộ lọc trên URL), không về Tra cứu trống trơn.
  const backState = fromHere(location)
  const [exporting, setExporting] = useState(false)
  const singleFlight = useSingleFlight()
  const createBatch = useCreateCustomsExportBatch()
  const total = totalRows ?? 0
  const hasRows = total > 0
  const busy = exporting || createBatch.isPending

  function exportNow() {
    trackUiAction(UI_ACTION_CODE.EXPORT_EXCEL)
    void singleFlight(async () => {
      setExporting(true)
      try {
        await exportCustomsLines(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })
  }

  function exportAll() {
    void singleFlight(async () => {
      const ok = await confirm({
        title: 'Xuất toàn bộ theo bộ lọc',
        message: buildFullExportConfirmMessage(total, filterSummary),
        confirmLabel: 'Đồng ý',
        tone: 'default',
      })
      if (!ok) return
      trackUiAction(UI_ACTION_CODE.EXPORT_EXCEL)
      try {
        const { batch, message } = await createBatch.mutateAsync(filterParams)
        toast.success(message || `Đã tạo lô xuất #${batch.id}`)
        navigate(appRoutes.procurement.customsExportDetail(batch.id), { state: backState })
      } catch (error) {
        //  409 = đang có một lô chờ / chạy của chính người này — chỉ đường sang lô đó.
        if (isConflict(error)) {
          toast.error(extractErrorMessage(error), {
            action: {
              label: 'Lô xuất của tôi',
              onClick: () => navigate(appRoutes.procurement.customsExports, { state: backState }),
            },
          })
          return
        }
        toast.error(extractErrorMessage(error))
      }
    })
  }

  const capLabel = CUSTOMS_EXPORT_ROWS_PER_FILE.toLocaleString('vi-VN')

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button type="button" variant="outline" disabled={busy}>
          {busy ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}
          {busy ? 'Đang xuất…' : 'Xuất dữ liệu'}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-80">
        <DropdownMenuItem
          disabled={!hasRows || total > CUSTOMS_EXPORT_ROWS_PER_FILE}
          onSelect={exportNow}
        >
          <Download className="size-4" />
          <span className="flex min-w-0 flex-col gap-0.5">
            <span>Xuất ngay (tối đa {capLabel} dòng)</span>
            <span className="text-xs font-normal text-muted-foreground">
              {total > CUSTOMS_EXPORT_ROWS_PER_FILE
                ? `Bộ lọc đang có ${total.toLocaleString('vi-VN')} dòng — quá trần, dùng mục xuất toàn bộ bên dưới.`
                : 'Tải về ngay một tệp Excel đúng các dòng đang lọc.'}
            </span>
          </span>
        </DropdownMenuItem>
        <DropdownMenuItem disabled={!hasRows} onSelect={exportAll}>
          <FileStack className="size-4" />
          <span className="flex min-w-0 flex-col gap-0.5">
            <span>Xuất toàn bộ theo bộ lọc (chạy nền)</span>
            <span className="text-xs font-normal text-muted-foreground">
              {hasRows
                ? `${total.toLocaleString('vi-VN')} dòng, dự kiến ${estimateExportFileCount(total)} tệp — báo chuông khi xong.`
                : 'Bộ lọc chưa có dòng nào để xuất.'}
            </span>
          </span>
        </DropdownMenuItem>
        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => navigate(appRoutes.procurement.customsExports, { state: backState })}>
          <ListChecks className="size-4" />
          Lô xuất của tôi
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
