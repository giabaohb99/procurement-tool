import { useMemo } from 'react'
import { useNavigate } from 'react-router-dom'

import { DataTable, type DataTableColumn } from '@/shared/data-table'

import type { ReportDrilldownResponse, ReportDrilldownRow } from '../types/report-drilldown'
import { formatDrilldownCell, resolveDrilldownLink } from '../utils/format-drilldown-cell'

type Row = ReportDrilldownRow & { __rowKey: string }

const NUMERIC_KINDS = new Set(['int', 'days', 'money'])

interface ReportDrilldownTableProps {
  data: ReportDrilldownResponse
  /** Nhớ bố cục cột theo TỪNG chỉ số — bộ cột mỗi chỉ số một khác. */
  storageKey: string
}

/**
 * Bảng của ngăn «Danh sách người» — cột dựng THẲNG từ `columns` backend trả (không gõ
 * tay), định dạng ô theo `kind`. Dòng có `link` nội bộ thì bấm mở trang đó (hồ sơ nhân
 * sự, đơn nghỉ…). Tối đa 500 dòng, không phân trang.
 */
export function ReportDrilldownTable({ data, storageKey }: ReportDrilldownTableProps) {
  const navigate = useNavigate()

  const rows = useMemo<Row[]>(
    () => data.rows.map((r, i) => ({ ...r, __rowKey: String(i) })),
    [data.rows],
  )
  const hasLinks = useMemo(() => rows.some((r) => resolveDrilldownLink(r) !== null), [rows])

  const columns = useMemo<DataTableColumn<Row>[]>(
    () =>
      data.columns.map((col, index) => ({
        key: col.key,
        header: col.label,
        width: index === 1 ? 200 : NUMERIC_KINDS.has(col.kind) ? 130 : 140,
        align: NUMERIC_KINDS.has(col.kind) ? ('right' as const) : undefined,
        //  Hai cột đầu (Mã NV · Họ tên) là định danh — luôn hiện, ghim trái khi bảng nhiều cột.
        hideable: index > 1,
        defaultPinned: index === 0 && data.columns.length > 6,
        wrap: col.kind === 'text' && index === 1,
        cell: (row: Row) => formatDrilldownCell(row[col.key], col.kind),
      })),
    [data.columns],
  )

  const [titleCol, ...restCols] = data.columns

  return (
    <DataTable
      //  Bộ cột đổi theo chỉ số: mount lại để bảng tính lại bố cục trên ĐÚNG bộ cột mới.
      key={data.columns.map((c) => c.key).join('|')}
      fillHeight
      idColumn={false}
      columns={columns}
      rows={rows}
      getRowId={(r) => r.__rowKey}
      emptyMessage="Không có ai trong danh sách này."
      storageKey={storageKey}
      filtersActive={false}
      onRowClick={
        hasLinks
          ? (row) => {
              const link = resolveDrilldownLink(row)
              if (link) navigate(link)
            }
          : undefined
      }
      mobileCard={(row) => (
        <div className="space-y-1 text-sm">
          {titleCol && (
            <p className="font-medium">
              {formatDrilldownCell(row[titleCol.key], titleCol.kind)}
              {restCols[0]?.kind === 'text' && ` · ${formatDrilldownCell(row[restCols[0].key], 'text')}`}
            </p>
          )}
          {restCols.slice(restCols[0]?.kind === 'text' ? 1 : 0).map((col) => {
            const value = formatDrilldownCell(row[col.key], col.kind)
            if (!value) return null
            return (
              <p key={col.key} className="text-muted-foreground">
                {col.label}: <span className="text-foreground">{value}</span>
              </p>
            )
          })}
        </div>
      )}
    />
  )
}
