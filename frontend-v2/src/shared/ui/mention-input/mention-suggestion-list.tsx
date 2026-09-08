import { useLayoutEffect, useRef, useState } from 'react'

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

/** Khoảng thở giữa bảng gợi ý và mép khung nhìn. */
const EDGE_GAP = 8

/**
 * Menu gợi ý người để `@` — bung DƯỚI ô soạn, tự LẬT LÊN khi dưới không đủ chỗ.
 *
 * Phải tự lật vì ô soạn không phải lúc nào cũng ở giữa trang: panel chi tiết
 * việc của phân hệ Dự án ghim ô soạn sát ĐÁY màn hình, nên "bung xuống dưới" là
 * rơi hẳn ra ngoài khung nhìn — gõ `@` xong không thấy ai để chọn (khách báo
 * 03/09/2026). Ở những chỗ còn rộng chỗ bên dưới thì không đổi gì.
 */
export function MentionSuggestionList({
  people,
  activeIndex,
  searching,
  onHover,
  onPick,
}: MentionSuggestionListProps) {
  const boxRef = useRef<HTMLDivElement>(null)
  const [flip, setFlip] = useState(false)

  /*  Đo theo Ô NEO (`offsetParent` — chính khung `relative` bọc ô soạn), KHÔNG
      theo vị trí hiện tại của bảng: đo chính nó thì lật xong vị trí đổi, lần đo
      sau lại ra kết luận ngược và bảng nhấp nháy qua lại không dừng.  */
  useLayoutEffect(() => {
    const box = boxRef.current
    const anchor = box?.offsetParent
    if (!box || !(anchor instanceof HTMLElement)) return
    const rect = anchor.getBoundingClientRect()
    const choDuoi = window.innerHeight - rect.bottom
    const choTren = rect.top
    setFlip(choDuoi < box.offsetHeight + EDGE_GAP && choTren > choDuoi)
  }, [people.length, searching])

  if (!people.length && !searching) return null

  return (
    <div
      ref={boxRef}
      className={cn(
        'absolute left-0 z-30 max-h-64 w-80 max-w-full overflow-y-auto rounded-lg border bg-popover py-1 shadow-md',
        flip ? 'bottom-full mb-1' : 'top-full mt-1',
      )}
    >
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
