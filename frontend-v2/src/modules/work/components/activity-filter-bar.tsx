import { Check, Filter, User } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { cn } from '@/shared/utils/cn'
import {
  WORK_ACTIVITY_KIND_OPTIONS,
  type WorkActivityActor,
  type WorkActivityKind,
} from '../types/activity'

interface ActivityFilterBarProps {
  kind: WorkActivityKind | null
  onKindChange: (value: WorkActivityKind | null) => void
  by: number | null
  onByChange: (value: number | null) => void
  actors: WorkActivityActor[]
  /** Tổng số dòng KHỚP bộ lọc — backend đếm, không phải số dòng đã tải. */
  total: number
}

/**
 * Hai ô lọc nhanh của tab «Hoạt động» (§8): theo LOẠI sự kiện và theo NGƯỜI.
 *
 * Dựng bằng `DropdownMenu` nút chữ không viền, đúng khuôn `ToolbarMenu` của
 * `work-toolbar.tsx` — cùng phân hệ thì hai hàng nút phải nhìn như một.
 * Cố ý KHÔNG dùng `@/shared/conditional-filter`: bộ đó dựng câu điều kiện nhiều
 * tầng cho bảng chứng từ, ở đây chỉ có đúng hai lựa chọn một-giá-trị.
 */
export function ActivityFilterBar({
  kind,
  onKindChange,
  by,
  onByChange,
  actors,
  total,
}: ActivityFilterBarProps) {
  const kindLabel =
    WORK_ACTIVITY_KIND_OPTIONS.find((o) => o.value === kind)?.label ?? 'Tất cả hoạt động'
  const byLabel = actors.find((a) => a.id === by)?.name ?? 'Mọi người'

  return (
    <div className="flex flex-wrap items-center gap-1 border-b pb-2">
      <FilterMenu
        icon={Filter}
        srLabel="Loại hoạt động"
        label={kindLabel}
        active={kind !== null}
        options={WORK_ACTIVITY_KIND_OPTIONS.map((o) => ({ value: o.value, label: o.label }))}
        value={kind}
        onChange={onKindChange}
      />
      <FilterMenu
        icon={User}
        srLabel="Người thao tác"
        label={byLabel}
        active={by !== null}
        options={[
          { value: null, label: 'Mọi người' },
          ...actors.map((a) => ({ value: a.id, label: a.name })),
        ]}
        value={by}
        onChange={onByChange}
      />

      {/*  Đếm ở mép phải: dòng hoạt động cuộn dần nên không nhìn ra nó dài bao
          nhiêu, mà "còn bao nhiêu nữa" là câu hỏi đầu tiên khi mở tab này. */}
      <span className="ml-auto text-xs text-muted-foreground">{total} hoạt động</span>
    </div>
  )
}

interface FilterMenuProps<T> {
  icon: typeof Filter
  /** Tên trường cho trình đọc màn hình — nút chỉ hiện GIÁ TRỊ đang chọn. */
  srLabel: string
  label: string
  /** Đang lọc thì nút đậm màu lên, không thì không ai nhớ mình đang lọc. */
  active: boolean
  value: T
  options: { value: T; label: string }[]
  onChange: (value: T) => void
}

function FilterMenu<T>({
  icon: Icon,
  srLabel,
  label,
  active,
  value,
  options,
  onChange,
}: FilterMenuProps<T>) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          size="sm"
          aria-label={`${srLabel}: ${label}`}
          className={cn(
            'text-muted-foreground hover:text-foreground',
            active && 'text-primary hover:text-primary',
          )}
        >
          <Icon className="size-4" />
          {label}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="max-h-80 w-56 overflow-y-auto">
        {options.map((o) => (
          <DropdownMenuItem
            key={String(o.value)}
            role="menuitemradio"
            aria-checked={o.value === value}
            onSelect={() => onChange(o.value)}
            className={cn(o.value === value && 'text-primary focus:text-primary')}
          >
            <span className="truncate">{o.label}</span>
            {o.value === value && <Check className="ml-auto size-4 shrink-0" />}
          </DropdownMenuItem>
        ))}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
