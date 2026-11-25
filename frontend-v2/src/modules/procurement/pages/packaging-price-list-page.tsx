/**
 * duoc-CR-784 — BẢNG GIÁ VTBB (bám `renderPrices` của bản mẫu): mỗi mã một dòng với số lần mua, hai lần mua
 * gần nhất, báo giá mới nhất, giá cũ / mới theo luật của kế hoạch, min–max theo khoảng ngày, ngưỡng
 * sàn–trần và số sản phẩm đang dùng. Phân trang + xếp tại MÁY CHỦ (luật §8) — tham số xếp đi kèm bộ lọc
 * nên Xuất Excel ra đúng thứ tự đang xem. Nút từng dòng: Báo giá mới, đặt Ngưỡng.
 */
import { FileDown, Loader2, Plus } from 'lucide-react'
import { useCallback, useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { exportPackagingPriceList } from '../api/packaging-cost-api'
import {
  PackagingPriceListToolbar,
  type PriceListFilters,
} from '../components/packaging-price-list-toolbar'
import { PackagingExcelImportButton } from '../components/packaging-excel-import-button'
import { PackagingPriceLimitDialog } from '../components/packaging-price-limit-dialog'
import { PackagingQuoteDialog } from '../components/packaging-quote-dialog'
import { PACKAGING_QUOTE_IMPORT } from '../config/packaging-excel-imports'
import { usePackagingCodeOptions } from '../hooks/use-packaging-impact'
import { usePackagingPriceList } from '../hooks/use-packaging-price-list'
import { usePackagingPriceListColumns } from '../hooks/use-packaging-price-list-columns'
import type { PackagingPriceListParams, PackagingPriceRow } from '../types/packaging-cost-types'
import { collectPackagingGroups } from '../utils/packaging-code-match'

const EMPTY_FILTERS: PriceListFilters = { q: '', group: '', scope: 'bom', breachOnly: false }

export function PackagingPriceListPage() {
  const { can } = usePermission()
  const [filters, setFilters] = useState<PriceListFilters>(EMPTY_FILTERS)
  const [range, setRange] = useState({ from: '', to: '' })
  const [sortBy, setSortBy] = useState('')
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('asc')
  const [pageSize, setPageSize] = useState(50)
  const debouncedQ = useDebouncedValue(filters.q, 350)
  const [quoteCode, setQuoteCode] = useState<string | null>(null)
  const [limitRow, setLimitRow] = useState<PackagingPriceRow | null>(null)
  const [exporting, setExporting] = useState(false)
  const once = useSingleFlight()

  /** Bộ lọc + thứ tự gửi máy chủ — dùng chung cho danh sách và Xuất Excel. */
  const filterParams = useMemo<PackagingPriceListParams>(
    () => ({
      q: debouncedQ.trim() || undefined,
      group: filters.group || undefined,
      scope: filters.scope,
      breach_only: filters.breachOnly || undefined,
      date_from: range.from || undefined,
      date_to: range.to || undefined,
      //  Nhịp thứ ba của tiêu đề cột trả khóa rỗng = thôi xếp → KHÔNG gửi, để máy chủ xếp mặc định.
      ...(sortBy ? { sort_by: sortBy, sort_dir: sortDir } : {}),
    }),
    [debouncedQ, filters.group, filters.scope, filters.breachOnly, range, sortBy, sortDir],
  )
  const [page, setPage] = usePageResetOnFilterChange([filterParams, pageSize])
  const list = usePackagingPriceList({ ...filterParams, page, page_size: pageSize })

  //  Nhóm cho chip lấy từ mã đang dùng trong định mức (đã có cache của màn Tác động).
  const optionsQuery = usePackagingCodeOptions()
  const groups = useMemo(() => collectPackagingGroups(optionsQuery.data ?? []), [optionsQuery.data])

  const openQuote = useCallback((row: PackagingPriceRow) => setQuoteCode(row.code), [])
  const columns = usePackagingPriceListColumns({
    canQuote: can('packaging_cost', 'create'),
    canLimit: can('packaging_cost', 'create') || can('packaging_cost', 'write'),
    onQuote: openQuote,
    onLimit: setLimitRow,
  })

  const filtersActive =
    filters.q !== '' ||
    filters.group !== '' ||
    filters.scope !== 'bom' ||
    filters.breachOnly ||
    Boolean(range.from || range.to)

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingPriceList(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })

  return (
    <PageContainer fill>
      <PageHeader
        title="Bảng giá VTBB"
        description="Giá cũ / mới từng mã vật tư bao bì: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT."
        actions={
          <>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng ngày tính min – max"
              onChange={(from, to) => setRange({ from, to })}
            />
            {can('packaging_cost', 'create') && (
              <Button type="button" onClick={() => setQuoteCode('')}>
                <Plus />
                Báo giá mới
              </Button>
            )}
            <PackagingExcelImportButton kind={PACKAGING_QUOTE_IMPORT} />
            {can('packaging_cost', 'export') && (
              <Button
                type="button"
                variant="outline"
                disabled={exporting}
                onClick={() => void exportExcel()}
              >
                {exporting ? <Loader2 className="animate-spin" /> : <FileDown />}
                Xuất Excel
              </Button>
            )}
          </>
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4">
        <DataTable
          //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => row.code}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={
            filtersActive
              ? 'Không có mã nào khớp bộ lọc.'
              : 'Chưa có mã vật tư bao bì nào trong định mức.'
          }
          storageKey="procurement.packaging-price-list"
          filtersActive={filtersActive}
          onResetFilters={() => {
            setFilters(EMPTY_FILTERS)
            setRange({ from: '', to: '' })
          }}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={(by, dir) => {
            setSortBy(by)
            setSortDir(dir)
          }}
          toolbar={
            <PackagingPriceListToolbar filters={filters} groups={groups} onChange={setFilters} />
          }
          pagination={{
            page,
            pageSize,
            total: list.data?.total ?? 0,
            onPageChange: setPage,
            onPageSizeChange: setPageSize,
            unitLabel: 'mã',
          }}
        />
      </Card>

      {quoteCode !== null && (
        <PackagingQuoteDialog
          open
          defaultCode={quoteCode || undefined}
          onOpenChange={(open) => !open && setQuoteCode(null)}
        />
      )}
      {limitRow && (
        <PackagingPriceLimitDialog
          code={limitRow.code}
          name={limitRow.name}
          onClose={() => setLimitRow(null)}
        />
      )}
    </PageContainer>
  )
}
