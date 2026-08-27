import { Skeleton } from '@/shared/ui/skeleton'

/** Khung xương một thẻ bài trong lúc chờ dữ liệu — dùng ở bảng tin và trang cá nhân. */
export function FeedSkeleton() {
  return (
    <div className="border-y border-border bg-card p-4 shadow-sm sm:rounded-xl sm:border">
      <div className="flex items-center gap-3">
        <Skeleton className="size-10 rounded-full" />
        <div className="space-y-1.5">
          <Skeleton className="h-3.5 w-40" />
          <Skeleton className="h-3 w-24" />
        </div>
      </div>
      <div className="mt-3 space-y-2">
        <Skeleton className="h-3.5 w-full" />
        <Skeleton className="h-3.5 w-3/4" />
      </div>
      <Skeleton className="mt-3 aspect-[2/1] w-full" />
    </div>
  )
}
