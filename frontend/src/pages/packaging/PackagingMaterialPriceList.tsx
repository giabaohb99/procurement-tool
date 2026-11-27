import { PACKAGING_ENTITY, fetchMaterialCodeOptions, fetchMaterialPriceList } from '../../api/packaging-cost'
import { PackagingPriceListScreen, type PriceListSource } from './PackagingPriceList'

/**
 * Nguồn của màn nguyên liệu (bao-CR-800): CHỈ các đường `material-*` và khóa quyền riêng `packaging_material_price`.
 * Tuyệt đối không gọi đường của Bảng giá VTBB (`price-list`, `code-options`) — người chỉ có khóa nguyên liệu sẽ bị 403.
 */
const MATERIAL_SOURCE: PriceListSource = {
  entity: PACKAGING_ENTITY.materialPrices,
  packaging: false,
  tableKey: 'packaging-material-price-list',
  title: 'Bảng giá nguyên liệu',
  hint: 'Giá cũ / mới từng mã nguyên liệu: có báo giá thì giá mới là báo giá, không thì là lần mua gần nhất. Đơn vị VNĐ, chưa VAT.',
  codeLabel: 'Mã nguyên liệu',
  nameLabel: 'Tên nguyên liệu',
  pickerKind: 'ingredient',
  pickerPlaceholder: 'Tìm mã nguyên liệu — gõ mã, tên, nhóm hoặc NCC, chọn được nhiều mã',
  emptyText: 'Chưa có nguyên liệu nào có giá.',
  exportPath: 'material-price-list',
  exportName: 'bang-gia-nguyen-lieu.xlsx',
  fetchList: fetchMaterialPriceList,
  fetchCodes: fetchMaterialCodeOptions,
}

/**
 * BẢNG GIÁ NGUYÊN LIỆU. duoc-CR-798 (27/11/2026) dựng khung y khuôn Bảng giá VTBB, bảng rỗng; bao-CR-800 nối dữ liệu thật:
 * nguyên liệu = sản phẩm nhóm `NL` đã có giá, lấy qua đường riêng `material-price-list` và gác bằng khóa quyền riêng
 * `packaging_material_price` (chủ dự án chốt 27/11/2026). Dùng CHUNG khung `PackagingPriceListScreen` với màn VTBB — phân
 * trang + xếp cột tại máy chủ, ô chọn mã, chip nhóm, khoảng ngày tính min – max, Xóa lọc, Xuất Excel (khi có quyền `export`).
 * Khác màn VTBB: không có nút phạm vi mã, không có cột Số SP đang dùng / Ghi chú / Thao tác (Báo giá), và mã nguyên liệu là
 * chữ thường (không bấm sang Lịch sử mua hàng của cụm).
 */
export default function PackagingMaterialPriceList() {
  return <PackagingPriceListScreen source={MATERIAL_SOURCE} />
}
