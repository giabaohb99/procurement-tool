import { PACKAGING_ENTITY, fetchMaterialCodeOptions, fetchMaterialHistory } from '../../api/packaging-cost'
import type { PackagingMaterialHistoryParams } from '../../api/packaging-cost-types'
import { buildMaterialHistoryParams } from '../../utils/packaging-query'
import { PackagingHistoryScreen, type HistorySource } from './PackagingHistory'

/**
 * Nguồn của màn lịch sử nguyên liệu (bao-CR-801): CHỈ các đường `material-*` và khóa quyền `packaging_material_price`.
 * Tuyệt đối không gọi đường của VTBB (`history`, `code-options`, `fg-options`) — người chỉ có khóa nguyên liệu sẽ bị 403,
 * và các đường đó nay không trả mã nguyên liệu.
 */
const MATERIAL_HISTORY_SOURCE: HistorySource<PackagingMaterialHistoryParams> = {
  entity: PACKAGING_ENTITY.materialPrices,
  packaging: false,
  tableKey: 'packaging-material-history',
  title: 'Lịch sử mua nguyên liệu',
  hint: 'Từng lần mua của mã nguyên liệu, mới nhất trước. Giá VNĐ, chưa VAT, là bản chụp lúc mua: đỏ = đắt hơn lần trước, xanh = rẻ hơn.',
  codeLabel: 'Mã nguyên liệu',
  nameLabel: 'Tên nguyên liệu',
  pickerKind: 'ingredient',
  pickerPlaceholder: 'Tất cả mã nguyên liệu — gõ mã, tên, nhóm hoặc NCC để chọn mã cụ thể',
  codesError: 'Không nạp được danh sách mã nguyên liệu',
  exportPath: 'material-history',
  exportName: 'lich-su-mua-nguyen-lieu.xlsx',
  buildParams: buildMaterialHistoryParams,
  fetchList: fetchMaterialHistory,
  fetchCodes: fetchMaterialCodeOptions,
}

/**
 * LỊCH SỬ MUA NGUYÊN LIỆU (bao-CR-801): từng lần mua của mã nguyên liệu (sản phẩm nhóm `NL`), mở bằng cách bấm mã ở màn
 * Bảng giá nguyên liệu (`?codes=<mã>`); không có mục menu riêng, đang ở đây thì mục Bảng giá nguyên liệu vẫn sáng. Dùng
 * CHUNG khung `PackagingHistoryScreen` với màn Lịch sử mua hàng của VTBB — thẻ số liệu, biểu đồ diễn biến đơn giá khi chọn
 * đúng một mã, lọc + xếp + phân trang tại máy chủ, lựa chọn mã nằm ở URL.
 * Khác màn VTBB: chỉ có chế độ theo mã (không có "Theo mã sản phẩm"), không có nút Nạp sổ Misa và nút In, mã trong bảng là
 * chữ thường; cột Nguồn vẫn dẫn sang đơn mua hàng. Xuất Excel theo quyền `packaging_material_price.export`.
 */
export default function PackagingMaterialHistory() {
  return <PackagingHistoryScreen source={MATERIAL_HISTORY_SOURCE} />
}
