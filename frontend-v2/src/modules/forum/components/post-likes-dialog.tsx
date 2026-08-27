import { useState } from 'react'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'

import { usePostLikes } from '../hooks/use-post-likes'
import { FORUM_REACTION_KINDS, FORUM_REACTION_META } from '../types/forum-post'
import type { ForumReactionKind } from '../types/forum-post'

interface PostLikesDialogProps {
  postId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/**
 * Hộp "ai đã bày tỏ cảm xúc" (CR-206) — mở từ số đếm dưới bài. Hàng chip đầu
 * hộp lọc theo từng cảm xúc kiểu Facebook; chip chỉ hiện cảm xúc CÓ người bấm.
 * API chỉ trả tên + kind, không avatar.
 */
export function PostLikesDialog({ postId, open, onOpenChange }: PostLikesDialogProps) {
  const likes = usePostLikes(postId, open)
  // 0 = "Tất cả". Không nhớ tab giữa hai lần mở — mỗi lần mở nhìn tổng trước.
  const [filterKind, setFilterKind] = useState(0)

  const people = likes.data ?? []
  const countByKind = new Map<number, number>()
  for (const person of people) {
    countByKind.set(person.kind, (countByKind.get(person.kind) ?? 0) + 1)
  }
  const shownKinds = FORUM_REACTION_KINDS.filter((kind) => (countByKind.get(kind) ?? 0) > 0)
  const shown = filterKind === 0 ? people : people.filter((p) => p.kind === filterKind)

  const selectTab = (kind: number) => setFilterKind(kind)

  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setFilterKind(0)
        onOpenChange(next)
      }}
    >
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-base">Cảm xúc về bài viết</DialogTitle>
        </DialogHeader>
        {likes.isPending && <Skeleton className="h-20 w-full" />}
        {likes.isError && (
          <p className="text-sm text-destructive">Không tải được danh sách.</p>
        )}
        {likes.data && (
          <>
            {shownKinds.length > 1 && (
              <div className="flex flex-wrap items-center gap-1 border-b border-border pb-2 text-sm">
                <button
                  type="button"
                  onClick={() => selectTab(0)}
                  className={cn(
                    'rounded-full px-2.5 py-1 hover:bg-muted',
                    filterKind === 0 && 'bg-muted font-medium',
                  )}
                >
                  Tất cả {people.length}
                </button>
                {shownKinds.map((kind) => {
                  const meta = FORUM_REACTION_META[kind]
                  const Icon = meta.icon
                  return (
                    <button
                      key={kind}
                      type="button"
                      aria-label={meta.label}
                      title={meta.label}
                      onClick={() => selectTab(kind)}
                      className={cn(
                        'flex items-center gap-1 rounded-full px-2.5 py-1 hover:bg-muted',
                        filterKind === kind && 'bg-muted font-medium',
                      )}
                    >
                      <Icon
                        className={cn('size-4', meta.className, meta.fill && 'fill-current')}
                        aria-hidden
                      />
                      {countByKind.get(kind)}
                    </button>
                  )
                })}
              </div>
            )}
            <ul className="max-h-72 space-y-1 overflow-y-auto text-sm">
              {shown.map((person) => {
                const meta = FORUM_REACTION_META[person.kind as ForumReactionKind]
                const Icon = meta?.icon
                return (
                  <li
                    key={person.user_id}
                    className="flex items-center justify-between rounded-md px-2 py-1.5 hover:bg-muted"
                  >
                    <span>{person.name}</span>
                    {Icon && (
                      <Icon
                        className={cn('size-4', meta.className, meta.fill && 'fill-current')}
                        aria-label={meta.label}
                      />
                    )}
                  </li>
                )
              })}
              {!shown.length && (
                <li className="px-2 py-1.5 text-muted-foreground">
                  Chưa có ai bày tỏ cảm xúc với bài này.
                </li>
              )}
            </ul>
          </>
        )}
      </DialogContent>
    </Dialog>
  )
}
