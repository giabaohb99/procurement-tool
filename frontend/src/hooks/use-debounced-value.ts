import { useEffect, useState } from 'react'

/** Giá trị trễ `ms` mili giây — gõ liên tục chỉ gửi máy chủ sau khi ngừng tay. */
export function useDebouncedValue<T>(value: T, ms: number): T {
  const [debounced, setDebounced] = useState(value)
  useEffect(() => {
    const t = setTimeout(() => setDebounced(value), ms)
    return () => clearTimeout(t)
  }, [value, ms])
  return debounced
}
