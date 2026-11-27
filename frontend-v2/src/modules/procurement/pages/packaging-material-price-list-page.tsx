/**
 * duoc-CR-798 — BẢNG GIÁ NGUYÊN LIỆU (27/11/2026): dựng y khuôn Bảng giá VTBB (cùng bộ cột, cùng khung bảng) cho
 * nguyên liệu, mục menu ngay dưới Bảng giá VTBB. CHƯA nối dữ liệu (chủ dự án chốt: dựng màn trước, dữ liệu sau) nên bảng
 * luôn rỗng và nói thẳng điều đó; khi có nguồn giá nguyên liệu thì thay `rows` bằng hook gọi API như màn VTBB.
 * Gác cùng khóa xem bảng giá `packaging_price_list` (mục menu khai trong `routes.tsx`).
 * Thanh lọc đủ như màn VTBB (ô chọn mã, chip nhóm, phạm vi mã, khoảng ngày tính min – max — 27/11/2026); chưa có dữ liệu
 * nên bộ lọc chỉ giữ trạng thái trên màn, chưa gửi đi đâu.
 */
import { useMemo, useState } from 'react'

import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import {
  PackagingPriceListToolbar,
  type PriceListFilters,
} from '../components/packaging-price-list-toolbar'
import { usePackagingPriceListColumns } from '../hooks/use-packaging-price-list-columns'
import type { PackagingPriceRow } from '../types/packaging-cost-types'

/** Chưa có nguồn dữ liệu — bảng rỗng có chủ đích, không phải lỗi tải. */
const NO_ROWS: PackagingPriceRow[] = []
const EMPTY_FILTERS: PriceListFilters = { codes: [], group: '', scope: 'bom' }

export function PackagingMaterialPriceListPage() {
  const isMobile = useIsMobile()
  const [filters, setFilters] = useState<PriceListFilters>(EMPTY_FILTERS)
  const [range, setRange] = useState({ from: '', to: '' })
  const filtersActive =
    filters.codes.length > 0 || filters.group !== '' || filters.scope !== 'bom' || Boolean(range.from || range.to)
  const baseColumns = usePackagingPriceListColumns({ canQuote: false, onQuote: () => undefined })
  //  Cùng bộ cột với Bảng giá VTBB, chỉ đổi chữ "VTBB" thành "nguyên liệu" ở tiêu đề.
  const columns = useMemo(
    () =>
      baseColumns.map((column) =>
        typeof column.header === 'string' && column.header === 'Mã VTBB'
          ? { ...column, header: 'Mã nguyên liệu' }
          : typeof column.header === 'string' && column.header === 'Tên vật tư'
            ? { ...column, header: 'Tên nguyên liệu' }
            : column,
      ),
    [baseColumns],
  )

  return (
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Bảng giá nguyên liệu"
        description={
          isMobile
            ? undefined
            : 'Giá cũ / mới từng mã nguyên liệu: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.'
        }
        actions={
          <DateRangePicker
            from={range.from}
            to={range.to}
            placeholder="Khoảng ngày tính min – max"
            className="max-md:basis-full"
            onChange={(from, to) => setRange({ from, to })}
          />
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4 max-md:gap-2 max-md:p-3">
        <DataTable
          idColumn={false}
          fillHeight
          columns={columns}
          rows={NO_ROWS}
          getRowId={(row) => row.code}
          emptyMessage={
            filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có dữ liệu bảng giá nguyên liệu.'
          }
          storageKey="procurement.packaging-material-price-list"
          filtersActive={filtersActive}
          onResetFilters={() => {
            setFilters(EMPTY_FILTERS)
            setRange({ from: '', to: '' })
          }}
          toolbar={
            <PackagingPriceListToolbar
              filters={filters}
              groups={[]}
              searchPlaceholder="Tìm mã nguyên liệu — gõ mã, tên, nhóm hoặc NCC, chọn được nhiều mã"
              onChange={setFilters}
            />
          }
        />
      </Card>
    </PageContainer>
  )
}
