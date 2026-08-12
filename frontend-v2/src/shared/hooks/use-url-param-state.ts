import { useCallback } from 'react'
import { useSearchParams } from 'react-router-dom'

/**
 * Một ô lọc dạng CHỌN (select) lấy URL làm nguồn sự thật — tải lại trang hay
 * gửi link cho người khác vẫn giữ nguyên bộ lọc đang xem.
 *
 * Khác `useUrlSearchParam` (dành cho ô gõ chữ): không cần state cục bộ và không
 * debounce, vì select chỉ đổi giá trị khi người dùng bấm chọn.
 *
 * Giá trị trùng `defaultValue` thì XÓA khỏi URL thay vì ghi `?status=all` —
 * link sạch, và mặc định đổi sau này không làm hỏng link cũ.
 *
 * ⚠️ Param nào dùng ở đây PHẢI khai trong `preserveParams` của `FilterProvider`
 * trên cùng trang, nếu không lần bấm "Áp dụng" bộ lọc nâng cao sẽ quét sạch nó.
 */
export function useUrlParamState(name: string, defaultValue: string) {
  const [searchParams, setSearchParams] = useSearchParams()
  const value = searchParams.get(name) ?? defaultValue

  const setValue = useCallback(
    (next: string) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current)
          if (next && next !== defaultValue) params.set(name, next)
          else params.delete(name)
          return params
        },
        // `replace`: đổi bộ lọc năm lần rồi bấm Back thì người dùng mong quay
        // lại TRANG TRƯỚC, không phải lùi qua từng lần chọn.
        { replace: true },
      )
    },
    [name, defaultValue, setSearchParams],
  )

  return [value, setValue] as const
}
