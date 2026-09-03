import { ArrowLeft, ChevronLeft, ChevronRight, Lock, MessagesSquare, Pin, SquarePen } from 'lucide-react'
import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import { BoardIcon } from '../components/board-icon'
import { PostComposerDialog } from '../components/post-composer-dialog'
import { ThreadPrefixChip } from '../components/thread-prefix-chip'
import { useBoardThreads } from '../hooks/use-board-threads'
import type { ForumPost } from '../types/forum-post'
import { authorInitials } from '../utils/author-initials'

/**
 * Màn thread của một box (F13b, QĐ-D7): mỗi dòng là chip prefix + tiêu đề +
 * tác giả + số bình luận + hoạt động cuối; thread ghim đứng đầu (backend sắp),
 * phân trang SỐ TRANG kiểu VOZ — số trang nằm trên URL (`?page=`) để back/share
 * giữ đúng trang.
 */
export function ForumBoardThreadsPage() {
  const { id } = useParams()
  const boardId = Number(id)
  const [searchParams, setSearchParams] = useSearchParams()
  const page = Math.max(1, Number(searchParams.get('page')) || 1)
  const threads = useBoardThreads(boardId, page)
  const [composerOpen, setComposerOpen] = useState(false)

  function goToPage(next: number) {
    setSearchParams(next <= 1 ? {} : { page: String(next) })
    window.scrollTo({ top: 0 })
  }

  const board = threads.data?.board

  return (
    <div className="pt-3">
      <div className="mb-2 px-4 sm:px-0">
        <Link
          to={appRoutes.forum.boards}
          className="inline-flex items-center gap-1.5 text-sm text-muted-foreground hover:text-foreground"
        >
          <ArrowLeft className="size-4" />
          Diễn đàn
        </Link>
      </div>

      {threads.isPending && (
        <div className="border-y border-border bg-card p-4 shadow-sm sm:rounded-xl sm:border">
          <div className="flex items-center gap-3">
            <Skeleton className="size-10 rounded-lg" />
            <div className="space-y-1.5">
              <Skeleton className="h-4 w-40" />
              <Skeleton className="h-3 w-56" />
            </div>
          </div>
          <div className="mt-4 space-y-3">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-10 w-full" />
            ))}
          </div>
        </div>
      )}

      {threads.isError && (
        <div className="flex flex-col items-center gap-3 py-16 text-center">
          <Lock className="size-10 text-muted-foreground opacity-40" aria-hidden />
          <p className="text-sm text-muted-foreground">Box không tồn tại hoặc đã ẩn.</p>
          <Button asChild variant="outline">
            <Link to={appRoutes.forum.boards}>Về danh sách chuyên mục</Link>
          </Button>
        </div>
      )}

      {threads.data && board && (
        <div className="space-y-3">
          <div className="flex items-center gap-3 border-y border-border bg-card px-4 py-3 shadow-sm sm:rounded-xl sm:border">
            <BoardIcon icon={board.icon} />
            <div className="min-w-0 flex-1">
              <h1 className="truncate text-base font-semibold">{board.name}</h1>
              {board.description && (
                <p className="truncate text-xs text-muted-foreground">{board.description}</p>
              )}
            </div>
            <Button size="sm" className="shrink-0" onClick={() => setComposerOpen(true)}>
              <SquarePen className="size-4" />
              Tạo chủ đề
            </Button>
          </div>

          {threads.data.items.length === 0 ? (
            <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
              <MessagesSquare className="size-10 opacity-40" aria-hidden />
              <p className="text-sm">Chưa có chủ đề nào. Hãy tạo chủ đề đầu tiên.</p>
            </div>
          ) : (
            <div
              className={cn(
                'divide-y divide-border/70 border-y border-border bg-card shadow-sm sm:rounded-xl sm:border',
                threads.isPlaceholderData && 'opacity-60',
              )}
            >
              {threads.data.items.map((thread) => (
                <ThreadRow key={thread.id} thread={thread} />
              ))}
            </div>
          )}

          <ThreadPagination
            page={threads.data.page}
            totalPages={Math.max(1, Math.ceil(threads.data.total / threads.data.per_page))}
            onChange={goToPage}
          />
        </div>
      )}

      {board && (
        <PostComposerDialog
          open={composerOpen}
          onOpenChange={setComposerOpen}
          board={{ id: board.id, name: board.name }}
        />
      )}
    </div>
  )
}

/** Một dòng thread — cả dòng là link vào trang bài viết. */
function ThreadRow({ thread }: { thread: ForumPost }) {
  const lastActivity = thread.last_activity_at || thread.created_at
  return (
    <Link
      to={appRoutes.forum.postDetail(thread.id)}
      className="group flex items-center gap-3 px-4 py-2.5"
    >
      <Avatar className="size-8 shrink-0">
        <AvatarImage className="object-cover" src={thread.author_avatar} alt={thread.author_name} />
        <AvatarFallback className="bg-navy-solid text-xs font-semibold text-white">
          {authorInitials(thread.author_name)}
        </AvatarFallback>
      </Avatar>
      <div className="min-w-0 flex-1">
        <p className="flex items-center gap-1.5 text-sm">
          {thread.pinned_at != null && (
            <Pin className="size-3.5 shrink-0 text-blue-600" aria-label="Chủ đề ghim" />
          )}
          <ThreadPrefixChip prefix={thread.prefix} />
          <span className="truncate font-medium group-hover:underline">{thread.title}</span>
        </p>
        <p
          className="truncate text-xs text-muted-foreground"
          title={formatDateTime(lastActivity)}
        >
          {thread.author_name} · {thread.comment_count} bình luận · {formatRelativeTime(lastActivity)}
        </p>
      </div>
    </Link>
  )
}

/** Dải số trang kiểu VOZ: cửa sổ quanh trang hiện tại + trang đầu/cuối. */
function ThreadPagination({
  page,
  totalPages,
  onChange,
}: {
  page: number
  totalPages: number
  onChange: (page: number) => void
}) {
  if (totalPages <= 1) return null
  return (
    <nav aria-label="Phân trang chủ đề" className="flex items-center justify-center gap-1 pb-2">
      <Button
        variant="ghost"
        size="icon"
        className="size-8"
        disabled={page <= 1}
        aria-label="Trang trước"
        onClick={() => onChange(page - 1)}
      >
        <ChevronLeft className="size-4" />
      </Button>
      {buildPageItems(page, totalPages).map((item, index) =>
        item === 'gap' ? (
          <span key={`gap-${index}`} className="px-1 text-sm text-muted-foreground" aria-hidden>
            …
          </span>
        ) : (
          <Button
            key={item}
            variant={item === page ? 'default' : 'ghost'}
            size="icon"
            className="size-8 text-sm"
            aria-current={item === page ? 'page' : undefined}
            onClick={() => onChange(item)}
          >
            {item}
          </Button>
        ),
      )}
      <Button
        variant="ghost"
        size="icon"
        className="size-8"
        disabled={page >= totalPages}
        aria-label="Trang sau"
        onClick={() => onChange(page + 1)}
      >
        <ChevronRight className="size-4" />
      </Button>
    </nav>
  )
}

/** 1 … (page-1) page (page+1) … cuối — đủ nhảy thẳng mà không tràn mobile. */
function buildPageItems(page: number, totalPages: number): (number | 'gap')[] {
  const wanted = new Set([1, page - 1, page, page + 1, totalPages])
  const items: (number | 'gap')[] = []
  let previous = 0
  for (let n = 1; n <= totalPages; n += 1) {
    if (!wanted.has(n)) continue
    if (previous && n - previous > 1) items.push('gap')
    items.push(n)
    previous = n
  }
  return items
}
