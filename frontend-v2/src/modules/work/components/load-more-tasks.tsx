import { Loader2 } from 'lucide-react'
import { useEffect, useRef } from 'react'

import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'

interface LoadMoreTasksProps {
  /** Số việc còn chưa tải của cột / nhóm này; 0 = không dựng gì. */
  remaining: number
  loading: boolean
  onLoadMore: () => void
  className?: string
}

/**
 * Đuôi «Tải thêm» của một cột kanban / một nhóm ở khung Danh sách — bao-CR-483.
 *
 * Hai cách kích: cuộn tới đáy (IntersectionObserver trên chính nút) hoặc bấm.
 * Nút vẫn phải có vì (1) cột ngắn không cuộn được thì không có sự kiện «tới
 * đáy» nào, (2) người dùng bàn phím / trình đọc màn hình cần một điểm bấm thật.
 * jsdom không có IntersectionObserver — bỏ qua phần tự tải, bài kiểm bấm tay.
 */
export function LoadMoreTasks({ remaining, loading, onLoadMore, className }: LoadMoreTasksProps) {
  const ref = useRef<HTMLButtonElement>(null)
  //  Bản mới nhất của hai prop cho observer đọc — cập nhật trong effect chứ
  //  không lúc render (`react-hooks/refs`), để observer khỏi phải dựng lại mỗi
  //  lần trang vẽ lại vì `onLoadMore` là lambda mới.
  const latest = useRef({ loading, onLoadMore })
  useEffect(() => {
    latest.current = { loading, onLoadMore }
  }, [loading, onLoadMore])

  useEffect(() => {
    const node = ref.current
    if (!node || remaining <= 0 || typeof IntersectionObserver === 'undefined') return
    const observer = new IntersectionObserver((entries) => {
      if (entries.some((e) => e.isIntersecting) && !latest.current.loading) {
        latest.current.onLoadMore()
      }
    })
    observer.observe(node)
    return () => observer.disconnect()
  }, [remaining])

  if (remaining <= 0) return null
  return (
    <Button
      ref={ref}
      type="button"
      variant="ghost"
      size="sm"
      disabled={loading}
      onClick={onLoadMore}
      className={cn('w-full justify-center text-muted-foreground', className)}
      aria-label={`Tải thêm ${remaining} việc`}
    >
      {loading ? <Loader2 className="size-4 animate-spin" /> : null}
      {loading ? 'Đang tải…' : `Tải thêm ${remaining} việc`}
    </Button>
  )
}
