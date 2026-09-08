import { cn } from '@/shared/utils/cn'

interface PurchaseOrderPrintSignatureBoxProps {
  /** Tên ô ký: "Người lập", "Trưởng bộ phận"… */
  title: string
  /** Dòng nhỏ trong ngoặc — mỗi mẫu in ghi một kiểu. */
  hint?: string
  /** Dòng nơi + ngày ký đặt phía trên tiêu đề (chỉ mẫu Đơn đặt hàng có). */
  dateLine?: string
  /** URL ảnh chữ ký; rỗng thì ô để trống cho ký tay. */
  signature?: string
  /** Họ tên người ký — in cả khi tắt chữ ký, cho đúng "(Ký, ghi rõ họ tên)". */
  name?: string
  className?: string
}

/**
 * Một ô ký trên bản in Đơn mua hàng.
 *
 * Chiều cao ô giữ nguyên dù có ảnh hay không: bật/tắt chữ ký mà bố cục nhảy thì
 * đơn dài đúng một trang sẽ tràn sang trang hai ở đúng bản không chữ ký.
 *
 * `h-28` ≈ 2,8cm — chỗ trống của bản v1 (h-16 ≈ 1,7cm) hẹp quá, in ra ký tay
 * không lọt chữ ký (khách báo 31/08/2026). Đừng hạ xuống cho gọn trang.
 */
export function PurchaseOrderPrintSignatureBox({
  title,
  hint = '(Ký, ghi rõ họ tên)',
  dateLine,
  signature,
  name,
  className,
}: PurchaseOrderPrintSignatureBoxProps) {
  return (
    <div className={cn('text-center', className)}>
      {dateLine && <p className="mb-1 text-[11.5px] italic">{dateLine}</p>}
      <b>{title}</b>
      <p className="text-[11px] italic">{hint}</p>
      <div className="mt-1 flex h-28 flex-col items-center justify-center gap-1">
        {signature && (
          <img
            src={signature}
            alt={`Chữ ký ${title}`}
            className="max-h-20 max-w-full object-contain"
          />
        )}
        {name && <span className="font-semibold">{name}</span>}
      </div>
    </div>
  )
}
