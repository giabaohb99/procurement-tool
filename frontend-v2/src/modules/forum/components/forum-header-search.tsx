import { useState } from 'react'
import type { KeyboardEvent } from 'react'
import { Loader2, Search, SlidersHorizontal } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Input } from '@/shared/ui/input'
import { cn } from '@/shared/utils/cn'

import {
  QUICK_SEARCH_MIN_CHARS,
  useForumQuickSearch,
} from '../hooks/use-forum-quick-search'
import { FORUM_BODY_FORMAT } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { stripRichBodyText } from '../utils/rich-body'

/** Nhãn một dòng cho bài trong dropdown — thread lấy tiêu đề, bài feed lấy thân. */
function quickResultLabel(post: ForumPost): string {
  if (post.title) return post.title
  return post.body_format === FORUM_BODY_FORMAT.richHtml
    ? stripRichBodyText(post.body)
    : post.body
}

/**
 * Ô tìm trên header Diễn đàn (bao-CR-272 + bao-CR-273.1): gõ đủ 2 ký tự là sổ
 * top 5 bài khớp ngay dưới ô — bấm bài nào nhảy thẳng bài đó; Enter, «Xem tất
 * cả» hay «Bộ lọc nâng cao» mới qua trang Tìm bài đầy đủ (kèm `?q=` tự chạy).
 */
export function ForumHeaderSearch({ className }: { className?: string }) {
  const navigate = useNavigate()
  const [q, setQ] = useState('')
  const [focused, setFocused] = useState(false)
  //  -1 = chưa trỏ vào bài nào → Enter đi trang Tìm bài; mũi tên xuống/lên đổi.
  const [activeIndex, setActiveIndex] = useState(-1)

  const keyword = q.trim()
  const open = focused && keyword.length >= QUICK_SEARCH_MIN_CHARS
  const quick = useForumQuickSearch(q, open)
  const items = quick.data?.items ?? []
  const total = quick.data?.total ?? 0

  /** Về trang Tìm bài đầy đủ kèm từ khóa (trang đó nhận `?q=` là chạy luôn). */
  function goFullSearch() {
    setFocused(false)
    navigate(
      keyword
        ? `${appRoutes.forum.search}?q=${encodeURIComponent(keyword)}`
        : appRoutes.forum.search,
    )
  }

  function openPost(id: number) {
    setFocused(false)
    navigate(appRoutes.forum.postDetail(id))
  }

  function submit(event: React.FormEvent) {
    event.preventDefault()
    const picked = activeIndex >= 0 ? items[activeIndex] : undefined
    if (picked) openPost(picked.id)
    else goFullSearch()
  }

  function onKeyDown(event: KeyboardEvent<HTMLInputElement>) {
    if (!open) return
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setActiveIndex((i) => Math.min(i + 1, items.length - 1))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActiveIndex((i) => Math.max(i - 1, -1))
    } else if (event.key === 'Escape') {
      setFocused(false)
    }
  }

  return (
    <div
      className={cn('relative', className)}
      onFocus={() => setFocused(true)}
      //  Focus chạy sang phần tử NGOÀI cụm này mới đóng — bấm nút trong dropdown
      //  cũng là một lần blur input, đóng ngay thì click không kịp ăn.
      onBlur={(event) => {
        if (!event.currentTarget.contains(event.relatedTarget)) setFocused(false)
      }}
    >
      <form onSubmit={submit} className="relative">
        <Search
          className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground"
          aria-hidden
        />
        <Input
          value={q}
          onChange={(event) => {
            setQ(event.target.value)
            setActiveIndex(-1)
          }}
          onKeyDown={onKeyDown}
          placeholder="Tìm bài viết..."
          maxLength={255}
          className="h-9 w-44 rounded-full bg-muted/60 pl-8 lg:w-72"
          aria-label="Tìm bài viết"
          autoComplete="off"
        />
        {/* Nút submit ẨN — không có nó, một số trình duyệt bỏ qua Enter
            (implicit submission), gõ xong bấm Enter mà trang đứng im. */}
        <button type="submit" className="sr-only">
          Tìm
        </button>
      </form>

      {open ? (
        <div className="absolute top-full right-0 z-20 mt-1.5 w-80 overflow-hidden rounded-lg border border-border bg-background shadow-lg lg:w-96">
          {quick.isPending ? (
            <p className="flex items-center gap-2 px-3 py-3 text-sm text-muted-foreground">
              <Loader2 className="size-4 animate-spin" aria-hidden />
              Đang tìm...
            </p>
          ) : items.length === 0 ? (
            <p className="px-3 py-3 text-sm text-muted-foreground">
              Không có bài viết nào khớp.
            </p>
          ) : (
            <ul>
              {items.map((post, index) => (
                <li key={post.id}>
                  <button
                    type="button"
                    onClick={() => openPost(post.id)}
                    onMouseEnter={() => setActiveIndex(index)}
                    className={cn(
                      'block w-full px-3 py-2 text-left',
                      index === activeIndex && 'bg-accent',
                    )}
                  >
                    <span className="line-clamp-1 text-sm font-medium text-foreground">
                      {quickResultLabel(post)}
                    </span>
                    <span className="line-clamp-1 text-xs text-muted-foreground">
                      {post.author_name}
                      {post.board_name ? ` · ${post.board_name}` : ''}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}

          <div className="flex items-center justify-between border-t border-border bg-muted/40 px-1.5 py-1">
            {total > 0 ? (
              <button
                type="button"
                onClick={goFullSearch}
                className="rounded-md px-1.5 py-1 text-sm font-medium text-blue-600 hover:bg-accent"
              >
                Xem tất cả {total} kết quả
              </button>
            ) : (
              <span aria-hidden />
            )}
            <button
              type="button"
              onClick={goFullSearch}
              className="flex items-center gap-1 rounded-md px-1.5 py-1 text-xs text-muted-foreground hover:bg-accent hover:text-foreground"
            >
              <SlidersHorizontal className="size-3.5" aria-hidden />
              Bộ lọc nâng cao
            </button>
          </div>
        </div>
      ) : null}
    </div>
  )
}
