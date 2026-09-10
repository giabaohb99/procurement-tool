import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { FileSpreadsheet, Printer, Search } from 'lucide-react'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
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

      <div className="flex flex-wrap items-end gap-3">
        <div className="w-[280px] space-y-1">
          <Label htmlFor="landed-cost-codes">Mã đơn mua hàng</Label>
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
        <div className="space-y-1">
          <Label>Ngày đặt từ</Label>
          <DatePicker
            value={draft.date_from}
            onChange={(value) => setDraft({ ...draft, date_from: value })}
            disabled={byCodes}
          />
        </div>
        <div className="space-y-1">
          <Label>đến</Label>
          <DatePicker
            value={draft.date_to}
            onChange={(value) => setDraft({ ...draft, date_to: value })}
            disabled={byCodes}
          />
        </div>

        <Button onClick={() => setApplied(draft)}>
          <Search />
          Xem
        </Button>

        {hasData ? (
          <Button variant="outline" asChild>
            <Link
              to={`${appRoutes.procurement.importLandedCostPrint}?${printQuery}`}
              target="_blank"
              rel="noreferrer"
            >
              <Printer />
              In
            </Link>
          </Button>
        ) : (
          <Button variant="outline" disabled>
            <Printer />
            In
          </Button>
        )}

        {can('report', 'export') && (
          <Button
            variant="outline"
            disabled={!hasData}
            onClick={() => purchaseReportApi.exportImportLandedCost(params)}
          >
            <FileSpreadsheet />
            Xuất Excel
          </Button>
        )}
      </div>

      <p className="text-[13px] text-muted-foreground">
        Chỉ tính <b>đơn nhập khẩu</b>. Chi phí nhập khẩu chia về từng dòng hàng theo khối lượng, thiếu
        khối lượng thì chia theo tiền hàng. Số liệu tính tại thời điểm xem, không lưu lại.
      </p>

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
