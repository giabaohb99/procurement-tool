import { useCallback, useRef, useState } from 'react'

import type { MentionPerson } from './serialize-mention-body'

/** Vùng chữ `@abc` đang gõ dở — giữ để lúc chọn người thì thay đúng đoạn đó. */
export interface MentionRange {
  node: Text
  start: number
  end: number
}

/**
 * Phần "đang gõ @ thì gợi ý ai" — tách khỏi ô soạn thảo để chỗ đó chỉ còn lo
 * chuyện con trỏ và DOM.
 */
export function useMentionSuggestions(search: (query: string) => Promise<MentionPerson[]>) {
  const [people, setPeople] = useState<MentionPerson[]>([])
  const [activeIndex, setActiveIndex] = useState(0)
  const [searching, setSearching] = useState(false)
  const rangeRef = useRef<MentionRange | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  /** Từ khóa của lần tìm gần nhất — trùng thì KHÔNG tìm lại, để dòng đang chọn đứng yên. */
  const lastQueryRef = useRef<string | null>(null)

  const close = useCallback(() => {
    rangeRef.current = null
    lastQueryRef.current = null
    if (timerRef.current) clearTimeout(timerRef.current)
    setPeople([])
    setSearching(false)
    setActiveIndex(0)
  }, [])

  /** Gọi sau mỗi lần gõ / di con trỏ: xem con trỏ có đứng sau một cụm `@...` không. */
  const scan = useCallback(
    (root: HTMLElement | null) => {
      const selection = window.getSelection()
      const node = selection?.anchorNode
      if (!selection || !node || node.nodeType !== Node.TEXT_NODE || !root?.contains(node)) {
        close()
        return
      }

      const text = node as Text
      const before = (text.textContent || '').slice(0, selection.anchorOffset)
      // `@` phải đứng đầu dòng hoặc sau khoảng trắng — tránh bắt nhầm trong email.
      const match = /(^|[\s ])@([^\s @]{0,30})$/.exec(before)
      if (!match) {
        close()
        return
      }

      rangeRef.current = {
        node: text,
        start: selection.anchorOffset - match[2].length - 1,
        end: selection.anchorOffset,
      }

      const query = match[2]
      if (lastQueryRef.current === query) return
      lastQueryRef.current = query

      setSearching(true)
      if (timerRef.current) clearTimeout(timerRef.current)
      timerRef.current = setTimeout(async () => {
        try {
          const found = await search(query)
          // Người dùng có thể đã gõ tiếp / đóng menu trong lúc chờ mạng.
          if (rangeRef.current) {
            setPeople(found)
            setActiveIndex(0)
          }
        } catch {
          setPeople([])
        } finally {
          setSearching(false)
        }
      }, 180)
    },
    [close, search],
  )

  const move = useCallback((step: number) => {
    setPeople((current) => {
      setActiveIndex((index) => (index + step + current.length) % (current.length || 1))
      return current
    })
  }, [])

  return { people, activeIndex, searching, rangeRef, scan, close, move, setActiveIndex }
}
