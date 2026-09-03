import { EyeOff, Library, RefreshCw } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Avatar, AvatarFallback, AvatarImage } from '@/shared/ui/avatar'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Skeleton } from '@/shared/ui/skeleton'
import { formatDateTime, formatRelativeTime } from '@/shared/utils/format-date'

import { BoardIcon } from '../components/board-icon'
import { BoardsSidebar, PinnedSpotlight } from '../components/boards-sidebar'
import { ThreadPrefixChip } from '../components/thread-prefix-chip'
import { FORUM_BOARD_STATUS } from '../types/forum-board'
import type { ForumBoardNode } from '../types/forum-board'
import { authorInitials } from '../utils/author-initials'
import { useForumBoards } from '../hooks/use-forum-boards'

/**
 * Tab «Diễn đàn» (F13b, QĐ-D7) — danh sách box gom theo nhóm kiểu VOZ: mỗi
 * dòng box có icon + tên + mô tả + bộ đếm gọn, kèm khối bài-mới-nhất bấm
 * được bên phải (mobile giấu khối này, giữ số đếm). Số đếm ghi THẲNG con số,
 * không format 1K+ — chốt trong spec F13b.
 */
export function ForumBoardsPage() {
  const boards = useForumBoards()

  if (boards.isPending) {
    return (
      <div className="space-y-3 pt-3">
        {[0, 1].map((i) => (
          <div key={i} className="border-y border-border bg-card p-4 shadow-sm sm:rounded-xl sm:border">
            <Skeleton className="h-4 w-32" />
            <div className="mt-4 space-y-4">
              {[0, 1, 2].map((j) => (
                <div key={j} className="flex items-center gap-3">
                  <Skeleton className="size-10 rounded-lg" />
                  <div className="flex-1 space-y-1.5">
                    <Skeleton className="h-3.5 w-40" />
                    <Skeleton className="h-3 w-56" />
                  </div>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>
    )
  }

  if (boards.isError) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center">
        <p className="text-sm text-muted-foreground">
          Không tải được danh sách chuyên mục. Kiểm tra kết nối rồi thử lại.
        </p>
        <Button variant="outline" onClick={() => void boards.refetch()}>
          <RefreshCw className="size-4" />
          Thử lại
        </Button>
      </div>
    )
  }

  const groups = boards.data ?? []

  if (groups.length === 0) {
    return (
      <div className="flex flex-col items-center gap-3 py-16 text-center text-muted-foreground">
        <Library className="size-10 opacity-40" aria-hidden />
        <p className="text-sm">Chưa có chuyên mục nào — quản trị viên diễn đàn sẽ mở box sau.</p>
      </div>
    )
  }

  return (
    //  F13c: desktop rộng chia 2 cột (danh sách box + sidebar 300px); mobile
    //  giấu sidebar, riêng khối «Nổi bật» dồn lên đầu trang (PinnedSpotlight).
    <div className="pt-3 lg:grid lg:grid-cols-[minmax(0,1fr)_300px] lg:items-start lg:gap-4">
      <div className="space-y-4">
        <PinnedSpotlight className="lg:hidden" />
        {groups.map((group) => (
          <section key={group.id} aria-label={group.name}>
            <div className="flex items-center gap-2 px-4 pb-1.5 sm:px-1">
              <h2 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">
                {group.name}
              </h2>
              {group.status === FORUM_BOARD_STATUS.hidden && <HiddenBadge />}
            </div>
            <div className="divide-y divide-border/70 border-y border-border bg-card shadow-sm sm:rounded-xl sm:border">
              {group.children.length === 0 ? (
                <p className="px-4 py-4 text-sm text-muted-foreground">
                  Chưa có box nào trong nhóm này.
                </p>
              ) : (
                group.children.map((box) => <BoardRow key={box.id} box={box} />)
              )}
            </div>
          </section>
        ))}
      </div>
      <BoardsSidebar className="hidden lg:block" />
    </div>
  )
}

/** Một dòng box: trái = link vào box (icon · tên · mô tả · số đếm), phải =
 * khối bài-mới-nhất link thẳng vào thread — hai link TÁCH NHAU, không lồng. */
function BoardRow({ box }: { box: ForumBoardNode }) {
  const last = box.last_post
  return (
    <div className="flex items-center gap-3 px-4 py-3">
      <Link
        to={appRoutes.forum.boardDetail(box.id)}
        className="group flex min-w-0 flex-1 items-center gap-3"
      >
        <BoardIcon icon={box.icon} />
        <div className="min-w-0">
          <p className="truncate text-sm font-semibold group-hover:underline">
            {box.name}
            {box.status === FORUM_BOARD_STATUS.hidden && <HiddenBadge className="ml-1.5" />}
          </p>
          {box.description && (
            <p className="truncate text-xs text-muted-foreground">{box.description}</p>
          )}
          <p className="mt-0.5 text-xs text-muted-foreground">
            {box.thread_count} chủ đề · {box.comment_count} bình luận
          </p>
        </div>
      </Link>

      {last && (
        <Link
          to={appRoutes.forum.postDetail(last.post_id)}
          className="group hidden w-52 shrink-0 items-center gap-2 sm:flex"
          title={formatDateTime(last.last_at)}
        >
          <Avatar className="size-8">
            <AvatarImage
              className="object-cover"
              src={last.last_author_avatar}
              alt={last.last_author_name}
            />
            <AvatarFallback className="bg-navy-solid text-xs font-semibold text-white">
              {authorInitials(last.last_author_name)}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0">
            <p className="flex items-center gap-1 text-xs font-medium">
              <ThreadPrefixChip prefix={last.prefix} />
              <span className="truncate group-hover:underline">{last.title}</span>
            </p>
            <p className="truncate text-[11px] text-muted-foreground">
              {last.last_author_name} · {formatRelativeTime(last.last_at)}
            </p>
          </div>
        </Link>
      )}
    </div>
  )
}

/** Nhãn «Đang ẩn» — chỉ forum_admin mới nhận được nhóm/box ẩn từ backend. */
function HiddenBadge({ className }: { className?: string }) {
  return (
    <Badge variant="secondary" className={className}>
      <EyeOff className="size-3" aria-hidden />
      Đang ẩn
    </Badge>
  )
}
