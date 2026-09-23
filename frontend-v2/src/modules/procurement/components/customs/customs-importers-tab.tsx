// bao-CR-470 — thẻ «Nhà nhập khẩu» (T-05): ai đang nhập mặt hàng này, gộp theo MÃ SỐ
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
import type { CustomsFilters, CustomsImporterRow } from '../../types/customs'
import { buildCustomsParams, formatCustomsUnit, formatUsd } from '../../utils/customs'
import { CustomsUnitChips } from './customs-controls'

interface CustomsImportersTabProps {
  filters: CustomsFilters
  onPickImporter: (id: number, name: string) => void
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

  const columns = useMemo<DataTableColumn<CustomsImporterRow & { rank: number }>[]>(
    () => [
      { key: 'rank', header: '#', width: 56, align: 'right', hideable: false, cell: (r) => r.rank },
      {
        key: 'name',
        header: 'Doanh nghiệp',
        width: 300,
        wrap: true,
        hideable: false,
        cell: (r) => <span className="font-medium">{r.name || '—'}</span>,
      },
      { key: 'tax_code', header: 'Mã số thuế', width: 130, hideable: false, cell: (r) => r.tax_code },
      {
        key: 'count',
        header: 'Số dòng',
        width: 90,
        align: 'right',
        hideable: false,
        cell: (r) => <span className="tabular-nums">{r.count}</span>,
      },
      {
        key: 'qty',
        header: `Tổng lượng (${unit})`,
        width: 140,
        align: 'right',
        hideable: false,
        cell: (r) => <span className="tabular-nums">{formatQuantity(r.qty)}</span>,
      },
      {
        key: 'share',
        header: 'Thị phần',
        width: 150,
        align: 'right',
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
        hideable: false,
        cell: (r) => <span className="tabular-nums">{formatUsd(r.wavg)}</span>,
      },
      {
        key: 'last_date',
        header: 'Lần nhập gần nhất',
        width: 140,
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
          rows={rows}
          getRowId={(r) => r.importer_id}
          isLoading={isLoading}
          isError={isError}
          errorMessage={extractErrorMessage(error)}
          emptyMessage="Không có doanh nghiệp nào khớp bộ lọc."
          onRowClick={(r) => onPickImporter(r.importer_id, r.name)}
        />
      </Card>
    </div>
  )
}
