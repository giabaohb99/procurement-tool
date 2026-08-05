import { Children, isValidElement, ReactNode, useState } from 'react'

// Khung thanh lọc DÙNG CHUNG cho mọi trang danh sách.
//
// Trước đây mỗi trang tự dựng `<div className="card filters" style={{...}}>` với label/kích thước
// khác nhau → UI lộn xộn. Nay mọi trang khai báo:
//
//   <FilterPanel canClear={...} onClear={...}>
//     <FilterItem label="Công ty">…</FilterItem>
//     <FilterItem label="Tuổi nợ" secondary active={!!f.aging}>…</FilterItem>
//   </FilterPanel>
//
// Trường `secondary` là bộ lọc PHỤ: mặc định ẩn sau nút "Thêm bộ lọc (N)"; nếu đang có giá trị
// (`active`) thì panel tự mở sẵn và hiện badge số lượng để người dùng biết đang lọc gì.

export function FilterItem({
  label, children, width, grow, secondary, active,
}: {
  label?: string
  children: ReactNode
  width?: number          // bề rộng cơ sở (px); mặc định 180
  grow?: boolean          // chiếm phần dư còn lại (dùng cho ô tìm kiếm)
  secondary?: boolean     // bộ lọc phụ — ẩn sau nút "Thêm bộ lọc"
  active?: boolean        // đang có giá trị lọc (chỉ dùng cho secondary, để đếm badge)
}) {
  void secondary; void active   // do FilterPanel đọc, không dùng ở đây
  return (
    <div className={'filter-item' + (grow ? ' grow' : '')} style={width ? { flexBasis: width } : undefined}>
      {label && <label>{label}</label>}
      {children}
    </div>
  )
}

export default function FilterPanel({
  children, onClear, canClear, extra,
}: {
  children: ReactNode
  onClear?: () => void
  canClear?: boolean      // có giá trị lọc nào không → hiện nút "Xóa lọc"
  extra?: ReactNode       // nút phụ bên phải (vd Xuất CSV)
}) {
  const items = Children.toArray(children).filter(isValidElement) as any[]
  const primary = items.filter((c) => !c.props?.secondary)
  const secondary = items.filter((c) => c.props?.secondary)
  const activeCount = secondary.filter((c) => c.props?.active).length

  const [expanded, setExpanded] = useState(() => activeCount > 0)

  return (
    <div className="card filter-panel">
      {primary}
      {expanded && secondary}

      <div className="filter-actions">
        {secondary.length > 0 && (
          <button className="btn ghost" onClick={() => setExpanded((e) => !e)}>
            <i className={`ti ${expanded ? 'ti-chevron-up' : 'ti-adjustments-horizontal'}`} />
            {expanded
              ? 'Thu gọn'
              : activeCount > 0
                ? `Thêm bộ lọc · ${activeCount} đang lọc`
                : `Thêm bộ lọc (${secondary.length})`}
          </button>
        )}
        {canClear && onClear && (
          <button className="btn ghost" onClick={onClear} title="Xóa tất cả bộ lọc">
            <i className="ti ti-rotate" />Xóa lọc
          </button>
        )}
        {extra}
      </div>
    </div>
  )
}
