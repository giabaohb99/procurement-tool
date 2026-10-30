import { USAGE_STYLE } from '@/shared/constants/statuses'

/**
 * Gợi ý đọc cho từng kiểu làm việc (`UsageStyle` backend, số cố định 1..10) — chép
 * bảng §4 của thiết kế, tầng hiển thị. TÊN kiểu lấy từ `USAGE_STYLE` (sinh từ
 * backend), không gõ tay ở đây. Mọi nhãn chỉ để THAM KHẢO: không phải kết luận
 * về con người, phải đối chiếu thực tế (§8).
 */
export const USAGE_STYLE_HINTS: Record<number, string> = {
  1: 'Việc dồn vào cuối tháng hoặc vài khung giờ. Xem lịch việc có theo kỳ chốt không.',
  2: 'Phiếu chờ người này lâu hơn nhóm. Xem họ có đang quá tải hay thiếu người thay.',
  3: 'Hay xuất Excel đều đặn. Có thể màn chưa đủ báo cáo họ cần.',
  4: 'Mới vào, nhiều lỗi nhập hoặc bỏ form. Nên kèm cặp hoặc bổ sung hướng dẫn.',
  5: 'Dùng nhiều màn, ít lỗi, có lưu bộ lọc. Có thể nhờ hướng dẫn người khác.',
  6: 'Hay bị chặn quyền hoặc đi vòng giữa các màn. Xem phân quyền và đường vào màn.',
  7: 'Phần lớn thao tác ghi trên điện thoại. Cần màn di động đủ dùng.',
  8: 'Phiếu hay bị trả về hoặc sửa sau khi gửi. Xem biểu mẫu có khó hiểu không.',
  9: 'Nhiều phiếu do người khác lập hộ. Xem người đó có cần thêm quyền hay hướng dẫn.',
  10: 'Ít vào hệ thống so với nhóm. Có thể việc của họ ít qua hệ thống — hỏi trước khi kết luận.',
}

/** Tên kiểu theo mã; mã lạ (backend thêm trước FE) hiện "Kiểu N". */
export function styleLabel(code: number): string {
  return USAGE_STYLE.find((o) => o.value === String(code))?.label ?? `Kiểu ${code}`
}
