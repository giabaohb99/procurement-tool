/**
 * duoc-CR-798 — BẢNG GIÁ NGUYÊN LIỆU (27/11/2026): khuôn Bảng giá VTBB cho nguyên liệu (sản phẩm nhóm `NL`), mục menu ngay
 * dưới Bảng giá VTBB.
 *
 * bao-CR-800 — nối DỮ LIỆU THẬT và khóa quyền RIÊNG `packaging_material_price` (chủ dự án chốt 27/11/2026: có bộ phận được
 * xem giá nguyên liệu, có bộ phận không). Màn chỉ gọi ba đường của nguyên liệu (`material-price-list`, đường xuất của nó,
 * `material-code-options`); TUYỆT ĐỐI không gọi `price-list` / `code-options` của VTBB — người chỉ giữ khóa nguyên liệu gọi
 * hai đường đó là 403. Khác màn VTBB: không có nút phạm vi (nguyên liệu không nằm trong định mức bao bì), không có cột Số SP
 * đang dùng / Thao tác. Phân trang + xếp tại MÁY CHỦ; tham số xếp đi kèm bộ lọc nên Xuất Excel ra đúng thứ tự đang xem.
 *
 * bao-CR-801 — bấm mã nguyên liệu mở màn Lịch sử mua nguyên liệu của đúng mã đó (cùng khóa `packaging_material_price`), như
 * bấm mã ở Bảng giá VTBB mở Lịch sử mua hàng.
 */
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { useSingleFlight } from '@/shared/hooks/use-single-flight'
import { Card } from '@/shared/ui/card'
import { DateRangePicker } from '@/shared/ui/date-range-picker'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'

import { exportPackagingMaterialPriceList } from '../api/packaging-cost-api'
import { PackagingExportExcelButton } from '../components/packaging-header-buttons'
import { PackagingPriceListToolbar } from '../components/packaging-price-list-toolbar'
import { PackagingPriceRowCard } from '../components/packaging-price-row-card'
import {
  usePackagingMaterialCodeOptions,
  usePackagingMaterialPriceList,
} from '../hooks/use-packaging-material-price-list'
import { usePackagingPriceListColumns } from '../hooks/use-packaging-price-list-columns'
import { usePackagingPriceListState } from '../hooks/use-packaging-price-list-state'
import { collectPackagingGroups, sortPackagingCodeOptions } from '../utils/packaging-code-match'

export function PackagingMaterialPriceListPage() {
  const { can } = usePermission()
  const isMobile = useIsMobile()
  //  Bộ lọc / cột xếp / trang sống trên URL — cùng hook với Bảng giá VTBB, chế độ nguyên liệu (không có `scope`).
  const {
    filters,
    setFilters,
    range,
    setRange,
    sortBy,
    sortDir,
    setSort,
    page,
    setPage,
    pageSize,
    setPageSize,
    filterParams,
    listParams,
    filtersActive,
    resetFilters,
  } = usePackagingPriceListState({ rawMaterial: true })
  const [exporting, setExporting] = useState(false)
  const once = useSingleFlight()
  const list = usePackagingMaterialPriceList(listParams)

  //  Ô chọn mã = mọi mã nguyên liệu đã có giá; nhóm cho chip lấy từ chính danh sách đó (không đụng đường của VTBB).
  const optionsQuery = usePackagingMaterialCodeOptions()
  const codeOptions = useMemo(() => sortPackagingCodeOptions(optionsQuery.data ?? []), [optionsQuery.data])
  const groups = useMemo(() => collectPackagingGroups(codeOptions), [codeOptions])

  const columns = usePackagingPriceListColumns({ rawMaterial: true })

  const exportExcel = () =>
    once(async () => {
      setExporting(true)
      try {
        await exportPackagingMaterialPriceList(filterParams)
      } catch (error) {
        toast.error(error instanceof Error ? error.message : 'Không xuất được tệp Excel')
      } finally {
        setExporting(false)
      }
    })

  return (
    //  `fill` chỉ từ `md`: ở khổ hẹp bảng thành danh sách thẻ dài, nhét vào khe cao cố định là cuộn LỒNG (xem crud-list-page).
    <PageContainer fill className="max-md:h-auto">
      <PageHeader
        title="Bảng giá nguyên liệu"
        description={
          isMobile
            ? undefined
            : 'Giá cũ / mới từng mã nguyên liệu: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.'
        }
        actions={
          <>
            <DateRangePicker
              from={range.from}
              to={range.to}
              placeholder="Khoảng ngày tính min – max"
              className="max-md:basis-full"
              onChange={(from, to) => setRange({ from, to })}
            />
            {can('packaging_material_price', 'export') && (
              <PackagingExportExcelButton exporting={exporting} onClick={() => void exportExcel()} />
            )}
          </>
        }
      />
      <Card className="flex min-h-0 flex-1 flex-col gap-4 p-4 max-md:gap-2 max-md:p-3">
        <DataTable
          //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
          idColumn={false}
          fillHeight
          columns={columns}
          rows={list.data?.items}
          getRowId={(row) => row.code}
          isLoading={list.isLoading}
          isError={list.isError}
          emptyMessage={filtersActive ? 'Không có mã nào khớp bộ lọc.' : 'Chưa có nguyên liệu nào có giá.'}
          storageKey="procurement.packaging-material-price-list"
          mobileCard={(row) => <PackagingPriceRowCard row={row} rawMaterial />}
          mobileSort
          filtersActive={filtersActive}
          onResetFilters={resetFilters}
          sortBy={sortBy}
          sortDir={sortDir}
          onSortChange={setSort}
          toolbar={
            <PackagingPriceListToolbar
              rawMaterial
              filters={filters}
              groups={groups}
              codeOptions={codeOptions}
              codeOptionsLoading={optionsQuery.isLoading}
              onChange={setFilters}
            />
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
    </PageContainer>
  )
}
