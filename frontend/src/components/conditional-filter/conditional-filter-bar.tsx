import { ReactNode, useMemo, useState } from 'react'
import './conditional-filter.css'
import { FilterProvider } from './provider/filter-provider'
import { useFilterContext } from './provider/filter-context'
import FilterPopover from './ui/filter-popover'
import type { FilterFieldDefinition, RestQueryParams } from './types'

/**
 * Bộ lọc ĐIỀU KIỆN — port từ FilterCN (bỏ shadcn/Tailwind, dùng plain CSS + component sẵn có).
 *
 * Khác thanh lọc cơ bản (`FilterBar`) ở chỗ cho chọn PHÉP SO SÁNH (chứa / bằng / lớn hơn /
 * trong khoảng / thuộc danh sách / đang trống…) và nối nhiều điều kiện bằng VÀ / HOẶC.
 * Toàn bộ điều kiện nằm trên URL nên link chia sẻ được và nút back của trình duyệt chạy đúng.
 *
 * Tách provider và nút để nút nằm CHUNG hàng với thanh lọc cơ bản (slot `extra` của FilterBar):
 *
 *   <ConditionalFilter fields={PRODUCT_COND_FILTERS} onChange={reload}>
 *     <FilterBar … extra={<ConditionalFilterButton />} />
 *   </ConditionalFilter>
 *
 * Điều kiện đang áp dụng chỉ hiện qua số đếm trên nút; muốn xem/sửa/xóa thì mở bảng lọc.
 *
 * `fields[].name` PHẢI nằm trong whitelist FILTERABLE của controller, nếu không backend sẽ bỏ
 * qua điều kiện đó (xem app/core/filter_operators.py).
 */
export function ConditionalFilter({
  fields, onChange, allowConjunctionToggle = true, maxRows, children,
}: {
  fields: FilterFieldDefinition[]
  /** Gọi mỗi khi bộ lọc có hiệu lực đổi (kể cả do bấm back) — nhận query param để gửi API */
  onChange?: (params: RestQueryParams) => void
  allowConjunctionToggle?: boolean
  maxRows?: number
  children: ReactNode
}) {
  const config = useMemo(
    () => ({ fields, allowConjunctionToggle, maxRows }),
    [fields, allowConjunctionToggle, maxRows],
  )
  return <FilterProvider config={config} onChange={onChange}>{children}</FilterProvider>
}

/** Nút mở bảng dựng điều kiện — đặt vào `extra` của FilterBar để nằm cạnh "Thêm bộ lọc" */
export function ConditionalFilterButton() {
  const { activeCount } = useFilterContext()
  const [open, setOpen] = useState(false)

  return (
    <div className="cf-anchor">
      <button type="button" className={activeCount > 0 ? 'btn' : 'btn ghost'}
        onClick={() => setOpen((o) => !o)}>
        <i className="ti ti-filter-cog" />
        Bộ lọc điều kiện{activeCount > 0 ? ` · ${activeCount}` : ''}
      </button>
      {open && <FilterPopover onClose={() => setOpen(false)} />}
    </div>
  )
}
