import { FolderKanban, Settings2 } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

import type { WorkList } from '../types/work'
import { matchesProjectGroup, type FlatWorkGroup, type ProjectGroupFilterValue } from '../utils/work-groups'

interface ProjectGroupFilterProps {
  groups: FlatWorkGroup[]
  projects: WorkList[]
  value: ProjectGroupFilterValue
  onChange: (value: ProjectGroupFilterValue) => void
  /** Mở hộp Quản lý nhóm (đổi tên · thành viên · lưu trữ) — bao-CR-482. */
  onManage: (group: FlatWorkGroup) => void
}

function Chip({
  on,
  label,
  count,
  onClick,
  icon,
  className,
}: {
  on: boolean
  label: string
  count: number
  onClick: () => void
  icon?: boolean
  className?: string
}) {
  return (
    <button
      type="button"
      aria-pressed={on}
      onClick={onClick}
      className={cn(
        'inline-flex h-8 items-center gap-1.5 rounded-md border px-2.5 text-sm transition-colors',
        on
          ? 'border-primary/40 bg-primary/10 font-medium text-primary'
          : 'bg-background text-muted-foreground hover:text-foreground',
        className,
      )}
    >
      {icon && <FolderKanban className="size-4 shrink-0" />}
      {label}
      <span className="text-xs tabular-nums opacity-80">{count.toLocaleString('vi-VN')}</span>
    </button>
  )
}

/**
 * Cụm NHÓM DỰ ÁN thành NÚT LỌC trên thanh công cụ của bảng dự án (duoc-CR-782).
 *
 * Bản bao-CR-482 vẽ mỗi nhóm thành một thẻ đứng riêng một hàng trên bảng — chỉ để biết nhóm tồn tại và mở hộp quản lý,
 * công ty mới có một nhóm nên cả hàng chỉ có một thẻ nhỏ, nhìn trống. Giờ nhóm vừa là bộ lọc (bấm DX là bảng còn dự án
 * của DX) vừa giữ nút bánh răng quản lý nhóm, nằm chung hàng với ô tìm.
 */
export function ProjectGroupFilter({ groups, projects, value, onChange, onManage }: ProjectGroupFilterProps) {
  const countOf = (v: ProjectGroupFilterValue) => projects.filter((p) => matchesProjectGroup(p, v)).length
  const looseCount = countOf('none')

  return (
    <div role="group" aria-label="Lọc theo nhóm dự án" className="flex flex-wrap items-center gap-1.5">
      <Chip on={value === 'all'} label="Tất cả" count={projects.length} onClick={() => onChange('all')} />
      {groups.map((group) => (
        //  Nút lọc và nút bánh răng dính làm một khối: hai nút rời thì không rõ bánh răng thuộc nhóm nào.
        <span key={group.id} className="inline-flex items-center">
          <Chip
            icon
            on={value === group.id}
            label={group.is_archived === 1 ? `${group.name} (lưu trữ)` : group.name}
            count={countOf(group.id)}
            onClick={() => onChange(group.id)}
            className="rounded-r-none"
          />
          <Button
            variant="outline"
            size="icon-sm"
            title={`Quản lý nhóm dự án ${group.name}`}
            aria-label={`Quản lý nhóm dự án ${group.name}`}
            className="size-8 rounded-l-none border-l-0 text-muted-foreground"
            onClick={() => onManage(group)}
          >
            <Settings2 className="size-4" />
          </Button>
        </span>
      ))}
      {/*  Có nhóm thì mới cần nút "Chưa thuộc nhóm": không nhóm nào thì nó trùng hẳn "Tất cả". */}
      {groups.length > 0 && looseCount > 0 && (
        <Chip on={value === 'none'} label="Chưa thuộc nhóm" count={looseCount} onClick={() => onChange('none')} />
      )}
    </div>
  )
}
