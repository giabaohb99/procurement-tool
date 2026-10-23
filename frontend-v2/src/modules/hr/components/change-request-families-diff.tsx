import { Lock, TriangleAlert } from 'lucide-react'
import { useMemo } from 'react'

import { FAMILY_COLUMNS } from '../config/employee-family-columns'
import { MASKED_VALUE_TEXT } from '../config/employee-profile-fields'
import type {
  ChangeRequestFamilies,
  ChangeRequestFamilyRow,
} from '../types/employee-change-request'
import { isFamiliesChangedSinceSubmit } from '../utils/employee-change-request-review'
import { formatPeopleCell } from '../utils/format-people-cell'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { SectionHeading } from '@/shared/ui/section-heading'
import { cn } from '@/shared/utils/cn'

interface IndexedFamilyRow extends ChangeRequestFamilyRow {
  index: number
}

function indexRows(rows: readonly ChangeRequestFamilyRow[] | null | undefined): IndexedFamilyRow[] {
  return (rows ?? []).map((row, index) => ({ ...row, index }))
}

/**
 * Hộ gia đình của đề nghị sửa hồ sơ (duoc-CR-676): ba bảng «Lúc gửi» / «Hiện tại» / «Đề nghị».
 *
 * Đề nghị THAY CẢ danh sách, nên so theo cả bảng chứ không theo từng dòng (dòng không có khóa
 * chung — thêm một người ở đầu là mọi dòng lệch chỗ). Bảng «Hiện tại» khác «Lúc gửi» nghĩa là
 * phòng Nhân sự đã sửa hộ gia đình sau lúc nhân viên gửi: tô lên + nói rõ, vì duyệt lúc đó backend
 * trả 409 (review M3) — duyệt thì GHI ĐÈ mất bản sửa kia.
 *
 * Bảng xếp DỌC chứ không cạnh nhau: ba bảng sáu cột chia ba bề ngang thì cột nào cũng cụt chữ.
 */
export function ChangeRequestFamiliesDiff({ families }: { families: ChangeRequestFamilies }) {
  const columns = useMemo<DataTableColumn<IndexedFamilyRow>[]>(
    () => [
      { key: 'stt', header: 'STT', width: 56, align: 'center', hideable: false, cell: (row) => row.index + 1 },
      ...FAMILY_COLUMNS.map<DataTableColumn<IndexedFamilyRow>>((col) => ({
        key: col.key,
        header: col.label,
        width: col.key === 'full_name' ? 200 : 140,
        wrap: col.key === 'full_name',
        hideable: false,
        cell: (row) => formatPeopleCell(col.kind, row[col.key as keyof ChangeRequestFamilyRow]),
      })),
    ],
    [],
  )
  const sides = useMemo(() => {
    const changed = isFamiliesChangedSinceSubmit(families)
    const list = [
      { key: 'before', title: 'Lúc gửi', rows: indexRows(families.before), changed: false },
      //  Bản backend cũ chưa gửi `current` thì bỏ hẳn bảng giữa, khỏi bày một bảng rỗng đọc như «hồ sơ không có ai».
      ...(families.current !== undefined
        ? [{ key: 'current', title: 'Hiện tại', rows: indexRows(families.current), changed }]
        : []),
      { key: 'after', title: 'Đề nghị', rows: indexRows(families.after), changed: false },
    ]
    return { list, changed }
  }, [families])

  if (families.masked) {
    return (
      <p className="flex items-center gap-2 text-sm italic text-muted-foreground">
        <Lock className="size-4 shrink-0" />
        {MASKED_VALUE_TEXT}
      </p>
    )
  }

  return (
    <div className="flex flex-col gap-4">
      {sides.changed && (
        <p
          role="alert"
          className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900 dark:border-amber-700 dark:bg-amber-950/40 dark:text-amber-100"
        >
          <TriangleAlert className="mt-0.5 size-4 shrink-0" />
          Hộ gia đình trên hồ sơ đã đổi sau lúc nhân viên gửi. Duyệt sẽ bị chặn để không ghi đè bản
          sửa đó — hãy từ chối và nhờ nhân viên gửi lại đề nghị.
        </p>
      )}
      {sides.list.map((side) => (
        <div
          key={side.key}
          className={cn(
            'flex min-w-0 flex-col gap-2',
            side.changed && 'rounded-md border border-amber-300 p-2 dark:border-amber-700',
          )}
        >
          <div className="flex flex-wrap items-center gap-2">
            <SectionHeading>{`${side.title} (${side.rows.length} người)`}</SectionHeading>
            {side.changed && (
              <Badge
                variant="outline"
                className="border-amber-300 bg-amber-100 text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200"
              >
                Đã đổi sau khi gửi
              </Badge>
            )}
          </div>
          <DataTable
            columns={columns}
            rows={side.rows}
            idColumn={false}
            getRowId={(row) => row.index}
            emptyMessage="Không khai ai."
          />
        </div>
      ))}
    </div>
  )
}
