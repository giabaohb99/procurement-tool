import { useCallback, useEffect, useRef, useState } from 'react'

import type { SelectOption } from '../types'

/** Nạp options động cho trường `combobox`, có debounce 300ms. */
export function useFilterOptions(fetchFn?: (search: string) => Promise<SelectOption[]>) {
  const [options, setOptions] = useState<SelectOption[]>([])
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const search = useCallback(
    (query: string) => {
      if (!fetchFn) return
      if (timerRef.current) clearTimeout(timerRef.current)

      setLoading(true)
      timerRef.current = setTimeout(async () => {
        try {
          setOptions(await fetchFn(query))
        } catch {
          // Nạp hỏng thì để danh sách rỗng — ô lọc vẫn dùng được, không vỡ trang.
          setOptions([])
        } finally {
          setLoading(false)
        }
      }, 300)
    },
    [fetchFn],
  )

  useEffect(() => {
    if (fetchFn) search('')
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [fetchFn, search])

  return { options, loading, search }
}
