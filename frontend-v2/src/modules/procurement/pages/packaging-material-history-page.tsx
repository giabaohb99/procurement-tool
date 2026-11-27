/**
 * bao-CR-801 — LỊCH SỬ MUA NGUYÊN LIỆU: mở bằng cách bấm mã ở Bảng giá nguyên liệu (`?codes=<mã>`), không có mục menu riêng.
 *
 * Dùng lại nguyên khuôn Lịch sử mua hàng của VTBB với nguồn dữ liệu của nguyên liệu (`material-history`,
 * `material-code-options`, khóa `packaging_material_price`) — khác biệt giữa hai màn ghi ở `packaging-history-page.tsx`.
 */
import { PackagingHistoryPage } from './packaging-history-page'

export function PackagingMaterialHistoryPage() {
  return <PackagingHistoryPage rawMaterial />
}
