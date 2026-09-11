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

/**
 * bao-CR-364 — nhãn tiền tệ của một bảng TỔNG phải lấy từ các DÒNG, không lấy từ đầu phiếu.
 *
 * Từ `bao-CR-319` mỗi dòng hàng mang tiền tệ + tỷ giá riêng, còn đầu phiếu chỉ là giá trị
 * mặc định cho dòng nào để trống. Đơn đầu phiếu ghi `VND` mà dòng ghi `USD` là chuyện bình
 * thường — khi đó dán nhãn theo đầu phiếu ra ngay `6.500 VND` bên cạnh `Quy đổi 172.250.000 đ`.
 *
 * Trả về `mixed = true` khi các dòng KHÔNG cùng một loại tiền. Lúc đó cộng ngang các dòng là
 * vô nghĩa (USD cộng VND), nên nơi gọi phải chuyển sang bày bản quy đổi chứ đừng dán đại một
 * nhãn nào lên tổng đó.
 */
export function resolveTotalsCurrency(lineCurrencies: any[], fallback: string) {
  const found: string[] = []
  for (const raw of lineCurrencies || []) {
    const cur = String(raw || '').trim() || fallback
    if (cur && !found.includes(cur)) found.push(cur)
  }
  return { currency: found.length === 1 ? found[0] : fallback, mixed: found.length > 1 }
}
