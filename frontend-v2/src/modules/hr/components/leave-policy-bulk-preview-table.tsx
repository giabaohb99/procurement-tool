import { useMemo } from 'react'

import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Checkbox } from '@/shared/ui/checkbox'
import { sortRowsBy, type SortValue } from '@/shared/utils/compare-sort-values'
import { formatDate } from '@/shared/utils/format-date'
import type { PolicyPreviewItem } from '../types/leave-policy'
import {
  formatPolicyRange,
  summarizeQuotaChanges,
  type LeaveTypeNameLookup,
} from '../utils/leave-policy-display'
import { useLocalTableSort } from '../hooks/use-local-table-sort'
import { LeavePolicyBulkPreviewCard } from './leave-policy-bulk-preview-card'

/** Dòng "ngoài phạm vi" (`conflict: 'scope'`) không có tên — vẫn phải gọi được người đó là ai. */
function displayName(item: PolicyPreviewItem): string {
  return item.name || `Nhân sự #${item.employee_id}`
}

/** Chữ của ô "Chính sách hiện tại" — dòng `scope` và dòng *Chưa có* (chữ mờ) là ô trống. */
function currentPolicyText(item: PolicyPreviewItem): string {
  if (item.conflict === 'scope' || !item.current) return ''
  return `${item.current.policy_name} (${formatPolicyRange(item.current.from, item.current.to)})`
}

/** Chữ của ô "Lý do không phân bổ được" — dòng phân bổ được thì ô rỗng. */
function conflictText(item: PolicyPreviewItem): string {
  if (!item.conflict) return ''
  return item.conflict === 'self' ? 'Không tự phân bổ chính sách cho chính mình.' : item.conflict_message
}

/** Giá trị đem xếp của một dòng ở cột `columnKey` — đúng chữ ô đang hiện (duoc-CR-748). */
function previewSortValue(item: PolicyPreviewItem, columnKey: string, typeName: LeaveTypeNameLookup): SortValue {
  switch (columnKey) {
    case 'code':
      return item.code
    case 'name':
      return displayName(item)
    case 'department':
      return item.department_name
    case 'hire_date':
      return item.hire_date
    case 'current':
      return currentPolicyText(item)
    case 'changes':
      return item.conflict ? '' : summarizeQuotaChanges(item.changes, typeName)
    case 'conflict':
      return conflictText(item)
    default:
      return null
  }
}

interface LeavePolicyBulkPreviewTableProps {
  items: PolicyPreviewItem[]
  selectedIds: ReadonlySet<number>
  onToggle: (employeeId: number) => void
  onToggleAll: () => void
  typeName: LeaveTypeNameLookup
}

/**
 * Khối 3 của trang Phân bổ hàng loạt (duoc-CR-717): danh sách xem trước có ô chọn. Dòng VƯỚNG (chồng
 * ngày / tự phân bổ / gói ngừng / ngoài phạm vi) bị KHÓA ô chọn và hiện lý do. Dòng `scope` của backend có
 * mã / tên rỗng — hiện "Nhân sự #id" thay vì một ô trống — `createSelectionColumn` dùng chung không có
 * nhánh khóa từng dòng nên cột chọn dựng tại chỗ.
 */
export function LeavePolicyBulkPreviewTable({
  items,
  selectedIds,
  onToggle,
  onToggleAll,
  typeName,
}: LeavePolicyBulkPreviewTableProps) {
  const selectable = useMemo(() => items.filter((i) => !i.conflict), [items])
  const allSelected =
    selectable.length > 0 && selectable.every((i) => selectedIds.has(i.employee_id))
  const someSelected = selectable.some((i) => selectedIds.has(i.employee_id))

  //  duoc-CR-748: bấm tiêu đề cột xếp ngay ở trình duyệt — bản xem trước nạp một lượt (≤ 500 người, backend tự cắt
  //  theo mã và báo `truncated`), và nút Phân bổ chỉ chạy trên đúng những người đang bày ở đây. Ô tick đi theo
  //  `employee_id` chứ không theo vị trí dòng, nên xếp lại không làm lệch người đã chọn.
  //  Mỗi khóa xếp theo đúng chữ ô đang hiện; bằng nhau thì theo mã nhân sự.
  const sort = useLocalTableSort()
  const sortedItems = useMemo(() => {
    if (!sort.sortBy) return items
    return sortRowsBy(
      items,
      (item) => previewSortValue(item, sort.sortBy, typeName),
      sort.sortDir,
      (x, y) => x.employee_id - y.employee_id,
    )
  }, [items, sort.sortBy, sort.sortDir, typeName])

  const columns = useMemo<DataTableColumn<PolicyPreviewItem>[]>(
    () => [
      {
        key: 'select',
        header: 'Chọn',
        width: 52,
        minWidth: 44,
        align: 'center',
        hideable: false,
        defaultPinned: true,
        headerContent: (
          <Checkbox
            checked={allSelected ? true : someSelected ? 'indeterminate' : false}
            disabled={selectable.length === 0}
            aria-label={allSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả người phân bổ được'}
            onCheckedChange={onToggleAll}
          />
        ),
        cell: (i) => (
          <span className="flex items-center justify-center">
            <Checkbox
              checked={!i.conflict && selectedIds.has(i.employee_id)}
              disabled={Boolean(i.conflict)}
              aria-label={`Chọn ${displayName(i)}`}
              onCheckedChange={() => onToggle(i.employee_id)}
            />
          </span>
        ),
      },
      {
        key: 'code',
        header: 'Mã',
        width: 110,
        sortable: true,
        cell: (i) => <span className="tabular-nums">{i.code}</span>,
      },
      {
        key: 'name',
        header: 'Tên',
        width: 200,
        hideable: false,
        sortable: true,
        cell: (i) => <span className="font-medium">{displayName(i)}</span>,
      },
      { key: 'department', header: 'Phòng', width: 170, sortable: true, cell: (i) => i.department_name },
      {
        key: 'hire_date',
        header: 'Ngày vào làm',
        width: 120,
        sortable: true,
        cell: (i) => <span className="tabular-nums">{formatDate(i.hire_date)}</span>,
      },
      {
        key: 'current',
        header: 'Chính sách hiện tại',
        width: 240,
        wrap: true,
        sortable: true,
        cell: (i) =>
          i.conflict === 'scope' ? (
            ''
          ) : i.current ? (
            currentPolicyText(i)
          ) : (
            <span className="text-muted-foreground">Chưa có</span>
          ),
      },
      {
        key: 'changes',
        header: 'Thay đổi quỹ năm nay',
        width: 240,
        wrap: true,
        sortable: true,
        cell: (i) => (i.conflict ? '' : summarizeQuotaChanges(i.changes, typeName)),
      },
      {
        key: 'conflict',
        header: 'Lý do không phân bổ được',
        width: 300,
        wrap: true,
        sortable: true,
        cell: (i) => (i.conflict ? <span className="text-destructive">{conflictText(i)}</span> : ''),
      },
    ],
    [allSelected, someSelected, selectable.length, selectedIds, onToggle, onToggleAll, typeName],
  )

  return (
    <>
      {/*  Khổ điện thoại: thẻ thay bảng nên ô "Chọn tất cả" ở đầu cột mất theo — dựng lại ngay trên danh
           sách. `md:hidden` khớp ngưỡng 768px của `useIsMobile` mà `DataTable` dùng để đổi sang thẻ. */}
      {selectable.length > 0 && (
        <div className="flex items-center gap-2 text-sm md:hidden">
          <Checkbox
            id="bulk-preview-select-all"
            checked={allSelected ? true : someSelected ? 'indeterminate' : false}
            onCheckedChange={onToggleAll}
          />
          <label htmlFor="bulk-preview-select-all">
            {allSelected ? 'Bỏ chọn tất cả' : 'Chọn tất cả người phân bổ được'} ({selectable.length}
            )
          </label>
        </div>
      )}
      <DataTable
        columns={columns}
        rows={sortedItems}
        getRowId={(i) => i.employee_id}
        sortBy={sort.sortBy}
        sortDir={sort.sortDir}
        onSortChange={sort.onSortChange}
        emptyMessage="Không có nhân sự nào khớp bộ lọc (hoặc tất cả đã có chính sách hiệu lực)."
        storageKey="hr.leave-policy-bulk-preview"
        mobileCard={(i) => (
          <LeavePolicyBulkPreviewCard
            item={i}
            checked={selectedIds.has(i.employee_id)}
            onToggle={onToggle}
            typeName={typeName}
          />
        )}
      />
    </>
  )
}
