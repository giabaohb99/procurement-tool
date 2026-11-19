import { FolderKanban, Settings2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Select, SelectContent, SelectItem, SelectSeparator, SelectTrigger, SelectValue } from '@/shared/ui/select'

import type { WorkList } from '../types/work'
import { matchesProjectGroup, type FlatWorkGroup, type ProjectGroupFilterValue } from '../utils/work-groups'

interface ProjectGroupFilterProps {
  groups: FlatWorkGroup[]
  projects: WorkList[]
  value: ProjectGroupFilterValue
  onChange: (value: ProjectGroupFilterValue) => void
  /** Mở hộp Quản lý nhóm (đổi tên · thành viên · lưu trữ) — bao-CR-482. */
  onManage: (group: FlatWorkGroup) => void
  /** Đang bật "Lưu trữ" ở màn — mới hiện nhóm đã lưu trữ trong danh sách chọn. */
  showArchived: boolean
}

const ALL = 'all'
const NONE = 'none'

const toKey = (value: ProjectGroupFilterValue) => String(value)
const fromKey = (key: string): ProjectGroupFilterValue => (key === ALL || key === NONE ? key : Number(key))

/**
 * Lọc bảng dự án theo NHÓM bằng MỘT ô chọn thả xuống (duoc-CR-783, anh Được 19/11/2026: "hiện project theo kiểu này
 * không okee lắm"). Bản trước vẽ mỗi nhóm thành một nút kèm bánh răng dàn ngang — vài nhóm thử (đã lưu trữ, 0 dự án) là
 * hàng nút tràn, đẩy cả thanh công cụ xuống.
 *
 * - Nhóm đã lưu trữ chỉ có trong danh sách khi bật "Lưu trữ" ở màn; nhóm con thụt vào dưới nhóm cha.
 * - Nút *Quản lý nhóm* (mở hộp đổi tên / mời thành viên / lưu trữ nhóm) chỉ hiện khi đang chọn MỘT nhóm.
 */
export function ProjectGroupFilter({
  groups,
  projects,
  value,
  onChange,
  onManage,
  showArchived,
}: ProjectGroupFilterProps) {
  const countOf = (v: ProjectGroupFilterValue) => projects.filter((p) => matchesProjectGroup(p, v)).length
  const visibleGroups = groups.filter((g) => showArchived || g.is_archived !== 1)
  const looseCount = countOf(NONE)
  const selected = typeof value === 'number' ? groups.find((g) => g.id === value) : undefined

  return (
    <div className="flex items-center gap-1">
      <Select value={toKey(value)} onValueChange={(key) => onChange(fromKey(key))}>
        <SelectTrigger className="h-9 w-56 *:data-[slot=select-value]:flex-1" aria-label="Lọc theo nhóm dự án">
          <FolderKanban className="size-4 shrink-0 text-muted-foreground" />
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value={ALL}>
            Tất cả nhóm <span className="text-muted-foreground tabular-nums">· {projects.length}</span>
          </SelectItem>
          {visibleGroups.length > 0 && <SelectSeparator />}
          {visibleGroups.map((g) => (
            <SelectItem key={g.id} value={toKey(g.id)}>
              <span style={{ paddingLeft: g.depth * 12 }}>
                {g.name}
                {g.is_archived === 1 && <span className="text-muted-foreground"> (lưu trữ)</span>}{' '}
                <span className="text-muted-foreground tabular-nums">· {countOf(g.id)}</span>
              </span>
            </SelectItem>
          ))}
          {looseCount > 0 && (
            <>
              <SelectSeparator />
              <SelectItem value={NONE}>
                Chưa thuộc nhóm <span className="text-muted-foreground tabular-nums">· {looseCount}</span>
              </SelectItem>
            </>
          )}
        </SelectContent>
      </Select>
      {selected && (
        //  Có CHỮ, không chỉ biểu tượng: bánh răng trơn anh Được nhìn không hiểu để làm gì (19/11/2026).
        <Button
          variant="outline"
          size="sm"
          className="h-9"
          title={`Đổi tên, mời thành viên, lưu trữ nhóm "${selected.name}"`}
          aria-label={`Quản lý nhóm dự án ${selected.name}`}
          onClick={() => onManage(selected)}
        >
          <Settings2 className="size-4" />
          <span className="max-md:hidden">Quản lý nhóm</span>
        </Button>
      )}
    </div>
  )
}
