/**
 * Độ trễ giả cho lớp dữ liệu mẫu của phân hệ Hồ sơ.
 *
 * Có nó thì màn hình đi qua đúng trạng thái *đang tải* / *đang lưu* mà khung
 * chung vẽ sẵn; không có thì khung xương và vòng xoay không bao giờ hiện, và lỗi
 * bố cục ở những trạng thái đó chỉ lộ ra vào ngày nối API thật.
 *
 * Xóa cả tệp khi phân hệ gọi API thật.
 */
export function fakeLatency(ms = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}
