/**
 * duoc-CR-784 — ô MÃ VTBB bấm được: mở Lịch sử mua hàng của đúng mã đó (`?codes=`). Dùng ở các bảng của cụm Giá bao bì
 * (Bảng giá, Giá mua gần nhất, Tác động giá, chính Lịch sử mua hàng) để một mã là một cú bấm tới mọi lần mua của nó.
 *
 * Dừng nổi bọt cú bấm: bảng có thể đặt hành động ở cả dòng (bấm đúp / bấm dòng) — bấm mã thì chỉ đi tới lịch sử.
 *
 * bao-CR-792 — mỗi màn của cụm một khóa riêng: đích là màn Lịch sử mua hàng nên đòi `packaging_history.read`. Không có
 * quyền thì mã là CHỮ THƯỜNG (không màu link, không bấm được) — đừng để bấm vào rồi gặp trang cấm.
 *
 * bao-CR-801 — `rawMaterial`: mã NGUYÊN LIỆU (Bảng giá nguyên liệu) mở màn Lịch sử mua nguyên liệu và đòi
 * `packaging_material_price.read`, khóa riêng của nguyên liệu. Màn Lịch sử mua hàng của VTBB không có mã nguyên liệu.
 */
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { cn } from '@/shared/utils/cn'

import {
  packagingHistoryHref,
  packagingHistoryProductHref,
  packagingMaterialHistoryHref,
} from '../utils/packaging-history'

interface PackagingCodeLinkProps {
  code: string
  className?: string
  /** `code` là mã HÀNG HÓA (sản phẩm): mở lịch sử ở chế độ "Theo mã sản phẩm" (mọi mã thành phần của định mức). */
  product?: boolean
  /** `code` là mã NGUYÊN LIỆU: mở Lịch sử mua nguyên liệu (khóa `packaging_material_price`), không phải lịch sử của VTBB. */
  rawMaterial?: boolean
}

function resolveHistoryHref(code: string, product: boolean, rawMaterial: boolean): string {
  if (rawMaterial) return packagingMaterialHistoryHref(code)
  return product ? packagingHistoryProductHref(code) : packagingHistoryHref(code)
}

export function PackagingCodeLink({
  code,
  className,
  product = false,
  rawMaterial = false,
}: PackagingCodeLinkProps) {
  const { can } = usePermission()
  if (!can(rawMaterial ? 'packaging_material_price' : 'packaging_history', 'read')) {
    return <span className={cn('font-semibold tabular-nums', className)}>{code}</span>
  }
  return (
    <Link
      to={resolveHistoryHref(code, product, rawMaterial)}
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
