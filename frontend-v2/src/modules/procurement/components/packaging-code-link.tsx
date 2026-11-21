/**
 * duoc-CR-784 — ô MÃ VTBB bấm được: mở Lịch sử mua hàng của đúng mã đó (`?codes=`). Dùng ở các bảng của cụm Giá bao bì
 * (Bảng giá, Giá mua gần nhất, Tác động giá, chính Lịch sử mua hàng) để một mã là một cú bấm tới mọi lần mua của nó.
 *
 * Dừng nổi bọt cú bấm: bảng có thể đặt hành động ở cả dòng (bấm đúp / bấm dòng) — bấm mã thì chỉ đi tới lịch sử.
 */
import { Link } from 'react-router-dom'

import { cn } from '@/shared/utils/cn'

import { packagingHistoryHref, packagingHistoryProductHref } from '../utils/packaging-history'

interface PackagingCodeLinkProps {
  code: string
  className?: string
  /** `code` là mã HÀNG HÓA (sản phẩm): mở lịch sử ở chế độ "Theo mã sản phẩm" (mọi mã thành phần của định mức). */
  product?: boolean
}

export function PackagingCodeLink({ code, className, product = false }: PackagingCodeLinkProps) {
  return (
    <Link
      to={product ? packagingHistoryProductHref(code) : packagingHistoryHref(code)}
      title={
        product
          ? `Xem lịch sử mua các vật tư bao bì của ${code}`
          : `Xem lịch sử mua hàng của ${code}`
      }
      onClick={(event) => event.stopPropagation()}
      className={cn('font-semibold text-primary tabular-nums hover:underline', className)}
    >
      {code}
    </Link>
  )
}
