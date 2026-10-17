import type { ProfileGroupDefinition, ProfileSectionKey } from '@/app/components/profile/profile-sections'
import { Badge } from '@/shared/ui/badge'
import { Select, SelectContent, SelectGroup, SelectItem, SelectLabel, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'

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

      <nav aria-label="Các mục trang cá nhân" className="hidden space-y-5 md:block">
        {groups.map((group) => (
          <div key={group.key} className="space-y-1">
            <p className="px-2 text-xs font-semibold tracking-wide text-muted-foreground uppercase">{group.label}</p>
            <ul className="space-y-0.5">
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
        ))}
      </nav>
    </div>
  )
}
