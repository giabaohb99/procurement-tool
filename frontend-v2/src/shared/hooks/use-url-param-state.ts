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

/**
 * Đặt NHIỀU param trong MỘT lượt cập nhật URL.
 *
 * ⚠️ **Không gọi hai `setValue` của `useUrlParamState` liên tiếp trong cùng một
 * lần bấm** — lần thứ hai nhận `current` là URL CŨ (thay đổi của lần đầu chưa
 * kịp vào), nên nó ghi đè và thay đổi đầu tiên biến mất không dấu vết.
 *
 * Lỗi thật, dựng lại được 04/09/2026 ở màn Lịch nghỉ: bấm "+11 người nữa" trên
 * ô ngày 15 chạy `setAnchorISO('2027-03-15')` rồi `setMode('day')`; kết quả ra
 * `?mode=day&date=2027-03-01` — đúng chế độ, **sai ngày**, và người dùng rơi
 * vào một ngày chẳng ai nghỉ ngay sau khi bấm vào ngày có mười bốn người nghỉ.
 *
 * Giá trị rỗng hoặc trùng mặc định thì truyền `null` để xóa khỏi URL.
 */
export function useSetUrlParams() {
  const [, setSearchParams] = useSearchParams()

  return useCallback(
    (next: Record<string, string | null>) => {
      setSearchParams(
        (current) => {
          const params = new URLSearchParams(current)
          for (const [key, value] of Object.entries(next)) {
            if (value === null || value === '') params.delete(key)
            else params.set(key, value)
          }
          return params
        },
        { replace: true },
      )
    },
    [setSearchParams],
  )
}

/**
 * Hàm cho nút *Xóa lọc*: xóa các tham số `keys` khỏi URL trong MỘT lượt ghi
 * (kh-NT2-2b). `advanced: true` xóa luôn điều kiện của *Bộ lọc điều kiện*
 * (`<cột>__<op>`, `conjunction`) đang có trên URL.
 *
 * ⚠️ **Vì sao có hàm này.** Nút *Xóa lọc* cũ ở 21 màn gọi lần lượt từng setter
 * (`setStatus(ALL)`, `setCompanyId(ALL)`…). Mỗi setter dựng URL mới từ URL LÚC
 * DỰNG — xem `useSetUrlParams` — nên chỉ lần cuối ăn: bấm *Xóa lọc* mà bảng vẫn
 * lọc theo mấy ô đầu.
 *
 * ⚠️ **Có `filter.reset()` thì gọi nó TRƯỚC hàm này.** `reset` cũng ghi URL từ bản
 * lúc dựng và chép lại các ô có trong `preserveParams`; lượt ghi nào đến SAU thì
 * thắng, nên lượt của hàm này phải đi sau, kèm `advanced: true` để bỏ luôn điều
 * kiện cũ mà nó còn thấy trên URL lúc dựng.
 *
 * Giá trị bị xóa = ô về MẶC ĐỊNH của nó (`useUrlParamState` không ghi giá trị mặc
 * định lên URL), nên ô có mặc định khác `all` (năm hiện tại, `folder_sub=true`…)
 * vẫn về đúng mặc định.
 */
export function useClearUrlParams() {
  const [searchParams] = useSearchParams()
  const setUrlParams = useSetUrlParams()

  return useCallback(
    (keys: string[], { advanced = false }: { advanced?: boolean } = {}) => {
      const next: Record<string, null> = {}
      for (const key of keys) next[key] = null
      if (advanced) {
        for (const key of searchParams.keys()) {
          if (key.includes('__') || key === 'conjunction') next[key] = null
        }
      }
      setUrlParams(next)
    },
    [searchParams, setUrlParams],
  )
}
