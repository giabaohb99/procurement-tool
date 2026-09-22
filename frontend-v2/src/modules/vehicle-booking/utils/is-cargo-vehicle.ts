/**
 * Xe CHỞ HÀNG hay CHỞ NGƯỜI — đoán theo tên loại xe người dùng tự gõ.
 *
 * ⚠️ `tab_vehicle.type` là chữ TỰ DO (ô nhập text, không phải ô chọn), nên đây
 * là phép đoán chứ không phải sự thật khai báo. Cố ý gom về một chỗ: cùng một
 * phép đoán vừa chọn biểu tượng (`VehicleTypeIcon`) vừa chọn ĐƠN VỊ của cột
 * *Sức chứa* ("tấn" hay "chỗ"), hai nơi đó lệch nhau là bảng hiện "2,4 chỗ".
 *
 * ⚠️ **«Xe bán tải» KHÔNG phải xe chở hàng ở đây.** Nó có chữ "tải" nên bản đầu
 * xếp nhầm vào nhóm tấn, và bốn chiếc Hilux/BT50 trong danh mục hiện ra
 * «5 tấn» — thật ra là 5 CHỖ. Đội xe khai `capacity` của bán tải theo số chỗ
 * ngồi, nên luật phải loại nó ra trước khi bắt chữ "tải".
 */
export function isCargoVehicle(type: string): boolean {
  const name = type.toLowerCase()
  if (name.includes('bán tải')) return false
  return name.includes('tải')
}
