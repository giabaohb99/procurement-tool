import { useEffect, useRef } from 'react'

interface InfiniteSentinelInput {
  fetchNextPage: () => Promise<unknown>
  hasNextPage: boolean
  isFetchingNextPage: boolean
}

/**
 * Lính canh cuộn vô hạn: trả về ref gắn vào một `<div>` rỗng ở đáy danh sách —
 * lọt vào vùng nhìn (đệm trước 600px cho cuộn không khựng) là nạp trang kế.
 * Dùng chung cho bảng tin và trang cá nhân.
 */
export function useInfiniteSentinel({
  fetchNextPage,
  hasNextPage,
  isFetchingNextPage,
}: InfiniteSentinelInput) {
  const sentinelRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const sentinel = sentinelRef.current
    if (!sentinel) return
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting && hasNextPage && !isFetchingNextPage) {
          void fetchNextPage()
        }
      },
      { rootMargin: '600px' },
    )
    observer.observe(sentinel)
    return () => observer.disconnect()
  }, [fetchNextPage, hasNextPage, isFetchingNextPage])

  return sentinelRef
}
