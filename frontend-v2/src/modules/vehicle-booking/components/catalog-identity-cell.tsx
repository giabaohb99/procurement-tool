import type { ReactNode } from 'react'

interface CatalogIdentityCellProps {
  /** Ảnh đại diện / ô biểu tượng bên trái. */
  media: ReactNode
  /** Dòng trên — thứ người ta nhận ra bản ghi bằng nó (biển số, tên tài xế). */
  title: string
  /** Dòng dưới — thuộc tính phụ (mẫu xe, giấy phép lái xe). */
  subtitle: string
}

/**
 * Ô NHẬN DIỆN hai dòng của bảng danh mục Đặt xe: ảnh/biểu tượng + tên đậm +
 * dòng phụ mờ.
 *
 * Dùng chung cho danh mục Xe và Tài xế. Hai bảng đứng cạnh nhau trong cùng một
 * menu, nên chữ phải đậm bằng nhau và dòng phụ phải nhỏ bằng nhau — tách ra một
 * chỗ để không thể lệch.
 *
 * ⚠️ Dòng phụ LUÔN dựng, kể cả khi rỗng: thiếu nó thì hàng đó thấp hơn những
 * hàng khác và cả bảng gợn lên gợn xuống.
 */
export function CatalogIdentityCell({ media, title, subtitle }: CatalogIdentityCellProps) {
  return (
    <div className="flex items-center gap-3 py-1">
      {media}
      <div className="min-w-0">
        <div className="truncate font-semibold text-navy dark:text-foreground">{title || '—'}</div>
        <div className="truncate text-[11px] text-muted-foreground">{subtitle || '—'}</div>
      </div>
    </div>
  )
}
