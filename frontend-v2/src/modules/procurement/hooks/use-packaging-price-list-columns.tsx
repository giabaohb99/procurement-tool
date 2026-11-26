/**
 * duoc-CR-784 — cột của Bảng giá VTBB. Tách khỏi trang cho trang dưới 200 dòng.
 *
 * Cột bật `sortable` gửi `sort_by` = khóa cột (hoặc `sortKey`) lên máy chủ — khóa phải nằm trong
 * `SORT_KEYS` của `packaging_cost/price_list_service.py`. Hai cột giá mua gần nhất / lần trước KHÔNG bật
 * xếp vì máy chủ chưa có khóa cho chúng — bật mà máy chủ không nhận là lỗi "bấm không ăn" (luật §8).
 */
import { useMemo } from 'react'

import type { DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { formatDate } from '@/shared/utils/format-date'

import { PackagingCodeLink } from '../components/packaging-code-link'
import {
  DiffText,
  EmptyDash,
  PercentText,
  PriceText,
} from '../components/packaging-price-cells'
import type { PackagingPriceRow } from '../types/packaging-cost-types'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'

interface PriceListColumnOptions {
  canQuote: boolean
  onQuote: (row: PackagingPriceRow) => void
}

export function usePackagingPriceListColumns({ canQuote, onQuote }: PriceListColumnOptions) {
  return useMemo<DataTableColumn<PackagingPriceRow>[]>(
    () => [
        {
          key: 'code',
          header: 'Mã VTBB',
          width: 120,
          sortable: true,
          hideable: false,
          defaultPinned: true,
          cell: (row) => <PackagingCodeLink code={row.code} />,
        },
        {
          key: 'name',
          header: 'Tên vật tư',
          width: 220,
          wrap: true,
          sortable: true,
          cell: (row) => row.name || <span className="text-muted-foreground">(chưa có tên)</span>,
        },
        { key: 'group', header: 'Nhóm', width: 100, sortable: true, cell: (row) => row.group },
        { key: 'unit', header: 'ĐVT', width: 70, cell: (row) => row.unit },
        //  Mọi giá của bảng này tính bằng đồng Việt Nam (người chủ chốt 26/11/2026) — cột chỉ để ghi rõ đơn vị tiền.
        { key: 'currency', header: 'Tiền tệ', width: 80, cell: () => 'VND' },
        {
          key: 'purchase_count',
          header: 'Số lần mua',
          width: 90,
          align: 'right',
          sortable: true,
          sortDescFirst: true,
          cell: (row) => row.purchase_count,
        },
        {
          key: 'last_date',
          header: 'Mua gần nhất',
          width: 110,
          sortable: true,
          sortDescFirst: true,
          cell: (row) => (row.last_date ? formatDate(row.last_date) : <EmptyDash />),
        },
        {
          key: 'last_purchase_price',
          header: 'Giá mua gần nhất',
          width: 110,
          align: 'right',
          sortable: true,
          sortDescFirst: true,
          cell: (row) => <PriceText value={row.last_purchase_price} />,
        },
        {
          key: 'prev_purchase_price',
          header: 'Giá mua lần trước',
          width: 110,
          align: 'right',
          sortable: true,
          sortDescFirst: true,
          cell: (row) => <PriceText value={row.prev_purchase_price} />,
        },
        {
          key: 'quote',
          header: 'Báo giá mới',
          width: 120,
          align: 'right',
          sortable: true,
          sortKey: 'quote_price',
          cell: (row) =>
            row.quote ? (
              <div className="leading-tight">
                <PriceText value={row.quote.price} />
                <div className="text-xs text-muted-foreground">
                  {formatDate(row.quote.valid_from)}
                </div>
              </div>
            ) : (
              <EmptyDash />
            ),
        },
        {
          key: 'old',
          header: 'Giá cũ',
          width: 100,
          align: 'right',
          sortable: true,
          cell: (row) => <PriceText value={row.old} className="font-semibold" />,
        },
        {
          key: 'new',
          header: 'Giá mới',
          width: 100,
          align: 'right',
          sortable: true,
          cell: (row) => <PriceText value={row.new} className="font-semibold" />,
        },
        {
          key: 'diff',
          header: 'Chênh lệch',
          width: 100,
          align: 'right',
          sortable: true,
          cell: (row) => <DiffText value={row.diff} />,
        },
        {
          key: 'pct',
          header: '%',
          width: 80,
          align: 'right',
          sortable: true,
          cell: (row) => <PercentText value={row.pct} />,
        },
        //  Min và Max tách hai cột (người chủ chốt 21/11/2026), mỗi cột xếp theo đúng giá trị nó hiện.
        {
          key: 'min',
          header: 'Min',
          width: 100,
          align: 'right',
          sortable: true,
          defaultHidden: true,
          cell: (row) => <PriceText value={row.min} />,
        },
        {
          key: 'max',
          header: 'Max',
          width: 100,
          align: 'right',
          sortable: true,
          sortDescFirst: true,
          defaultHidden: true,
          cell: (row) => <PriceText value={row.max} />,
        },
        {
          key: 'usage',
          header: 'Số SP đang dùng',
          width: 100,
          align: 'right',
          sortable: true,
          sortDescFirst: true,
          cell: (row) => row.usage,
        },
        {
          key: 'note',
          header: 'Ghi chú',
          width: 200,
          wrap: true,
          defaultHidden: true,
          cell: (row) => (
            <span className="text-xs text-destructive">{joinPackagingWarnings(row.warnings)}</span>
          ),
        },
        {
          key: 'actions',
          header: 'Thao tác',
          width: 170,
          hideable: false,
          cell: (row) => (
            <div className="flex gap-1" onClick={(event) => event.stopPropagation()}>
              {canQuote && (
                <Button
                  type="button"
                  size="sm"
                  variant="outline"
                  className="h-7"
                  onClick={() => onQuote(row)}
                >
                  Báo giá
                </Button>
              )}
            </div>
          ),
        },
    ],
    [canQuote, onQuote],
  )
}
