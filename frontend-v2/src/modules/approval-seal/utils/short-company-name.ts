//  Tiền tố loại hình doanh nghiệp — bỏ đi khi BÀY TÊN TRONG BẢNG. Gần như pháp
//  nhân nào cũng mang nó, nên giữ lại thì mọi dòng đều mở đầu bằng cùng một cụm
//  20 ký tự và phần phân biệt bị đẩy ra ngoài mép cột. Cùng bài học với
//  `ORG_UNIT_PREFIX` của `shared/utils/name-initials.ts`.
//
//  Khớp lần lượt: "công ty"/"cty" → loại hình (tnhh · cổ phần · cp) → biến thể
//  (một thành viên · mtv). Mỗi phần đều TÙY CHỌN sau phần đầu, vì thực tế có đủ
//  "CÔNG TY TNHH MTV", "CÔNG TY CỔ PHẦN" lẫn "CÔNG TY" trơn.
const COMPANY_PREFIX =
  /^(?:công\s*ty|cty)\s*(?:tnhh|trách\s*nhiệm\s*hữu\s*hạn|cổ\s*phần|cp)?\s*(?:một\s*thành\s*viên|mtv)?\s*/i

/**
 * Tên công ty RÚT GỌN để bày trong ô bảng ("CÔNG TY TNHH SẢN XUẤT HÓA CHẤT ABA"
 * → "SẢN XUẤT HÓA CHẤT ABA").
 *
 * ⚠️ CHỈ dùng cho chỗ hiển thị chật (ô bảng, chip). Bản in, biểu mẫu, chú giải
 * khi rê chuột và mọi thứ gửi ra ngoài phải giữ TÊN ĐẦY ĐỦ — đó là tên pháp lý.
 *
 * Cắt xong mà rỗng (tên chỉ có mỗi tiền tố, hoặc dữ liệu nhập dở) thì trả về
 * tên gốc: thà dài còn hơn ô trống.
 */
export function shortCompanyName(name: string): string {
  //  Gộp mọi khoảng trắng về một dấu cách: tên nhập tay hay dính hai dấu cách
  //  hoặc tab, làm biểu thức trên trượt.
  const full = name.trim().replace(/\s+/g, ' ')
  const short = full.replace(COMPANY_PREFIX, '').trim()
  return short || full
}
