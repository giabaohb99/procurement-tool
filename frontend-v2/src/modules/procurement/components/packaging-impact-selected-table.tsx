/**
 * duoc-CR-784 — bảng MÃ ĐÃ CHỌN của màn Tác động giá: giá cũ / mới, ô giá giả định (nền vàng như bản
 * mẫu), chênh lệch, số SP dùng và min–max theo sổ giá (ngưỡng sàn–trần đã bỏ ở phase 04). Chip nhóm (Chai · Nắp ·
 * Nhãn · Nhãn thùng · Thùng) trên thanh công cụ chỉ ẩn dòng của bảng này — danh sách mã đã chọn và phép tính không đổi.
 */
import { X } from 'lucide-react'
import { useMemo, useState, type ReactNode } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { useIsMobile } from '@/shared/hooks/use-mobile'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

import type { PackagingSelectedCode } from '../types/packaging-cost-types'
import { buildSelectedGroupChips, resolveSelectedGroup } from '../utils/packaging-selected-groups'
import { joinPackagingWarnings } from '../utils/packaging-warning-text'
import { PackagingAssumedPriceInput } from './packaging-assumed-price-input'
import { PackagingCodeLink } from './packaging-code-link'
import { PackagingSelectedCodeCard } from './packaging-selected-code-card'
import { DiffText, PercentText, PriceText } from './packaging-price-cells'

interface PackagingImpactSelectedTableProps {
  rows: PackagingSelectedCode[] | undefined
  isLoading: boolean
  isError: boolean
  /** Giá giả định đang gõ (chưa qua trễ) — ô nhập đọc từ đây, không đọc `row.assumed` của máy chủ. */
  assumed: Record<string, number>
  /** `null` = bỏ giả định, quay về giá bảng giá. */
  onAssumedChange: (code: string, price: number | null) => void
  onRemove: (code: string) => void
  /** Nội dung bên trái thanh công cụ của bảng (hiện chỉ là vòng quay "đang tính lại"; số liệu tóm tắt đã ở ba thẻ phía trên). */
  toolbar?: ReactNode
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
  const [pickedGroup, setPickedGroup] = useState('')
  const isMobile = useIsMobile()
  const chips = useMemo(() => buildSelectedGroupChips(rows), [rows])
  //  Nhóm đã chọn mà bị bỏ hết mã thì tự về "Tất cả" (suy ra lúc vẽ, không cần effect).
  const group = resolveSelectedGroup(pickedGroup, chips)
  const shownRows = useMemo(
    () => (group ? rows?.filter((row) => row.group === group) : rows),
    [rows, group],
  )
  const columns = useMemo<DataTableColumn<PackagingSelectedCode>[]>(() => {
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
          <PackagingAssumedPriceInput
            code={row.code}
            value={assumed[row.code]}
            onChange={onAssumedChange}
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
      { key: 'usage', header: 'Số SP bị ảnh hưởng', width: 104, align: 'right', cell: (row) => row.usage },
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
        key: 'note',
        header: 'Ghi chú',
        width: 140,
        wrap: true,
        cell: (row) => (
          <span className="text-xs text-destructive">{joinPackagingWarnings(row.warnings)}</span>
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
    //  Khổ điện thoại (thẻ, mỗi thẻ ~220px): khung cao theo màn để thấy được vài thẻ mà vẫn chừa bảng sản phẩm phía dưới.
    <div className="flex max-h-[28rem] min-h-0 flex-col max-md:max-h-[70svh]">
      <DataTable
        //  Dòng khóa theo mã, không có `id` số: để mặc định thì lúc đang tải bảng chèn cột ID rồi gỡ, làm tách nhóm cột.
        idColumn={false}
        fillHeight
        columns={columns}
        rows={shownRows}
        getRowId={(row) => row.code}
        isLoading={isLoading}
        isError={isError}
        emptyMessage="Các mã đã chọn chưa có trong định mức nào."
        storageKey="procurement.packaging-impact-selected"
        mobileCard={(row) => (
          <PackagingSelectedCodeCard
            row={row}
            assumed={assumed[row.code]}
            onAssumedChange={onAssumedChange}
            onRemove={onRemove}
          />
        )}
        //  Khổ điện thoại: chỉ một nhóm mã thì thanh công cụ chỉ còn mỗi nút Tải lại đứng trơ một hàng (dải trống người chủ
        //  chê 26/11/2026) — bỏ hẳn hàng đó; bảng thẻ không có menu Cột nên không mất gì.
        toolbar={
          isMobile && chips.length <= 1 ? undefined : (
            <div className="flex flex-1 flex-wrap items-center gap-x-3 gap-y-2">
              {toolbar}
              {/*  Một nhóm duy nhất thì không có gì để lọc. */}
              {chips.length > 1 && (
                <div className="flex flex-wrap gap-1" role="group" aria-label="Lọc mã đã chọn theo nhóm">
                  {[{ group: '', label: 'Tất cả', count: rows?.length ?? 0 }, ...chips.map((chip) => ({ ...chip, label: chip.group }))].map(
                    (chip) => (
                      <button
                        key={chip.group || 'all'}
                        type="button"
                        aria-pressed={group === chip.group}
                        onClick={() => setPickedGroup(chip.group)}
                        className={cn(
                          'h-7 rounded-full border px-3 text-xs hover:bg-accent',
                          group === chip.group &&
                            'border-primary bg-primary text-primary-foreground hover:bg-primary/90',
                        )}
                      >
                        {chip.label} ({chip.count.toLocaleString('vi-VN')})
                      </button>
                    ),
                  )}
                </div>
              )}
            </div>
          )
        }
      />
    </div>
  )
}
