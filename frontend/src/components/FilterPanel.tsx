import { ReactNode } from 'react'

// Khung thanh lọc DÙNG CHUNG cho mọi trang danh sách.
//
// Trước đây mỗi trang tự dựng `<div className="card filters" style={{...}}>` với label/kích thước
// khác nhau → UI lộn xộn. Nay mọi trang khai báo:
//
//   <FilterPanel canClear={...} onClear={...} extra={<ConditionalFilterButton />}>
//     <FilterItem label="Công ty">…</FilterItem>
//     <FilterItem label="Tuổi nợ">…</FilterItem>
//   </FilterPanel>
//
// Cơ chế "bộ lọc phụ" (nút "Thêm bộ lọc (N)" gập/mở) đã BỎ: nay mọi ô lọc hiện thẳng, còn các
// điều kiện phức tạp (chứa / lớn hơn / trong khoảng / VÀ-HOẶC) do BỘ LỌC ĐIỀU KIỆN lo
// (components/conditional-filter). Prop `secondary`/`active` của FilterItem vẫn nhận để khỏi
// phải sửa hàng loạt trang, nhưng không còn tác dụng gì.

export function FilterItem({
  label, children, width, grow,
}: {
  label?: string
  children: ReactNode
  width?: number          // bề rộng cơ sở (px); mặc định 180
  grow?: boolean          // chiếm phần dư còn lại (dùng cho ô tìm kiếm)
  secondary?: boolean     // (bỏ dùng) trước đây: ẩn sau nút "Thêm bộ lọc"
  active?: boolean        // (bỏ dùng) trước đây: đếm badge cho bộ lọc phụ
}) {
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
  extra?: ReactNode       // nút phụ bên phải (vd nút Bộ lọc điều kiện, Xuất CSV)
}) {
  return (
    <div className="card filter-panel">
      {children}

      <div className="filter-actions">
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
