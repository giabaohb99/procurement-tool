import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../auth/AuthContext'
import { PACKAGING_ENTITY, type PackagingEntity } from '../../api/packaging-cost'
import { PACKAGING_PATHS } from '../../utils/packaging-query'
import NotFound from '../NotFound'

/**
 * Cổng quyền của các màn riêng cụm Giá nguyên vật liệu sản xuất (menu đã ẩn mục khi thiếu quyền, nhưng gõ thẳng đường dẫn vẫn tới được).
 * bao-CR-792: mỗi màn một khóa quyền — route truyền khóa của màn mình qua `entity`.
 * Chỉ là tiện ích giao diện — backend `require("<khóa của màn>", "read")` mới là chốt thật.
 */
export default function PackagingGate({ entity, children }: { entity: PackagingEntity; children: ReactNode }) {
  const { can } = useAuth()
  if (!can(entity, 'read')) {
    return <NotFound title="Không có quyền xem" backTo="/" message="Bạn không có quyền xem màn này của cụm Giá nguyên vật liệu sản xuất." />
  }
  return <>{children}</>
}

/**
 * Thứ tự màn như menu trái — đường gốc `/packaging-cost` mở màn ĐẦU TIÊN người dùng xem được.
 * bao-CR-800: thêm Bảng giá nguyên liệu (khóa riêng) — người CHỈ có khóa đó được đưa thẳng xuống màn nguyên liệu.
 */
const INDEX_ORDER = ['impact', 'products', 'priceList', 'materialPrices', 'lastPrices', 'history', 'boms'] as const

/** bao-CR-792 — đường gốc của cụm: trước luôn về Tác động giá; nay người không có khóa màn đó được đưa tới màn đầu tiên mình có quyền xem. */
export function PackagingIndexRedirect() {
  const { can } = useAuth()
  const first = INDEX_ORDER.find((k) => can(PACKAGING_ENTITY[k], 'read'))
  if (!first) {
    return <NotFound title="Không có quyền xem" backTo="/" message="Bạn không có quyền xem cụm Giá nguyên vật liệu sản xuất." />
  }
  return <Navigate to={PACKAGING_PATHS[first]} replace />
}
