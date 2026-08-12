import { useEffect, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

import { useDebouncedValue } from './use-debounced-value'

/**
 * Ô tìm kiếm có ghi từ khóa lên URL — tải lại trang hay gửi link cho người khác
 * vẫn giữ nguyên kết quả đang xem.
 *
 * Ô nhập chạy bằng state cục bộ để gõ không giật; URL chỉ được ghi sau khi
 * ngừng gõ (`delay`), và ghi bằng `replace` để nút Back không phải bấm lại
 * từng ký tự đã gõ.
 *
 * Dùng chung tên param `q` với `conditional-filter` (`searchParamName`), nhờ đó
 * khi áp bộ lọc nâng cao thì từ khóa vẫn được giữ lại trên URL.
 */
export function useUrlSearchParam(name = 'q', delay = 350) {
  const [searchParams, setSearchParams] = useSearchParams()

  // Chỉ đọc URL lúc khởi tạo; sau đó ô nhập là nguồn sự thật.
  const [value, setValue] = useState(() => searchParams.get(name) ?? '')
  const debouncedValue = useDebouncedValue(value, delay)

  const lastWritten = useRef(debouncedValue)

  useEffect(() => {
    if (lastWritten.current === debouncedValue) return
    lastWritten.current = debouncedValue

    setSearchParams(
      (current) => {
        const next = new URLSearchParams(current)
        if (debouncedValue) next.set(name, debouncedValue)
        else next.delete(name)
        return next
      },
      { replace: true },
    )
  }, [debouncedValue, name, setSearchParams])

  return { value, setValue, debouncedValue }
}
