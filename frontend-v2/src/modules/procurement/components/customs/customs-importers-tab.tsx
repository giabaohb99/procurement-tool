// bao-CR-470 — thẻ "Nhà nhập khẩu" (T-05): ai đang nhập mặt hàng này, gộp theo MÃ SỐ
// THUẾ (cùng công ty có nhiều cách viết tên). Bấm một dòng để lọc danh sách và biểu đồ
// theo doanh nghiệp đó. Chỉ chạy khi đã có từ khóa hoặc mã HS — trang gọi tự chặn.
import { useMemo, useState } from 'react'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useHasChanged } from '@/shared/hooks/use-has-changed'
import { Card } from '@/shared/ui/card'
import { formatDate } from '@/shared/utils/format-date'
import { formatPercent, formatQuantity } from '@/shared/utils/format-money'

import { useCustomsImporters } from '../../hooks/use-customs'
import { useClientTableSort } from '../../hooks/use-client-table-sort'
import type { CustomsFilters, CustomsImporterRow } from '../../types/customs'
import { buildCustomsParams, formatCustomsUnit, formatUsd } from '../../utils/customs'
import { CustomsUnitChips } from './customs-controls'
import { CustomsImporterCard } from './customs-importer-card'

interface CustomsImportersTabProps {
  filters: CustomsFilters
  onPickImporter: (id: number, name: string) => void
}

type ImporterRow = CustomsImporterRow & { rank: number }

/** Giá trị ô đang hiển thị — cột tên trống hiện "—" nên tính là ô trống; thị phần / giá BQ rỗng cũng vậy. */
function importerSortValue(columnKey: string, row: ImporterRow) {
  switch (columnKey) {
    case 'rank':
      return row.rank
    case 'name':
      return row.name
    case 'tax_code':
      return row.tax_code
    case 'count':
      return row.count
    case 'qty':
      return row.qty
    case 'share':
      return row.share
    case 'wavg':
      return row.wavg
    case 'last_date':
      return row.last_date
    default:
      return null
  }
}

export function CustomsImportersTab({ filters, onPickImporter }: CustomsImportersTabProps) {
  const [chartUnit, setChartUnit] = useState('')
  const filtersChanged = useHasChanged(JSON.stringify(filters))
  if (filtersChanged && chartUnit) setChartUnit('')

  //  Bỏ lọc doanh nghiệp: bảng xếp hạng doanh nghiệp mà chỉ còn đúng một doanh nghiệp
  //  đang lọc thì chẳng xếp được gì.
  const params = {
    ...buildCustomsParams({ ...filters, importer_id: '' }),
    ...(chartUnit ? { chart_unit: chartUnit } : {}),
  }
  const { data, isLoading, isError, error } = useCustomsImporters(params, true)
  const unit = formatCustomsUnit(data?.unit)

  const rows = useMemo(
    () => (data?.items ?? []).map((item, index) => ({ ...item, rank: index + 1 })),
    [data],
  )

  //  duoc-CR-744 — bảng 20 doanh nghiệp đã tải đủ nên xếp ngay trên trình duyệt; mặc định giữ thứ tự xếp hạng.
  const sorted = useClientTableSort(rows, importerSortValue)

  const columns = useMemo<DataTableColumn<ImporterRow>[]>(
    () => [
      {
        key: 'rank',
        header: '#',
        width: 56,
        align: 'right',
        sortable: true,
        hideable: false,
        cell: (r) => r.rank,
      },
      {
        key: 'name',
        header: 'Doanh nghiệp',
        width: 300,
        wrap: true,
        sortable: true,
        hideable: false,
        cell: (r) => <span className="font-medium">{r.name || '—'}</span>,
      },
      {
        key: 'tax_code',
        header: 'Mã số thuế',
        width: 130,
        sortable: true,
        hideable: false,
        cell: (r) => r.tax_code,
      },
      {
        key: 'count',
        header: 'Số dòng',
        width: 90,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (r) => <span className="tabular-nums">{r.count}</span>,
      },
      {
        key: 'qty',
        header: `Tổng lượng (${unit})`,
        width: 140,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.qty)}</span>,
      },
      {
        key: 'share',
        header: 'Thị phần',
        width: 150,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (r) =>
          r.share === null ? (
            '—'
          ) : (
            <span className="inline-flex items-center gap-2">
              <span className="h-1.5 w-16 overflow-hidden rounded-full bg-chart-track">
                <span
                  className="block h-full bg-chart-1"
                  style={{ width: `${Math.round(r.share * 100)}%` }}
                />
              </span>
              <span className="tabular-nums">{formatPercent(r.share * 100)}</span>
            </span>
          ),
      },
      {
        key: 'wavg',
        header: `Giá BQ (USD/${unit})`,
        width: 140,
        align: 'right',
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (r) => <span className="tabular-nums">{formatUsd(r.wavg)}</span>,
      },
      {
        key: 'last_date',
        header: 'Lần nhập gần nhất',
        width: 140,
        sortable: true,
        sortDescFirst: true,
        hideable: false,
        cell: (r) => formatDate(r.last_date),
      },
    ],
    [unit],
  )

  return (
    <div className="flex flex-col gap-3">
      {data && <CustomsUnitChips label="Đơn vị" units={data.units} value={data.unit} onChange={setChartUnit} />}
      {data && (
        <p className="text-sm text-muted-foreground">
          {data.total_importers} doanh nghiệp nhập hàng khớp bộ lọc (đơn vị {data.unit}); hiện 20
          doanh nghiệp nhập nhiều nhất. Gộp theo mã số thuế. Bấm một dòng để lọc danh sách và biểu
          đồ theo doanh nghiệp đó.
        </p>
      )}
      <Card className="p-4">
        <DataTable
          columns={columns}
          rows={sorted.rows}
          sortBy={sorted.sortBy}
          sortDir={sorted.sortDir}
          onSortChange={sorted.onSortChange}
          getRowId={(r) => r.importer_id}
          isLoading={isLoading}
          isError={isError}
          errorMessage={extractErrorMessage(error)}
          emptyMessage="Không có doanh nghiệp nào khớp bộ lọc."
          onRowClick={(r) => onPickImporter(r.importer_id, r.name)}
          mobileCard={(r) => <CustomsImporterCard row={r} unit={unit} />}
        />
      </Card>
    </div>
  )
}
