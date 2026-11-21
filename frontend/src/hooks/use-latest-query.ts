import { useCallback, useEffect, useRef, useState } from 'react'

/**
 * Nạp dữ liệu theo khóa (thường là `JSON.stringify` của bộ lọc): mỗi lần khóa đổi gọi lại `fetcher`,
 * CHỈ nhận phản hồi của lần gọi mới nhất (lần cũ về trễ bị bỏ), và giữ dữ liệu cũ trong lúc nạp để bảng
 * không chớp trống. `enabled = false` thì không gọi và xóa dữ liệu. `reload()` ép nạp lại cùng khóa.
 */
export function useLatestQuery<T>(fetcher: () => Promise<T>, key: string, enabled = true) {
  const [data, setData] = useState<T | null>(null)
  const [loading, setLoading] = useState(false)
  const [failed, setFailed] = useState(false)
  const [tick, setTick] = useState(0)
  const seq = useRef(0)
  const fetcherRef = useRef(fetcher)
  fetcherRef.current = fetcher

  useEffect(() => {
    const id = ++seq.current
    if (!enabled) { setData(null); setLoading(false); setFailed(false); return }
    setLoading(true)
    setFailed(false)
    fetcherRef.current()
      .then((d) => { if (id === seq.current) setData(d) })
      .catch(() => { if (id === seq.current) setFailed(true) })
      .finally(() => { if (id === seq.current) setLoading(false) })
    return () => { seq.current++ }
  }, [key, enabled, tick])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, loading, failed, reload }
}
