import { appRoutes } from '@/shared/constants/app-routes'

/**
 * Nhãn và đường dẫn của từng loại chứng từ chạy qua bộ máy duyệt.
 *
 * Bộ máy duyệt cố ý **không biết** gì về các loại chứng từ — nó chỉ giữ `entity`
 * dạng chuỗi. Bảng tra này là chỗ duy nhất trong giao diện nối chuỗi đó với một
 * màn hình thật. Thêm loại chứng từ mới = thêm một dòng ở đây.
 */
export const ENTITY_LABELS: Record<string, string> = {
  document: 'Văn bản',
  purchase_request: 'Yêu cầu mua hàng',
  purchase_order: 'Đơn mua hàng',
  survey: 'Khảo sát',
  survey_request: 'Yêu cầu báo giá',
  payment_request: 'Yêu cầu thanh toán',
  vehicle_booking: 'Đặt xe',
}

/** Danh sách mã loại chứng từ, dùng cho ô lọc và cụm công tắc bộ máy. */
export const CAC_LOAI = Object.keys(ENTITY_LABELS)

const ENTITY_ROUTES: Record<string, (id: number) => string> = {
  document: appRoutes.document.documentDetail,
  purchase_request: appRoutes.procurement.purchaseRequestDetail,
  purchase_order: appRoutes.procurement.purchaseOrderDetail,
  vehicle_booking: appRoutes.vehicleBooking.detail,
}

/**
 * Đường tới chính chứng từ đó. Loại chưa có màn chi tiết ở v2 thì trả về
 * **chuỗi rỗng** — chỗ gọi hiện chữ thường thay vì một link.
 *
 * Trước đây rơi về hộp việc «Việc của tôi». Màn đó đã xóa (21/08/2026), mà kể
 * cả còn thì đó cũng là câu trả lời sai: bấm "mở chứng từ" rồi quay lại chính
 * danh sách vừa đứng thì người dùng tưởng nút hỏng.
 */
export function entityLink(entity: string, entityId: number): string {
  const build = ENTITY_ROUTES[entity]
  return build ? build(entityId) : ''
}
