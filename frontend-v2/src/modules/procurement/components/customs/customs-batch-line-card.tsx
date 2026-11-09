import type { ReactNode } from 'react'

interface CustomsBatchLineCardProps {
  /** Số dòng trong tệp Excel; 0 / null = ghi chú mức lô (lỗi đọc tệp…), không gắn dòng nào. */
  rowNo: number | null
  /** Huy hiệu kết cục / mức — truyền đúng huy hiệu bảng đang vẽ, kẻo hai khổ nói hai màu. */
  badge: ReactNode
  /** Tên hàng của dòng (chỉ nhật ký từng dòng có); trống thì bỏ hẳn, không in gạch ngang. */
  productName?: string
  message: string
}

/**
 * Một DÒNG NHẬT KÝ lô nạp ở khổ điện thoại — dùng chung cho thẻ "Kết quả từng dòng" (4 cột,
 * ~890px) và "Ghi chú lỗi / cảnh báo" (3 cột, ~710px) của hộp Nhật ký lô.
 *
 * ⚠️ **Số dòng + huy hiệu đứng chung hàng đầu**: người rà nhật ký mở tệp Excel bên cạnh và dò
 * theo số dòng, nên số dòng phải là thứ mắt chạm tới trước; câu ghi chú dài xuống dưới, xuống
 * dòng tự do — cắt cụt nó là mất đúng lý do dòng bị bỏ.
 *
 * Hai bảng không khai `onRowClick` nên thẻ là `<div>` thường.
 */
export function CustomsBatchLineCard({ rowNo, badge, productName, message }: CustomsBatchLineCardProps) {
  return (
    <div className="space-y-1">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium tabular-nums text-muted-foreground">
          {rowNo ? `Dòng ${rowNo}` : 'Không gắn dòng'}
        </span>
        {badge}
      </div>
      {productName && <p className="text-sm font-medium break-words">{productName}</p>}
      {message && <p className="text-xs break-words text-muted-foreground">{message}</p>}
    </div>
  )
}
