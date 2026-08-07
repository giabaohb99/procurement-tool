/**
 * Định dạng số tiền / đơn giá.
 *
 * Từ khi đơn giá cho phép 4 số lẻ (migration `d4b9e7c1a305`), thành tiền = SL × đơn giá hay
 * lẻ ra vài xu. `toLocaleString('vi-VN')` mặc định cho tối đa **3** số lẻ nên số đó lòi thẳng
 * ra danh sách kiểu `4.760.000,08 đ` — tiền Việt không có đơn vị nhỏ hơn đồng.
 *
 *   fmtVND  — TIỀN (thành tiền, tổng tiền, công nợ…): làm tròn về đồng.
 *   fmtPrice — ĐƠN GIÁ: giữ đủ 4 số lẻ, nếu không mặc định 3 số sẽ cắt mất chữ số cuối.
 *
 * Hai hàm này chỉ lo phần HIỂN THỊ; giá trị lưu trong CSDL vẫn nguyên vẹn.
 */
export const PRICE_DECIMALS = 4

export const fmtVND = (n: any) => Math.round(Number(n) || 0).toLocaleString('vi-VN')

export const fmtPrice = (n: any) =>
  Number(n || 0).toLocaleString('vi-VN', { maximumFractionDigits: PRICE_DECIMALS })
