import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { cn } from '@/shared/utils/cn'
import { nameInitial, type MentionPerson } from './serialize-mention-body'

interface MentionSuggestionListProps {
  people: MentionPerson[]
  activeIndex: number
  searching: boolean
  onHover: (index: number) => void
  onPick: (person: MentionPerson) => void
}

/** Menu gợi ý người để `@`, bung ngay dưới ô soạn thảo. */
export function MentionSuggestionList({
  people,
  activeIndex,
  searching,
  onHover,
  onPick,
}: MentionSuggestionListProps) {
  if (!people.length && !searching) return null

  return (
    <div className="absolute left-0 top-full z-30 mt-1 max-h-64 w-80 max-w-full overflow-y-auto rounded-lg border bg-popover py-1 shadow-md">
      {!people.length ? (
        <p className="px-3 py-2 text-sm text-muted-foreground">Đang tìm…</p>
      ) : (
        people.map((person, index) => (
          <button
            key={person.user_id}
            type="button"
            // `mousedown` chứ không phải `click`: ô soạn thảo mất focus trước khi
            // click kịp chạy, chặn ở đây thì con trỏ ở lại đúng chỗ đang gõ.
            onMouseDown={(event) => {
              event.preventDefault()
              onPick(person)
            }}
            onMouseEnter={() => onHover(index)}
            className={cn(
              'flex w-full items-center gap-2 border-l-2 border-transparent px-3 py-1.5 text-left',
              index === activeIndex && 'border-primary bg-accent',
            )}
          >
            <Avatar size="sm">
              <AvatarImage src={person.avatar} alt={person.name} />
              <AvatarFallback>{nameInitial(person.name)}</AvatarFallback>
            </Avatar>
            <span className="truncate text-sm font-medium">{person.name}</span>
            {!!person.code && (
              <span className="shrink-0 text-xs text-muted-foreground">{person.code}</span>
            )}
            {person.related && (
              <span className="ml-auto shrink-0 rounded-full bg-primary/10 px-2 py-0.5 text-[11px] text-primary">
                trong phiếu
              </span>
            )}
          </button>
        ))
      )}
    </div>
  )
}
