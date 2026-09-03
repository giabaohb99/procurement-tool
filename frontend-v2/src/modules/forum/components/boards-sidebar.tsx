import { Clock3, Flame, Pin } from 'lucide-react'
import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'

import { appRoutes } from '@/shared/constants/app-routes'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatRelativeTime } from '@/shared/utils/format-date'

import { useBoardHighlights } from '../hooks/use-board-highlights'
import { usePinnedPosts } from '../hooks/use-pinned-posts'
import type { ForumThreadSummary } from '../types/forum-board'
import { FORUM_BODY_FORMAT } from '../types/forum-post'
import type { ForumPost } from '../types/forum-post'
import { stripRichBodyText } from '../utils/rich-body'
import { ThreadPrefixChip } from './thread-prefix-chip'

/**
 * Sidebar phải màn «Diễn đàn» (F13c, chốt 03/09/2026 theo màn hình VOZ):
 * «Nổi bật» = bài đang ghim (admin quyết, API bài ghim sẵn có) · «Đang sôi
 * nổi» = top thread theo bình luận + reaction 7 ngày (máy tự xếp) · «Mới
 * nhất» = thread mới toàn diễn đàn. Chỉ hiện desktop màn rộng; mobile giấu
 * sidebar và DỒN riêng khối «Nổi bật» lên đầu trang (`PinnedSpotlight`).
 */
export function BoardsSidebar({ className }: { className?: string }) {
  const pinned = usePinnedPosts()
  const highlights = useBoardHighlights()

  if (pinned.isPending || highlights.isPending) {
    return (
      <aside className={cn('space-y-3', className)}>
        <div className="rounded-xl border border-border bg-card p-3 shadow-sm">
          <Skeleton className="h-3.5 w-24" />
          <div className="mt-3 space-y-2">
            {[0, 1, 2].map((i) => (
              <Skeleton key={i} className="h-3 w-full" />
            ))}
          </div>
        </div>
      </aside>
    )
  }

  const pinnedPosts = pinned.data ?? []
  const trending = highlights.data?.trending ?? []
  const latest = highlights.data?.latest ?? []
  //  Sidebar là khối phụ trợ — lỗi tải thì lặng lẽ vắng mặt, không chen toast
  //  vào giữa màn danh sách box đang hiển thị bình thường.
  if (!pinnedPosts.length && !trending.length && !latest.length) return null

  return (
    <aside className={cn('space-y-3', className)}>
      {pinnedPosts.length > 0 && (
        <SidebarCard icon={Pin} title="Nổi bật">
          {pinnedPosts.map((post) => (
            <PinnedRow key={post.id} post={post} />
          ))}
        </SidebarCard>
      )}

      {trending.length > 0 && (
        <SidebarCard icon={Flame} title="Đang sôi nổi">
          {trending.map((thread) => (
            <ThreadRow
              key={thread.id}
              thread={thread}
              meta={`${thread.board_name} · ${thread.comment_count} bình luận`}
            />
          ))}
        </SidebarCard>
      )}

      {latest.length > 0 && (
        <SidebarCard icon={Clock3} title="Mới nhất">
          {latest.map((thread) => (
            <ThreadRow
              key={thread.id}
              thread={thread}
              meta={`${thread.board_name} · ${formatRelativeTime(thread.created_at)}`}
            />
          ))}
        </SidebarCard>
      )}
    </aside>
  )
}

/**
 * Khối «Nổi bật» phiên bản MOBILE — đứng đầu trang khi sidebar bị giấu
 * (`lg:hidden` do trang cài). Cùng nguồn `usePinnedPosts` nên không gọi thêm
 * API: TanStack Query gộp theo khóa với khối trong sidebar.
 */
export function PinnedSpotlight({ className }: { className?: string }) {
  const pinned = usePinnedPosts()
  const posts = pinned.data ?? []
  if (!posts.length) return null
  return (
    <div className={className}>
      <SidebarCard icon={Pin} title="Nổi bật" flat>
        {posts.map((post) => (
          <PinnedRow key={post.id} post={post} />
        ))}
      </SidebarCard>
    </div>
  )
}

function SidebarCard({
  icon: Icon,
  title,
  flat,
  children,
}: {
  icon: LucideIcon
  title: string
  /** Bản mobile đầu trang: viền trên-dưới sát mép như các thẻ khác của feed. */
  flat?: boolean
  children: React.ReactNode
}) {
  return (
    <section
      aria-label={title}
      className={cn(
        'bg-card p-3 shadow-sm',
        flat
          ? 'border-y border-border sm:rounded-xl sm:border'
          : 'rounded-xl border border-border',
      )}
    >
      <h3 className="flex items-center gap-1.5 text-xs font-semibold tracking-wide text-muted-foreground uppercase">
        <Icon className="size-3.5" aria-hidden />
        {title}
      </h3>
      <ul className="mt-2 space-y-2">{children}</ul>
    </section>
  )
}

/** Bài ghim có thể là bài feed không tiêu đề — rơi về dòng đầu của nội dung.
 * Bài rich (CR-261) phải bóc thẻ trước, không thì nhãn hiện `<p>xin chào...`. */
function PinnedRow({ post }: { post: ForumPost }) {
  const label =
    post.title ||
    (post.body_format === FORUM_BODY_FORMAT.richHtml ? stripRichBodyText(post.body) : post.body)
  return (
    <li>
      <Link
        to={appRoutes.forum.postDetail(post.id)}
        className="block text-sm leading-snug hover:underline"
      >
        <span className="line-clamp-2">{label}</span>
      </Link>
    </li>
  )
}

function ThreadRow({ thread, meta }: { thread: ForumThreadSummary; meta: string }) {
  return (
    <li className="min-w-0">
      <Link
        to={appRoutes.forum.postDetail(thread.id)}
        className="block text-sm leading-snug hover:underline"
      >
        {/*  Chip nằm TRONG span bọc line-clamp — đứng ngoài thì line-clamp
            (display -webkit-box) đẩy tiêu đề rơi xuống dòng riêng. */}
        <span className="line-clamp-2">
          {thread.prefix > 0 && <ThreadPrefixChip prefix={thread.prefix} className="mr-1" />}
          {thread.title}
        </span>
      </Link>
      <p className="truncate text-[11px] text-muted-foreground">{meta}</p>
    </li>
  )
}
