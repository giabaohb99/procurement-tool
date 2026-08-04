import { RefObject, useEffect, useState } from 'react'

// Sinh mục lục từ heading (h1/h2/h3) trong nội dung HTML đã render, kèm theo dõi
// heading đang xem để tô sáng mục tương ứng ở sidebar.

export interface TocItem {
  id: string
  text: string
  level: number
}

/** Khoảng chừa cho header dính (sticky) khi tính heading đang xem / khi cuộn tới. */
const SCROLL_OFFSET = 96

export function useHeadingToc(
  contentRef: RefObject<HTMLElement>,
  deps: unknown[],
  enabled = true,
) {
  const [items, setItems] = useState<TocItem[]>([])
  const [activeId, setActiveId] = useState<string>('')

  useEffect(() => {
    if (!enabled || !contentRef.current) {
      setItems([])
      return
    }
    const headings = Array.from(contentRef.current.querySelectorAll('h1, h2, h3'))
    setItems(
      headings.map((heading, index) => {
        if (!heading.id) heading.id = `hc-heading-${index}`
        return {
          id: heading.id,
          text: heading.textContent || '',
          level: parseInt(heading.tagName.substring(1), 10),
        }
      }),
    )
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [enabled, ...deps])

  // Heading gần nhất đã cuộn qua = mục đang xem
  useEffect(() => {
    if (items.length === 0) return

    const onScroll = () => {
      let current = items[0].id
      for (const item of items) {
        const el = document.getElementById(item.id)
        if (el && el.getBoundingClientRect().top <= SCROLL_OFFSET + 8) current = item.id
      }
      setActiveId(current)
    }

    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [items])

  return { items, activeId }
}

/** Cuộn mượt tới heading, chừa chỗ cho header dính. */
export function scrollToHeading(e: React.MouseEvent, id: string) {
  e.preventDefault()
  const el = document.getElementById(id)
  if (!el) return
  window.scrollTo({ top: el.getBoundingClientRect().top + window.scrollY - SCROLL_OFFSET, behavior: 'smooth' })
}
