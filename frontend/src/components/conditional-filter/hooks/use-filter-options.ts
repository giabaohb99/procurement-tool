import { useEffect, useState } from 'react'
import { api } from '../../../api/client'
import type { FilterFieldDefinition, SelectOption } from '../types'

/** Nạp options động cho các field khai báo `source` (NCC, công ty, nhóm hàng…).
 *  Giữ đúng cách làm của FilterBar cũ: gọi 1 lần, page_size lớn, lỗi thì bỏ qua im lặng
 *  (dropdown rỗng còn hơn vỡ cả thanh lọc). */
export function useFilterOptions(fields: FilterFieldDefinition[]) {
  const [dynamic, setDynamic] = useState<Record<string, SelectOption[]>>({})

  useEffect(() => {
    let alive = true
    fields.filter((f) => f.source).forEach((f) => {
      api.get(f.source!.url, { params: { page_size: 1000 } }).then((r) => {
        if (!alive) return
        const vk = f.source!.value || 'code'
        const lk = f.source!.label || 'name'
        const opts: SelectOption[] = (r.data.data.items || [])
          .map((it: any) => ({
            value: String(it[vk] ?? ''),
            label: String(it[lk] ?? it[vk] ?? ''),
          }))
          .filter((o: SelectOption) => o.value)
        setDynamic((s) => ({ ...s, [f.name]: opts }))
      }).catch(() => {})
    })
    return () => { alive = false }
  }, [fields])

  /** Options dùng được cho 1 field: ưu tiên khai báo tĩnh, sau đó tới nguồn API */
  return function optionsOf(field: FilterFieldDefinition): SelectOption[] {
    return field.options || dynamic[field.name] || []
  }
}
