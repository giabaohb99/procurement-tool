import { ChevronDown, ChevronUp } from 'lucide-react'
import { useState } from 'react'

import type { ProfileGroupDefinition, ProfileSectionKey } from '@/app/components/profile/profile-sections'
import { Badge } from '@/shared/ui/badge'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { readSectionOpen, writeSectionOpen } from '@/shared/utils/section-open-storage'

export interface ProfileSectionBadge {
  count: number
  variant: 'destructive' | 'secondary'
}

interface ProfileSettingsNavProps {
  groups: ProfileGroupDefinition[]
  active: ProfileSectionKey
  onSelect: (key: ProfileSectionKey) => void
  /** Số đếm cạnh mục (việc cần làm, thông báo chưa đọc, yêu cầu hỗ trợ). 0 thì không hiện. */
  badges?: Partial<Record<ProfileSectionKey, ProfileSectionBadge>>
  className?: string
}

/**
 * Thanh bên trái của Trang cá nhân (P0 doc 21 §6.5): 4 nhóm, mỗi nhóm vài mục — thay dải 13 tab ngang tràn hàng.
 *
 * Khổ từ `md` trở lên: danh sách dọc theo nhóm, mục đang mở đánh dấu `aria-current="page"`.
 * Điện thoại: một ô chọn ở đầu trang, mục xếp theo nhóm — thanh bên dọc chiếm hết bề ngang thì nội dung bị đẩy
 * xuống dưới cả chục dòng menu.
 */
export function ProfileSettingsNav({ groups, active, onSelect, badges, className }: ProfileSettingsNavProps) {
  return (
    <div className={className}>
      <div className="md:hidden">
        <Select value={active} onValueChange={(value) => onSelect(value as ProfileSectionKey)}>
          <SelectTrigger aria-label="Chọn mục trang cá nhân" className="w-full">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            {groups.map((group) => (
              <SelectGroup key={group.key}>
                <SelectLabel>{group.label}</SelectLabel>
                {group.sections.map((section) => {
                  const badge = badges?.[section.key]
                  return (
                    <SelectItem key={section.key} value={section.key}>
                      {section.label}
                      {badge && badge.count > 0 ? ` (${badge.count})` : ''}
                    </SelectItem>
                  )
                })}
              </SelectGroup>
            ))}
          </SelectContent>
        </Select>
      </div>

      <nav aria-label="Các mục trang cá nhân" className="hidden space-y-3 md:block">
        {groups.map((group) => (
          <ProfileNavGroup
            key={group.key}
            group={group}
            active={active}
            onSelect={onSelect}
            badges={badges}
          />
        ))}
      </nav>
    </div>
  )
}

interface ProfileNavGroupProps {
  group: ProfileGroupDefinition
  active: ProfileSectionKey
  onSelect: (key: ProfileSectionKey) => void
  badges?: Partial<Record<ProfileSectionKey, ProfileSectionBadge>>
}

/**
 * Một NHÓM của thanh bên, gập / mở được bằng tiêu đề (duoc-CR-774): mở là mũi tên lên, gập là mũi tên xuống; nhớ theo
 * nhóm (`erp.section.me.nav.<khóa nhóm>`).
 *
 * ⚠️ Nhóm chứa mục ĐANG MỞ luôn mở, bất kể đã gập: mở trang bằng `?tab=` vào một mục nằm trong nhóm đã gập mà nhóm vẫn
 * gập thì không còn chỗ nào trên thanh bên cho biết mình đang ở đâu.
 *
 * ⚠️ Gập rồi thì số đếm của các mục bên trong (việc cần làm, thông báo chưa đọc) gộp lên tiêu đề nhóm — gập không được
 * làm mất tín hiệu có việc chờ.
 */
function ProfileNavGroup({ group, active, onSelect, badges }: ProfileNavGroupProps) {
  const storageKey = `me.nav.${group.key}`
  const [saved, setSaved] = useState<boolean | null>(() => readSectionOpen(storageKey))
  const holdsActive = group.sections.some((section) => section.key === active)
  const open = holdsActive || (saved ?? true)
  const Chevron = open ? ChevronUp : ChevronDown

  const hiddenBadges = group.sections.map((section) => badges?.[section.key]).filter((b) => b && b.count > 0)
  const hiddenCount = hiddenBadges.reduce((sum, b) => sum + (b?.count ?? 0), 0)
  const hiddenVariant = hiddenBadges.some((b) => b?.variant === 'destructive') ? 'destructive' : 'secondary'

  function toggle() {
    const next = !open
    writeSectionOpen(storageKey, next)
    setSaved(next)
  }

  return (
    <div className="space-y-1">
      <button
        type="button"
        aria-expanded={open}
        //  Nhóm chứa mục đang mở không gập được — tắt nút cho khỏi bấm mà không thấy gì xảy ra.
        disabled={holdsActive}
        onClick={toggle}
        className="flex w-full items-center gap-2 rounded-md px-2 py-1 text-left text-xs font-semibold tracking-wide text-muted-foreground uppercase transition-colors hover:bg-accent/60 disabled:cursor-default disabled:hover:bg-transparent"
      >
        <span className="min-w-0 flex-1 truncate">{group.label}</span>
        {!open && hiddenCount > 0 && (
          <Badge variant={hiddenVariant} className="h-4 px-1.5 text-[10px] normal-case">
            {hiddenCount}
          </Badge>
        )}
        <Chevron className={cn('size-3.5 shrink-0', holdsActive && 'opacity-40')} aria-hidden="true" />
      </button>
      <ul hidden={!open} className="space-y-0.5">
        {group.sections.map((section) => {
          const Icon = section.icon
          const isActive = section.key === active
          const badge = badges?.[section.key]
          return (
            <li key={section.key}>
              <button
                type="button"
                aria-current={isActive ? 'page' : undefined}
                onClick={() => onSelect(section.key)}
                className={cn(
                  'flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-sm transition-colors',
                  'hover:bg-accent hover:text-accent-foreground focus-visible:ring-2 focus-visible:ring-ring focus-visible:outline-none',
                  isActive ? 'bg-accent font-medium text-accent-foreground' : 'text-muted-foreground',
                )}
              >
                <Icon className="size-4 shrink-0" />
                <span className="min-w-0 flex-1 truncate">{section.label}</span>
                {badge && badge.count > 0 && (
                  <Badge variant={badge.variant} className="h-4 px-1.5 text-[10px]">
                    {badge.count}
                  </Badge>
                )}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
