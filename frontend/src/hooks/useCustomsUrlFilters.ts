// bao-CR-734 (bê từ bản v2 `customs-price-page.tsx` + `use-url-search-param.ts`): bộ lọc dòng hàng Tra cứu thị
// trường nằm trên URL — gửi link là người nhận thấy đúng kết quả, F5 / Back không mất bộ lọc. Ô CHỌN áp ngay;
// ô GÕ CHỮ (từ khóa, ba khoảng số) chờ ngưng gõ 350 ms rồi mới ghi URL (mỗi phím không bắn một lượt gọi API).
//
// Ngoại lệ có chủ ý: frontend/ đã đóng băng, người chủ cho phép đồng bộ khu này với v2 (05/11/2026).
import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { useSearchParams } from 'react-router-dom'
import { CustomsFilters, EMPTY_FILTERS } from '../components/customs/customs-shared'

const KEYS = Object.keys(EMPTY_FILTERS) as (keyof CustomsFilters)[]
/** Ô gõ chữ — hoãn ghi URL tới khi ngưng gõ. Các ô còn lại là ô chọn, ghi ngay. */
export const TYPED_FILTER_KEYS: (keyof CustomsFilters)[] = [
  'q', 'price_min', 'price_max', 'qty_min', 'qty_max', 'rate_min', 'rate_max',
]
export const TYPING_DELAY_MS = 350

export function readCustomsFilters(params: URLSearchParams): CustomsFilters {
  const out = { ...EMPTY_FILTERS }
  for (const key of KEYS) out[key] = params.get(key) ?? ''
  return out
}

/** Ghép `patch` vào bộ tham số URL: ô rỗng thì xóa khỏi URL. Giữ nguyên tham số không phải bộ lọc. */
export function mergeFilterParams(current: URLSearchParams, patch: Partial<CustomsFilters>): URLSearchParams {
  const next = new URLSearchParams(current)
  for (const [key, value] of Object.entries(patch)) {
    if (value) next.set(key, value)
    else next.delete(key)
  }
  return next
}

export function useCustomsUrlFilters() {
  const [searchParams, setSearchParams] = useSearchParams()
  const urlKey = searchParams.toString()
  const filters = useMemo(() => readCustomsFilters(searchParams), [urlKey])
  /** Giá trị đang hiện trong các ô (ô gõ chữ đi trước URL một nhịp hoãn). */
  const [draft, setDraft] = useState<CustomsFilters>(filters)
  /** URL do CHÍNH hook này ghi ra lần cuối — để phân biệt với URL đổi từ ngoài (Back, link, bộ lọc đã lưu). */
  const written = useRef<string | null>(null)

  //  URL đổi từ bên ngoài thì ô nhập theo. Không so thế này thì lúc gõ nhanh, nhịp ghi của ký tự trước
  //  nhảy ngược vào ô và nuốt mất mấy ký tự vừa gõ.
  useEffect(() => {
    if (written.current === urlKey) return
    setDraft(filters)
  }, [urlKey, filters])

  const write = useCallback((patch: Partial<CustomsFilters>) => {
    setSearchParams((current) => {
      const next = mergeFilterParams(current, patch)
      written.current = next.toString()
      return next
    }, { replace: true })
  }, [setSearchParams])

  //  Hoãn ghi các ô gõ chữ.
  const typedKey = TYPED_FILTER_KEYS.map((key) => draft[key]).join('\u0001')
  useEffect(() => {
    const timer = setTimeout(() => {
      const patch: Partial<CustomsFilters> = {}
      for (const key of TYPED_FILTER_KEYS) if (draft[key] !== filters[key]) patch[key] = draft[key]
      if (Object.keys(patch).length) write(patch)
    }, TYPING_DELAY_MS)
    return () => clearTimeout(timer)
  }, [typedKey])

  /** Đổi một ô: ô chọn ghi URL ngay, ô gõ chữ chờ ngưng gõ. */
  const setField = useCallback((key: keyof CustomsFilters, value: string) => {
    setDraft((cur) => ({ ...cur, [key]: value }))
    if (!TYPED_FILTER_KEYS.includes(key)) write({ [key]: value })
  }, [write])

  /** Đổi nhiều ô cùng lúc và ghi URL ngay (khoảng ngày, chip doanh nghiệp, bộ lọc đã lưu). */
  const setFields = useCallback((patch: Partial<CustomsFilters>) => {
    setDraft((cur) => ({ ...cur, ...patch }))
    write(patch)
  }, [write])

  /** Chỉ đổi chữ đang hiện, CHƯA ghi URL (khoảng ngày mới chọn một đầu). */
  const setDraftFields = useCallback((patch: Partial<CustomsFilters>) => {
    setDraft((cur) => ({ ...cur, ...patch }))
  }, [])

  /** Enter trong ô gõ chữ: ghi ngay, không chờ. */
  const flush = useCallback(() => {
    const patch: Partial<CustomsFilters> = {}
    for (const key of TYPED_FILTER_KEYS) patch[key] = draft[key]
    write(patch)
  }, [draft, write])

  const clear = useCallback(() => setFields({ ...EMPTY_FILTERS }), [setFields])

  return { filters, draft, searchParams, setField, setFields, setDraftFields, flush, clear }
}
