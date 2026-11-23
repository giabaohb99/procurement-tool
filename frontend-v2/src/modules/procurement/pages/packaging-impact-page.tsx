/**
 * duoc-CR-784 — màn TÁC ĐỘNG TĂNG GIÁ BAO BÌ (bám `renderImpact` / `drawImpact` của bản mẫu
 * `Bao cao gia NVL san xuat - 11.2026.html`).
 *
 * Chọn một hoặc nhiều mã chai / nắp / nhãn / nhãn thùng / thùng → bảng mã đã chọn (giá cũ, mới, ô giá
 * giả định), bốn thẻ KPI, và bảng mọi sản phẩm dùng ít nhất một mã đó với chi phí bao bì /chai, /thùng cũ
 * và mới. Giá giả định trễ 400 ms rồi mới tính lại; dữ liệu cũ giữ nguyên trong lúc tính. Bảng sản phẩm phân
 * trang / tìm / lọc nâng cao / xếp tại MÁY CHỦ (có thể hàng nghìn sản phẩm khi chọn cả nhóm); thẻ KPI luôn tính trên toàn bộ tập.
 */
import { FileDown, Loader2, Printer } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { UI_ACTION_CODE } from '@/core/telemetry/ui-event-codes'
import { trackUiAction } from '@/core/telemetry/track-ui-action'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { exportPackagingImpact } from '../api/packaging-cost-api'
import { PackagingCodePicker } from '../components/packaging-code-picker'
import { PackagingImpactProductsTable } from '../components/packaging-impact-products-table'
import { PackagingImpactSelectedTable } from '../components/packaging-impact-selected-table'
import { PackagingImpactSummary } from '../components/packaging-impact-summary'
import { usePackagingCodeOptions, usePackagingImpact } from '../hooks/use-packaging-impact'
import { usePackagingImpactTableState } from '../hooks/use-packaging-impact-table-state'
import type { PackagingImpactRequest } from '../types/packaging-cost-types'
import { sortPackagingCodeOptions } from '../utils/packaging-code-match'
import { impactFiltersToRequest } from '../utils/packaging-impact-filters'
import { packagingImpactPrintHref } from '../utils/packaging-impact-print'

/** Chỉ gửi giả định của mã còn đang chọn — bỏ mã khỏi danh sách là bỏ luôn giá giả định của nó. */
function pickAssumed(
  codes: string[],
  assumed: Record<string, number>,
): Record<string, number> | undefined {
  const picked = Object.fromEntries(
    codes.filter((code) => assumed[code] != null).map((code) => [code, assumed[code]]),
  )
  return Object.keys(picked).length ? picked : undefined
}

export function PackagingImpactPage() {
  const { can } = usePermission()
  const [codes, setCodes] = useState<string[]>([])
  const [assumed, setAssumed] = useState<Record<string, number>>({})
  const [range, setRange] = useState({ from: '', to: '' })
  const debouncedAssumed = useDebouncedValue(assumed, 400)
  const once = useSingleFlight()
  const [exporting, setExporting] = useState(false)

  const optionsQuery = usePackagingCodeOptions()
  const options = useMemo(
    () => sortPackagingCodeOptions(optionsQuery.data ?? []),
    [optionsQuery.data],
  )

  const table = usePackagingImpactTableState([codes, range])

  /** Phần thân dùng chung cho tính toán và Xuất Excel (cùng bộ lọc + thứ tự); chưa kèm trang. */
  const filterBody = useMemo<PackagingImpactRequest>(
    () => ({
      codes,
      assumed_prices: pickAssumed(codes, debouncedAssumed),
      date_from: range.from || undefined,
      date_to: range.to || undefined,
      q: table.query || undefined,
      ...impactFiltersToRequest(table.filters),
      //  Chưa chọn cột xếp thì KHÔNG gửi — máy chủ xếp mặc định theo mã HH.
      ...(table.sortBy ? { sort_by: table.sortBy, sort_dir: table.sortDir } : {}),
    }),
    [codes, debouncedAssumed, range, table.query, table.filters, table.sortBy, table.sortDir],
  )
  const body = useMemo<PackagingImpactRequest>(
    () => ({ ...filterBody, page: table.page, page_size: table.pageSize }),
    [filterBody, table.page, table.pageSize],
  )
  const impact = usePackagingImpact(body)
  const data = codes.length ? impact.data : undefined

  const changeAssumed = useCallback((code: string, price: number | null) => {
    setAssumed((prev) => {
      const next = { ...prev }
      if (price == null) delete next[code]
      else next[code] = price
      return next
    })
  }, [])
  const removeCode = useCallback(
    (code: string) => setCodes((prev) => prev.filter((item) => item !== code)),
    [],
  )

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        //  Xuất theo giá giả định ĐANG GÕ, không đợi nhịp trễ — người bấm Xuất muốn đúng số trên ô.
        await exportPackagingImpact({ ...filterBody, assumed_prices: pickAssumed(codes, assumed) })
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })


  return (
    <PageContainer className="space-y-4">
      <PageHeader
        title="Tác động tăng giá bao bì"
        description="Chọn mã bao bì, nhập giá giả định để xem sản phẩm nào tăng chi phí bao nhiêu trước khi NCC chốt giá."
        actions={
          <>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng ngày tính min – max"
              onChange={(from, to) => setRange({ from, to })}
            />
            {/* In = xem (quyền đọc). Mở tab mới, mã + giá giả định ĐANG GÕ + từ khóa / cột xếp của bảng; trang in tự nạp đủ mọi sản phẩm. */}
            {can('packaging_cost', 'read') &&
              (codes.length ? (
                <Button asChild variant="outline">
                  <Link
                    to={packagingImpactPrintHref({
                      ...filterBody,
                      assumed_prices: pickAssumed(codes, assumed),
                    })}
                    target="_blank"
                    rel="noreferrer"
                    onClick={() => trackUiAction(UI_ACTION_CODE.PRINT)}
                  >
                    <Printer />
                    In
                  </Link>
                </Button>
              ) : (
                <Button type="button" variant="outline" disabled title="Chọn ít nhất một mã để in">
                  <Printer />
                  In
                </Button>
              ))}
            {can('packaging_cost', 'export') && (
              <Button
                type="button"
                variant="outline"
                disabled={!codes.length || exporting}
                onClick={() => void exportExcel()}
              >
                {exporting ? <Loader2 className="animate-spin" /> : <FileDown />}
                Xuất Excel
              </Button>
            )}
          </>
        }
      />

      <Card className="gap-3 p-4">
        <PackagingCodePicker
          options={options}
          value={codes}
          onChange={setCodes}
          loading={optionsQuery.isLoading}
        />
        {codes.length === 0 ? (
          <p className="text-sm text-muted-foreground">
            Bấm vào ô trên để chọn một hoặc nhiều mã. Gõ tên nhóm (<b>chai</b>, <b>nắp</b>,{' '}
            <b>nhãn</b>…) rồi bấm <b>Chọn tất cả</b> để chọn cả nhóm.
          </p>
        ) : (
          <PackagingImpactSelectedTable
            rows={data?.selected}
            isLoading={impact.isLoading}
            isError={impact.isError}
            assumed={assumed}
            onAssumedChange={changeAssumed}
            onRemove={removeCode}
            //  Một hàng duy nhất trên bảng: tóm tắt bên trái, nút của bảng bên phải; bỏ hết mã = nút x trong ô chọn mã.
            toolbar={
              <div className="flex items-center gap-3">
                <PackagingImpactSummary kpis={data?.kpis} />
                {impact.isFetching && (
                  <Loader2 className="size-3.5 animate-spin text-muted-foreground" />
                )}
              </div>
            }
          />
        )}
      </Card>

      {codes.length > 0 && (
        <Card className="gap-3 p-4">
          <PackagingImpactProductsTable
            rows={data?.products}
            total={data?.products_total ?? 0}
            affected={data?.kpis.affected_products}
            isLoading={impact.isLoading}
            isError={impact.isError}
            view={table}
          />
        </Card>
      )}
    </PageContainer>
  )
}
