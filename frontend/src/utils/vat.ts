/** Quy ước ô nhập VAT theo DÒNG HÀNG (khảo sát, YCMH, ĐMH).
 *
 *  Trước CR-058 các ô này là <select> khoá cứng vài mức (0/2/4/6/8/10 ở khảo sát,
 *  0/5/8/10 ở YCMH) nên không nhập được thuế suất ngoài danh sách — hàng nhập khẩu,
 *  hàng chịu thuế theo hợp đồng riêng đều phải ghi tay vào ghi chú. Giờ cho nhập số.
 *
 *  Đơn vị là PHẦN TRĂM (8 = 8%), khớp cột DB `Numeric(5,2)`. KHÁC với `vat_rate` ở
 *  phần đầu chứng từ và `supplier.vat` — hai chỗ đó lưu TỈ LỆ (0.08), không có ô nhập.
 *
 *  Chặn trên: VAT phải < 100%. `Numeric(5,2)` chỉ chứa được tối đa 999,99 nên 99,99
 *  là số lớn nhất vừa dưới 100 mà DB giữ nguyên được, dùng luôn làm mức kẹp của ô nhập.
 *  Backend chặn lại bằng `Field(ge=0, lt=100)` — UI chỉ là tiện lợi, không phải rào chắn.
 */
export const VAT_MAX = 99.99

/** VAT lẻ tới 2 chữ số thập phân, đúng bằng phần thập phân của cột `Numeric(5,2)`. */
export const VAT_DECIMALS = 2
