// bao-CR-470 — thẻ «So sánh» (B-05): giá bình quân gia quyền của 2–5 mặt hàng / hoạt chất
// trên CÙNG một đơn vị tính. Bộ lọc khác (mã HS, xuất xứ, khoảng ngày…) áp chung cho mọi
// mặt hàng. Kỳ trống của một mặt hàng để TRỐNG, đường đứt ở đó chứ không nối qua.
import { GitCompareArrows, Plus, X } from 'lucide-react'
import { useMemo, useState } from 'react'
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts'

import { extractErrorMessage } from '@/core/api'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { CHART_COLORS } from '@/shared/ui/chart'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { Input } from '@/shared/ui/input'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatUnitPrice } from '@/shared/utils/format-money'

import { useCustomsCompare } from '../../hooks/use-customs'
import type { CustomsFilters, CustomsPeriod } from '../../types/customs'
import {
  buildCompareParams,
  cleanCompareTerms,
  COMPARE_MAX_TERMS,
  COMPARE_MIN_TERMS,
  CUSTOMS_PERIOD_OPTIONS,
  formatCustomsUnit,
  formatUsd,
  mergeCompareSeries,
  type CompareRow,
} from '../../utils/customs'
import { CustomsSegmentedChoice, CustomsUnitChips } from './customs-controls'

/** Năm màu cố định theo THỨ TỰ ô nhập — xóa một ô thì màu các ô sau không nhảy lung tung. */
const COMPARE_COLORS = [...CHART_COLORS, 'var(--destructive)'] as const
const AXIS_TICK = { fill: 'var(--muted-foreground)', fontSize: 12 }

interface CustomsCompareTabProps {
  filters: CustomsFilters
}

export function CustomsCompareTab({ filters }: CustomsCompareTabProps) {
  const [terms, setTerms] = useState<string[]>(() =>
    filters.q.trim() ? [filters.q.trim(), ''] : ['', ''],
  )
  const [period, setPeriod] = useState<CustomsPeriod>('month')
  const [validation, setValidation] = useState('')
  /** Tham số của lần bấm So sánh gần nhất — `null` = chưa bấm. */
  const [submitted, setSubmitted] = useState<Record<string, unknown> | null>(null)

  const { data, isFetching, isError, error } = useCustomsCompare(submitted)

  function runCompare(chartUnit = '') {
    if (cleanCompareTerms(terms).length < COMPARE_MIN_TERMS) {
      setValidation('Nhập ít nhất 2 mặt hàng / hoạt chất khác nhau để so sánh.')
      return
    }
    setValidation('')
    setSubmitted(buildCompareParams(terms, filters, period, chartUnit))
  }

  const rows = useMemo(() => (data ? mergeCompareSeries(data) : []), [data])
  const unit = formatCustomsUnit(data?.unit)

  const columns = useMemo<DataTableColumn<CompareRow>[]>(() => {
    if (!data) return []
    return [
      { key: 'label', header: 'Kỳ', width: 110, hideable: false, cell: (r) => r.label },
      ...data.terms.map<DataTableColumn<CompareRow>>((term, index) => ({
        key: `term-${index}`,
        header: `${term.term} (USD/${unit})`,
        width: 180,
        align: 'right',
        hideable: false,
        cell: (r) =>
          r.values[index] === null ? (
            '—'
          ) : (
            <span className="tabular-nums">
              {formatUsd(r.values[index])}{' '}
              <span className="text-xs text-muted-foreground">({r.counts[index]})</span>
            </span>
          ),
      })),
    ]
  }, [data, unit])

  return (
    <div className="flex flex-col gap-3">
      <Card className="gap-3 p-4">
        <p className="text-sm text-muted-foreground">
          So sánh giá bình quân gia quyền của 2–5 mặt hàng / hoạt chất trên CÙNG một đơn vị tính.
          Bộ lọc khác (mã HS, xuất xứ, khoảng ngày…) áp chung cho mọi mặt hàng.
        </p>
        <div className="flex flex-wrap items-center gap-2">
          {terms.map((term, index) => (
            <span key={index} className="inline-flex items-center gap-1.5">
              <span
                aria-hidden
                className="size-2.5 shrink-0 rounded-full"
                style={{ backgroundColor: COMPARE_COLORS[index] }}
              />
              <Input
                value={term}
                placeholder={`Mặt hàng ${index + 1}`}
                aria-label={`Mặt hàng ${index + 1}`}
                className="w-44"
                onChange={(event) =>
                  setTerms((current) =>
                    current.map((item, position) => (position === index ? event.target.value : item)),
                  )
                }
                onKeyDown={(event) => {
                  if (event.key === 'Enter') runCompare()
                }}
              />
              {terms.length > COMPARE_MIN_TERMS && (
                <Button
                  type="button"
                  variant="ghost"
                  size="icon-sm"
                  aria-label={`Bỏ mặt hàng ${index + 1}`}
                  onClick={() => setTerms((current) => current.filter((_, position) => position !== index))}
                >
                  <X className="size-4" />
                </Button>
              )}
            </span>
          ))}
          {terms.length < COMPARE_MAX_TERMS && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => setTerms((current) => [...current, ''])}
            >
              <Plus className="size-4" />
              Thêm
            </Button>
          )}
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <CustomsSegmentedChoice
            label="Kỳ"
            value={period}
            options={CUSTOMS_PERIOD_OPTIONS}
            onChange={setPeriod}
          />
          <Button type="button" onClick={() => runCompare()} disabled={isFetching}>
            <GitCompareArrows className="size-4" />
            So sánh
          </Button>
        </div>
        {validation && <p className="text-sm text-destructive">{validation}</p>}
        {isError && <p className="text-sm text-destructive">{extractErrorMessage(error)}</p>}
      </Card>

      {submitted && !data && isFetching && <Skeleton className="h-64 w-full" />}

      {data && (
        <>
          <CustomsUnitChips
            label="Đơn vị"
            units={data.units}
            value={data.unit}
            onChange={(nextUnit) => runCompare(nextUnit)}
          />
          <Card className="min-w-0 gap-3 p-4">
            <ul className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground">
              {data.terms.map((term, index) => (
                <li key={term.term} className="flex items-center gap-1.5">
                  <span
                    aria-hidden
                    className="h-0.5 w-3.5"
                    style={{ backgroundColor: COMPARE_COLORS[index] }}
                  />
                  {term.term}
                </li>
              ))}
            </ul>
            {rows.some((row) => row.values.some((value) => value !== null)) ? (
              <CompareChart rows={rows} terms={data.terms.map((term) => term.term)} unit={unit} />
            ) : (
              <p className="py-8 text-center text-sm text-muted-foreground">
                Không có giá để vẽ ở đơn vị này.
              </p>
            )}
          </Card>
          <Card className="gap-2 p-4">
            <DataTable
              columns={columns}
              rows={rows}
              getRowId={(r) => r.period}
              emptyMessage="Không có kỳ nào để so sánh."
            />
            <p className="text-sm font-medium">
              Cả khoảng:{' '}
              {data.terms.map((term, index) => (
                <span key={term.term} className="mr-4 inline-flex items-center gap-1.5">
                  <span
                    aria-hidden
                    className="size-2 rounded-full"
                    style={{ backgroundColor: COMPARE_COLORS[index] }}
                  />
                  {term.term}: <span className="tabular-nums">{formatUsd(term.kpi?.wavg)}</span>
                  <span className="text-xs font-normal text-muted-foreground">
                    ({term.kpi?.count ?? 0})
                  </span>
                </span>
              ))}
            </p>
            <p className="text-xs text-muted-foreground">
              Số trong ngoặc là số dòng hàng của kỳ đó.
            </p>
          </Card>
        </>
      )}
    </div>
  )
}

interface ComparePoint {
  label: string
  [key: string]: string | number | null | boolean
}

function CompareChart({ rows, terms, unit }: { rows: CompareRow[]; terms: string[]; unit: string }) {
  const data = rows.map<ComparePoint>((row) => {
    const point: ComparePoint = { label: row.label }
    row.values.forEach((value, index) => {
      point[`t${index}`] = value
      point[`c${index}`] = row.counts[index]
      point[`low${index}`] = row.lowData[index]
    })
    return point
  })

  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 8, right: 12, bottom: 0, left: 0 }}>
        <CartesianGrid vertical={false} stroke="var(--chart-grid)" />
        <XAxis dataKey="label" tickLine={false} axisLine={false} tick={AXIS_TICK} />
        <YAxis
          width="auto"
          tickLine={false}
          axisLine={false}
          tick={AXIS_TICK}
          domain={['auto', 'auto']}
          tickFormatter={(value: number) => formatUnitPrice(value)}
        />
        <Tooltip
          wrapperStyle={{ outline: 'none' }}
          formatter={(value, name) => [
            `${formatUsd(typeof value === 'number' ? value : null)} USD/${unit}`,
            terms[Number(String(name).slice(1))] ?? String(name),
          ]}
        />
        {terms.map((term, index) => (
          <Line
            key={term}
            dataKey={`t${index}`}
            name={`t${index}`}
            stroke={COMPARE_COLORS[index]}
            strokeWidth={2}
            connectNulls={false}
            isAnimationActive={false}
            dot={(props) => {
              const cx = Number(props.cx)
              const cy = Number(props.cy)
              const point = props.payload as ComparePoint | undefined
              if (!point || point[`t${index}`] === null || !Number.isFinite(cx) || !Number.isFinite(cy)) {
                return <g key={`dot-${index}-${props.index}`} />
              }
              return (
                <circle
                  key={`dot-${index}-${props.index}`}
                  cx={cx}
                  cy={cy}
                  r={3.5}
                  stroke={COMPARE_COLORS[index]}
                  strokeWidth={2}
                  fill={point[`low${index}`] ? 'var(--card)' : COMPARE_COLORS[index]}
                />
              )
            }}
          />
        ))}
      </LineChart>
    </ResponsiveContainer>
  )
}
