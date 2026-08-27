import { ThumbsUp } from 'lucide-react'

import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { Skeleton } from '@/shared/ui/skeleton'

import { usePostLikes } from '../hooks/use-post-likes'

interface PostLikesDialogProps {
  postId: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

/** Hộp "ai đã thích bài này" — mở từ số đếm dưới bài. API chỉ trả tên, không avatar. */
export function PostLikesDialog({ postId, open, onOpenChange }: PostLikesDialogProps) {
  const likes = usePostLikes(postId, open)

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2 text-base">
            <ThumbsUp className="size-4 text-primary" />
            Người đã thích
          </DialogTitle>
        </DialogHeader>
        {likes.isPending && <Skeleton className="h-20 w-full" />}
        {likes.isError && (
          <p className="text-sm text-destructive">Không tải được danh sách.</p>
        )}
        {likes.data && (
          <ul className="max-h-72 space-y-1 overflow-y-auto text-sm">
            {likes.data.map((person) => (
              <li key={person.user_id} className="rounded-md px-2 py-1.5 hover:bg-muted">
                {person.name}
              </li>
            ))}
            {!likes.data.length && (
              <li className="px-2 py-1.5 text-muted-foreground">Chưa có ai thích bài này.</li>
            )}
          </ul>
        )}
      </DialogContent>
    </Dialog>
  )
}
