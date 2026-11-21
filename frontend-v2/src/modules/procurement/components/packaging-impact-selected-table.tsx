/**
 * duoc-CR-784 — bảng MÃ ĐÃ CHỌN của màn Tác động giá: giá cũ / mới, ô giá giả định (nền vàng như bản
 * mẫu), chênh lệch, số SP dùng, min–max theo sổ giá và ngưỡng sàn–trần. Giá đang dùng ra ngoài ngưỡng
 * thì ô ngưỡng tô đỏ và ghi chú nói rõ — người chọn mã thấy ngay giá NCC báo có vượt trần không.
 */
import { X } from 'lucide-react'
import { useMemo, type ReactNode } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Button } from '@/shared/ui/button'
import { PACKAGING_COST_WARNING_CODE } from '@/shared/constants/statuses'
import { NumberInput, PRICE_MAX_DECIMALS } from '@/shared/ui/number-input'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { isOutsidePriceLimit } from '../utils/packaging-price-format'
import {
  joinPackagingWarnings,
  normalizeWarnings,
  packagingWarningText,
} from '../utils/packaging-warning-text'
import { PackagingCodeLink } from './packaging-code-link'
import { DiffText, PercentText, PriceText, RangeText } from './packaging-price-cells'

interface PackagingImpactSelectedTableProps {
  rows: PackagingSelectedCode[] | undefined
  isLoading: boolean
  isError: boolean
  /** Giá giả định đang gõ (chưa qua trễ) — ô nhập đọc từ đây, không đọc `row.assumed` của máy chủ. */
  assumed: Record<string, number>
  /** `null` = bỏ giả định, quay về giá bảng giá. */
  onAssumedChange: (code: string, price: number | null) => void
  onRemove: (code: string) => void
  /** Nội dung bên trái thanh công cụ của bảng (dòng tóm tắt số mã / số sản phẩm bị ảnh hưởng). */
  toolbar?: ReactNode
}

/** Câu ghi chú của một mã: cảnh báo máy chủ gửi + câu ngoài ngưỡng tính tại chỗ (giá giả định chưa kịp gửi). */
function buildNote(row: PackagingSelectedCode, applied: number | null): string {
  //  Bỏ cảnh báo ngưỡng của máy chủ rồi tự tính lại theo giá đang gõ — máy chủ chỉ biết giá đã gửi
  //  (trễ 400 ms), để nguyên thì vừa gõ về trong ngưỡng mà ô vẫn báo "vượt trần" thêm một nhịp.
  const limitKinds: number[] = [
    PACKAGING_COST_WARNING_CODE.BELOW_FLOOR,
    PACKAGING_COST_WARNING_CODE.ABOVE_CEILING,
  ]
  const serverNotes = normalizeWarnings(row.warnings).filter((w) => !limitKinds.includes(w.kind))
  const notes = [joinPackagingWarnings(serverNotes)]
  if (isNumber(applied) && isNumber(row.floor) && applied < row.floor)
    notes.push(packagingWarningText({ kind: PACKAGING_COST_WARNING_CODE.BELOW_FLOOR }))
  if (isNumber(applied) && isNumber(row.ceiling) && applied > row.ceiling)
    notes.push(packagingWarningText({ kind: PACKAGING_COST_WARNING_CODE.ABOVE_CEILING }))
  return notes.filter(Boolean).join('; ')
}

function isNumber(value: number | null | undefined): value is number {
  return typeof value === 'number' && Number.isFinite(value)
}

export function PackagingImpactSelectedTable({
  rows,
  isLoading,
  isError,
  assumed,
  onAssumedChange,
  onRemove,
  toolbar,
}: PackagingImpactSelectedTableProps) {
  const columns = useMemo<DataTableColumn<PackagingSelectedCode>[]>(() => {
    const appliedOf = (row: PackagingSelectedCode) => assumed[row.code] ?? row.new
    return [
      {
        key: 'code',
        header: 'Mã',
        width: 100,
        hideable: false,
        defaultPinned: true,
        cell: (row) => <PackagingCodeLink code={row.code} />,
      },
      //  Một dòng, rê chuột hiện đủ — tên xuống 2–3 dòng làm bảng cao lổn nhổn (người chủ chê 20/11/2026).
      {
        key: 'name',
        header: 'Tên vật tư',
        width: 210,
        cell: (row) => <span title={row.name}>{row.name}</span>,
      },
      { key: 'group', header: 'Nhóm', width: 80, cell: (row) => row.group },
      {
        key: 'old',
        header: 'Giá cũ',
        width: 90,
        align: 'right',
        cell: (row) => <PriceText value={row.old} />,
      },
      {
        key: 'new',
        header: 'Giá mới',
        width: 90,
        align: 'right',
        cell: (row) => <PriceText value={row.new} />,
      },
      {
        key: 'assumed',
        header: 'Giá giả định',
        width: 130,
        hideable: false,
        cell: (row) => (
          <NumberInput
            aria-label={`Giá giả định ${row.code}`}
            placeholder="Nhập giá"
            title="Nhập giá giả định để mô phỏng trước khi NCC chốt giá; xóa trắng để quay về giá mới"
            maxDecimals={PRICE_MAX_DECIMALS}
            className="h-8 bg-amber-50 text-right dark:bg-amber-950"
            value={assumed[row.code] ?? 0}
            //  Ô xóa trắng trả 0 — coi là BỎ giả định (giá bao bì 0 đồng không có nghĩa mô phỏng).
            onChange={(price) => onAssumedChange(row.code, price > 0 ? price : null)}
          />
        ),
      },
      {
        key: 'diff',
        header: 'Chênh lệch',
        width: 100,
        align: 'right',
        cell: (row) => <DiffText value={row.diff} bold />,
      },
      {
        key: 'pct',
        header: '%',
        width: 80,
        align: 'right',
        cell: (row) => <PercentText value={row.pct} />,
      },
      { key: 'usage', header: 'Số SP', width: 80, align: 'right', cell: (row) => row.usage },
      //  Min và Max tách hai cột (người chủ chốt 21/11/2026) — giá thấp / cao nhất trong sổ giá của mã.
      {
        key: 'min',
        header: 'Min',
        width: 90,
        align: 'right',
        cell: (row) => <PriceText value={row.min} />,
      },
      {
        key: 'max',
        header: 'Max',
        width: 90,
        align: 'right',
        cell: (row) => <PriceText value={row.max} />,
      },
      {
        key: 'limit',
        header: 'Sàn – Trần',
        width: 120,
        align: 'right',
        cell: (row) => (
          <RangeText
            low={row.floor}
            high={row.ceiling}
            danger={isOutsidePriceLimit(appliedOf(row), row.floor, row.ceiling)}
          />
        ),
      },
      {
        key: 'note',
        header: 'Ghi chú',
        width: 140,
        wrap: true,
        cell: (row) => (
          <span className="text-xs text-destructive">{buildNote(row, appliedOf(row))}</span>
        ),
      },
      {
        key: 'actions',
        header: '',
        width: 44,
        hideable: false,
        align: 'center',
        cell: (row) => (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label={`Bỏ ${row.code}`}
            onClick={() => onRemove(row.code)}
          >
            <X className="size-4" />
          </Button>
        ),
      },
    ]
  }, [assumed, onAssumedChange, onRemove])

  return (
    //  Chọn cả nhóm là vài chục mã — chặn chiều cao, cuộn trong khung, để bảng sản phẩm
    //  không bị đẩy xuống tận cuối trang.
    <div className="flex max-h-[28rem] min-h-0 flex-col">
      <DataTable
        //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
        idColumn={false}
        fillHeight
        columns={columns}
        rows={rows}
        getRowId={(row) => row.code}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Các mã đã chọn chưa có trong định mức nào."
        storageKey="procurement.packaging-impact-selected"
        toolbar={toolbar}
      />
    </div>
  )
}
