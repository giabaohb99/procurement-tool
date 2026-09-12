import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileSpreadsheet, Printer, Search } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { CollapsibleNote } from '@/shared/ui/collapsible-note'
import { DatePicker } from '@/shared/ui/date-picker'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { purchaseReportApi } from '../api/purchase-report-api'
import { useImportLandedCost } from '../hooks/use-purchase-report'
import {
  LANDED_COST_TABLE_STYLES,
  LandedCostItemTable,
  LandedCostPivotTable,
  LandedCostWarnings,
} from './import-landed-cost-tables'
import {
  buildLandedCostParams,
  LANDED_COST_VIEWS,
  type LandedCostFilter,
  type LandedCostView,
} from '../types/import-landed-cost'

interface ReportImportLandedCostTabProps {
  companyId?: string
}

function defaultFilter(): LandedCostFilter {
  const year = new Date().getFullYear()
  return { codes: '', date_from: `${year}-01-01`, date_to: `${year}-12-31` }
}

/**
 * Tab GIÁ VỐN NHẬP KHẨU của Báo cáo mua hàng (bao-CR-357, dời từ bản v1).
 *
 * Khác các tab còn lại, tab này có nút "Xem" chứ không tự gọi lại mỗi lần đổi ô
 * lọc: ô mã đơn là ô GÕ TAY, tự gọi thì mỗi ký tự một lần quét DB. Đổi công ty ở
 * thanh lọc chung thì vẫn tải lại ngay — đó là bộ lọc của cả trang.
 */
export function ReportImportLandedCostTab({ companyId }: ReportImportLandedCostTabProps) {
  const { can } = usePermission()
  const [draft, setDraft] = useState<LandedCostFilter>(defaultFilter)
  const [applied, setApplied] = useState<LandedCostFilter>(defaultFilter)
  const [view, setView] = useState<LandedCostView>('orders')

  const params = useMemo(() => buildLandedCostParams(applied, companyId), [applied, companyId])
  const { data, isLoading, isError } = useImportLandedCost(params)

  //  Gõ mã đơn thì khoảng ngày mất tác dụng — khóa hai ô ngày lại cho khỏi hiểu
  //  nhầm là đang lọc giao của cả hai điều kiện.
  const byCodes = draft.codes.trim().length > 0
  const hasData = (data?.orders?.length ?? 0) > 0

  const printQuery = useMemo(() => {
    const search = new URLSearchParams()
    for (const [name, value] of Object.entries(params)) {
      if (value) search.set(name, value)
    }
    search.set('view', view)
    return search.toString()
  }, [params, view])

  return (
    <Card className="flex min-h-0 flex-1 flex-col gap-3 p-4">
      <style>{LANDED_COST_TABLE_STYLES}</style>

      {/*  ⚠️ Khổ điện thoại xếp lại thành HAI hàng, không phải bốn:
           «ô mã đơn + Xem + hai nút phụ» / «hai ô ngày».

           Bản gốc bày bốn hàng bậc thang ≈230px chắn trên đầu số liệu. Cắt
           được là nhờ ba việc: bỏ nhãn ô *Mã đơn* (câu gợi ý «PO-001,
           PO-002…» đã nói đúng cái nhãn đó), hai nút phụ bỏ chữ, và hai ô
           ngày tách xuống hàng riêng.

           ⚠️ **Hai ô ngày phải có hàng RIÊNG, đừng gộp tiếp cho ngắn.** Một ô
           ngày cần ~146px mới in trọn `01/01/2026` (biểu tượng lịch 16 + chữ
           78 + dấu × 16 + đệm 24 + khe); hai ô đã 300px, cộng thêm bất cứ nút
           nào là chúng phải co, mà co thì **mất hẳn phần chữ ngày, chỉ còn
           biểu tượng lịch và dấu ×** — đã dựng nhầm đúng kiểu đó một lần
           (12/09/2026, ô còn ~80px). Một ô ngày không đọc được ngày thì không
           còn là ô ngày nữa. Nhãn cũng không bỏ được: «Ngày đặt từ» / «đến»
           là thứ duy nhất phân biệt hai ô. */}
      <div className="flex flex-wrap items-end gap-3 max-md:gap-2">
        <div className="flex items-end gap-2 max-md:w-full">
          <div className="w-[280px] space-y-1 max-md:min-w-0 max-md:flex-1">
            <Label htmlFor="landed-cost-codes" className="max-md:hidden">
              Mã đơn mua hàng
            </Label>
            <Input
              id="landed-cost-codes"
              value={draft.codes}
              placeholder="PO-001, PO-002…"
              onChange={(event) => setDraft({ ...draft, codes: event.target.value })}
              onKeyDown={(event) => {
                if (event.key === 'Enter') setApplied(draft)
              }}
            />
          </div>

          {/*  *Xem* giữ chữ: nó là việc chính của tab này — khác các tab khác,
               ở đây đổi ô lọc KHÔNG tự tải lại. Hai nút phụ bỏ chữ, lấy
               `aria-label` gánh phần nghĩa cho trình đọc màn hình. */}
          <Button onClick={() => setApplied(draft)} className="shrink-0">
            <Search />
            Xem
          </Button>

          {hasData ? (
            <Button
              variant="outline"
              asChild
              title="In báo cáo"
              aria-label="In báo cáo"
              className="max-md:size-9 max-md:px-0"
            >
              <Link
                to={`${appRoutes.procurement.importLandedCostPrint}?${printQuery}`}
                target="_blank"
                rel="noreferrer"
              >
                <Printer />
                <span className="max-md:hidden">In</span>
              </Link>
            </Button>
          ) : (
            <Button
              variant="outline"
              disabled
              title="In báo cáo"
              aria-label="In báo cáo"
              className="max-md:size-9 max-md:px-0"
            >
              <Printer />
              <span className="max-md:hidden">In</span>
            </Button>
          )}

          {can('report', 'export') && (
            <Button
              variant="outline"
              disabled={!hasData}
              onClick={() => purchaseReportApi.exportImportLandedCost(params)}
              title="Xuất Excel"
              aria-label="Xuất Excel"
              className="max-md:size-9 max-md:px-0"
            >
              <FileSpreadsheet />
              <span className="max-md:hidden">Xuất Excel</span>
            </Button>
          )}
        </div>

        <div className="flex items-end gap-3 max-md:w-full max-md:gap-2">
          <div className="space-y-1 max-md:min-w-0 max-md:flex-1">
            <Label>Ngày đặt từ</Label>
            <DatePicker
              value={draft.date_from}
              onChange={(value) => setDraft({ ...draft, date_from: value })}
              disabled={byCodes}
              className="max-md:w-full"
            />
          </div>
          <div className="space-y-1 max-md:min-w-0 max-md:flex-1">
            <Label>đến</Label>
            <DatePicker
              value={draft.date_to}
              onChange={(value) => setDraft({ ...draft, date_to: value })}
              disabled={byCodes}
              className="max-md:w-full"
            />
          </div>
        </div>
      </div>

      {/*  Gấp lại ở khổ hẹp — cùng khuôn với ghi chú của tab Tổng quan. Không bỏ
           được: đoạn này nói chi phí nhập khẩu được CHIA về dòng hàng theo cách
           nào, mà đọc sai cách chia thì con số giá vốn đúng cũng vô dụng. */}
      <CollapsibleNote title="Cách tính giá vốn">
        Chỉ tính <b>đơn nhập khẩu</b>. Chi phí nhập khẩu chia về từng dòng hàng theo khối lượng,
        thiếu khối lượng thì chia theo tiền hàng. Số liệu tính tại thời điểm xem, không lưu lại.
      </CollapsibleNote>

      <div className="flex gap-1 border-b">
        {LANDED_COST_VIEWS.map((option) => (
          <button
            key={option.value}
            type="button"
            onClick={() => setView(option.value)}
            className={cn(
              '-mb-px border-b-2 px-3 py-1.5 text-sm',
              view === option.value
                ? 'border-primary font-semibold text-navy dark:text-foreground'
                : 'border-transparent text-muted-foreground',
            )}
          >
            {option.label}
          </button>
        ))}
      </div>

      <div className="lc-scope min-h-0 flex-1 space-y-3 overflow-auto">
        {isLoading && <Skeleton className="h-64 w-full" />}
        {isError && (
          <p className="py-8 text-center text-sm text-destructive">
            Không tải được số liệu — có thể bạn không có quyền xem báo cáo này.
          </p>
        )}
        {data && !isLoading && (
          <>
            {view === 'orders' ? (
              <LandedCostPivotTable data={data} />
            ) : (
              <LandedCostItemTable data={data} />
            )}
            <LandedCostWarnings data={data} />
          </>
        )}
      </div>
    </Card>
  )
}
