import { useCallback, useEffect, useRef, useState } from 'react'

import type { SelectOption } from '../types'

/**
 * Nạp options động cho trường có `fetchOptions` (kiểu `combobox` hoặc `select` không khai
 * `options` tĩnh), có debounce 300ms.
 *
 * duoc-CR-778: trả thêm `labels` — sổ nhãn của MỌI mục đã từng nạp về trong phiên. Lọc do
 * server làm nên mỗi lần gõ là danh sách thay hẳn; mục đã chọn trước đó rơi khỏi danh sách
 * mới thì ô chọn chỉ còn biết mỗi cái id ("12") nếu không giữ lại nhãn của nó.
 */
export function useFilterOptions(fetchFn?: (search: string) => Promise<SelectOption[]>) {
  const [options, setOptions] = useState<SelectOption[]>([])
  const [labels, setLabels] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)
  const timerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const search = useCallback(
    (query: string) => {
      if (!fetchFn) return
      if (timerRef.current) clearTimeout(timerRef.current)

      setLoading(true)
      timerRef.current = setTimeout(async () => {
        try {
          const next = await fetchFn(query)
          setOptions(next)
          setLabels((prev) => {
            const merged = { ...prev }
            for (const option of next) merged[option.value] = option.label
            return merged
          })
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

  // Nạp options lần đầu. Đây là effect THẬT (gọi API ra ngoài React), không
  // phải đồng bộ state theo prop — `search()` chỉ set `loading` rồi fetch trong
  // setTimeout. Tắt rule tại chỗ vì chuyển sang gán lúc render sẽ fetch ngay
  // trong thân render, đúng thứ mà rule này muốn ngăn.
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    if (fetchFn) search('')
    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
    }
  }, [fetchFn, search])

  return { options, labels, loading, search }
}
