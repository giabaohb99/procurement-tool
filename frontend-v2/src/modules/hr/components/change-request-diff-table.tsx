import { useMemo } from 'react'

import {
  MASKED_VALUE_TEXT,
  formatEmployeeFieldValue,
  getEmployeeFieldLabel,
} from '../config/employee-profile-fields'
import type { ChangeRequestItem } from '../types/employee-change-request'
import { isChangedSinceSubmit } from '../utils/employee-change-request-review'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'

interface ChangeRequestDiffTableProps {
  items: readonly ChangeRequestItem[]
}

function renderValue(item: ChangeRequestItem, value: ChangeRequestItem['before']) {
  if (item.masked) return <span className="italic text-muted-foreground">{MASKED_VALUE_TEXT}</span>
  const text = formatEmployeeFieldValue(item.field, value)
  return text ? text : <span className="text-muted-foreground">(trống)</span>
}

function ChangedBadge() {
  return (
    <Badge
      variant="outline"
      className="border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
    >
      Đã đổi sau khi gửi
    </Badge>
  )
}

/**
 * Bảng so sánh một NHÓM của đề nghị sửa hồ sơ (duoc-CR-676): Trường · Lúc gửi · Hiện tại · Đề nghị.
 *
 * Dòng có "Hiện tại" khác "Lúc gửi" được tô và gắn nhãn "Đã đổi sau khi gửi" — hồ sơ đã bị sửa
 * (bởi phòng Nhân sự, nhập Excel…) sau lúc nhân viên gửi, nên người duyệt phải biết mình sắp ghi
 * đè lên giá trị nào. Dòng bị che (thiếu quyền nhạy cảm) không so được nên không tô.
 */
export function ChangeRequestDiffTable({ items }: ChangeRequestDiffTableProps) {
  const columns = useMemo<DataTableColumn<ChangeRequestItem>[]>(
    () => [
      {
        key: 'field',
        header: 'Trường',
        width: 200,
        hideable: false,
        cell: (item) => getEmployeeFieldLabel(item.field),
      },
      { key: 'before', header: 'Lúc gửi', width: 220, wrap: true, hideable: false, cell: (item) => renderValue(item, item.before) },
      {
        key: 'current',
        header: 'Hiện tại',
        width: 240,
        wrap: true,
        hideable: false,
        cell: (item) => (
          <span className="flex flex-wrap items-center gap-1.5">
            {renderValue(item, item.current)}
            {isChangedSinceSubmit(item) && <ChangedBadge />}
          </span>
        ),
      },
      {
        key: 'after',
        header: 'Đề nghị',
        width: 220,
        wrap: true,
        hideable: false,
        cell: (item) => <span className="font-medium">{renderValue(item, item.after)}</span>,
      },
    ],
    [],
  )
  const rows = useMemo(() => [...items], [items])

  return (
    <DataTable
      columns={columns}
      rows={rows}
      //  Bảng con 4 cột cố định trong trang chi tiết: tắt cột ID + thanh "Tải lại / Cột" (mọi cột
      //  `hideable: false` thì bảng không dựng thanh đó) — có chúng chỉ thêm nhiễu.
      idColumn={false}
      getRowId={(item) => `${item.group}-${item.field}`}
      emptyMessage="Nhóm này không có ô nào đổi."
      //  Màn hẹp: bốn cột 880px không vừa 390px, cột "Đề nghị" — thứ quan trọng nhất — trôi khỏi
      //  tầm mắt. Thẻ xếp dọc bày đủ ba giá trị của một ô.
      mobileCard={(item) => (
        <div className="flex flex-col gap-1 text-sm">
          <div className="font-medium">{getEmployeeFieldLabel(item.field)}</div>
          <div>
            <span className="text-muted-foreground">Lúc gửi: </span>
            {renderValue(item, item.before)}
          </div>
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-muted-foreground">Hiện tại: </span>
            {renderValue(item, item.current)}
            {isChangedSinceSubmit(item) && <ChangedBadge />}
          </div>
          <div>
            <span className="text-muted-foreground">Đề nghị: </span>
            <span className="font-medium">{renderValue(item, item.after)}</span>
          </div>
        </div>
      )}
      rowClassName={(item) => (isChangedSinceSubmit(item) ? 'bg-amber-50 dark:bg-amber-950/30' : undefined)}
    />
  )
}
