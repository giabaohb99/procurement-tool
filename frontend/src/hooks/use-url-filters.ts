import { Dispatch, SetStateAction, useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'

// Giữ bộ lọc của trang danh sách trên URL query.
//
// Trước đây bộ lọc chỉ nằm trong state React: F5 / mở lại tab / gửi link cho đồng nghiệp là mất
// hết, danh sách nạp lại toàn bộ dữ liệu. Nay mọi ô lọc chính được ghi thẳng lên URL, cùng chỗ với
// BỘ LỌC ĐIỀU KIỆN (`<field>__<op>`, xem components/conditional-filter) — hai bên không đụng nhau
// vì mỗi bên chỉ xóa/ghi đúng các key của mình.
//
// Quy ước: giá trị RỖNG hoặc TRÙNG MẶC ĐỊNH thì không ghi lên URL, để link gọn và để đổi mặc
// định sau này không làm link cũ hiểu sai.

export type FilterValues = Record<string, any>

/** Ghi các key do thanh lọc quản lý vào `target`. Param khác (page, bộ lọc điều kiện…) giữ nguyên. */
function applyOwnedKeys(
  target: URLSearchParams, values: FilterValues, defaults: FilterValues, keys: string[],
) {
  keys.forEach((k) => {
    const v = values[k]
    const d = defaults[k]
    const isEmpty = v === undefined || v === null || v === ''
    if (isEmpty || String(v) === String(d ?? '')) target.delete(k)
    else target.set(k, String(v))
  })
}

/** Đọc URL → giá trị lọc, ép về đúng kiểu của `defaults` (ô số vẫn ra số). */
function readFromUrl<T extends FilterValues>(params: URLSearchParams, defaults: T, keys: string[]): T {
  const out: any = { ...defaults }
  keys.forEach((k) => {
    const raw = params.get(k)
    if (raw === null) return
    out[k] = typeof defaults[k] === 'number' ? (Number(raw) || 0) : raw
  })
  return out
}

/** Bộ lọc lưu trên URL — dùng y như `useState`.
 *
 *  `defaults` chỉ được đọc ở lần mount ĐẦU TIÊN (giống initial state của useState): vừa quyết định
 *  danh sách key mà hook được phép ghi lên URL, vừa là mốc so sánh để bỏ bớt param thừa.
 */
export function useUrlFilters<T extends FilterValues>(defaults: T): [T, Dispatch<SetStateAction<T>>] {
  const [searchParams, setSearchParams] = useSearchParams()
  const defaultsRef = useRef(defaults)
  const keys = useMemo(() => Object.keys(defaultsRef.current), [])
  const [values, setValues] = useState<T>(
    () => readFromUrl(new URLSearchParams(window.location.search), defaultsRef.current, keys),
  )

  useEffect(() => {
    const next = new URLSearchParams(searchParams)
    applyOwnedKeys(next, values, defaultsRef.current, keys)
    // Chỉ điều hướng khi URL thực sự đổi → không lặp vô hạn, không đè bộ lọc điều kiện.
    // `replace` để nút Back vẫn quay về TRANG trước, không phải từng bước gõ ô lọc.
    if (next.toString() !== searchParams.toString()) setSearchParams(next, { replace: true })
  }, [values, searchParams, keys, setSearchParams])

  return [values, setValues]
}

/** Bản chỉ-ghi, cho trang mà danh sách ô lọc đổi theo cấu hình (CrudList: mỗi danh mục một bộ key)
 *  nên không thể chốt `defaults` ở lần mount đầu. State vẫn do component tự giữ. */
export function useFilterUrlWriter(keys: string[]) {
  const [searchParams, setSearchParams] = useSearchParams()
  return useCallback((values: FilterValues) => {
    const next = new URLSearchParams(searchParams)
    applyOwnedKeys(next, values, {}, keys)
    if (next.toString() !== searchParams.toString()) setSearchParams(next, { replace: true })
  }, [searchParams, keys, setSearchParams])
}
