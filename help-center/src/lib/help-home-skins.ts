// Nền gradient + ảnh minh họa cho tile "Bắt đầu ngay" ở trang chủ.
//
// Backend chỉ lưu SLUG (cột `gradient` String(30)) chứ không lưu chuỗi CSS — đổi bảng màu sau này
// chỉ phải sửa ở đây, không phải chạy migration hay sửa dữ liệu đã lưu.
// Chưa chọn thì tile tự lấy nền/ảnh xoay vòng theo vị trí, nên trang chủ không bao giờ trống trơn.

export interface HomeGradient {
  slug: string
  label: string
  css: string
}

export const HOME_GRADIENTS: HomeGradient[] = [
  { slug: 'blue', label: 'Xanh dương', css: 'linear-gradient(135deg, #e4f7ff 0%, #bde1ff 100%)' },
  { slug: 'violet', label: 'Tím', css: 'linear-gradient(135deg, #e6e6ff 0%, #cccdff 100%)' },
  { slug: 'pink', label: 'Hồng', css: 'linear-gradient(135deg, #fae6ff 0%, #efc2ff 100%)' },
  { slug: 'mint', label: 'Xanh bạc hà', css: 'linear-gradient(135deg, #e3fbf1 0%, #bdf0da 100%)' },
  { slug: 'amber', label: 'Vàng', css: 'linear-gradient(135deg, #fff5e0 0%, #ffe0ad 100%)' },
]

/** Ảnh minh họa dựng sẵn trong `public/`. */
export const HOME_ILLUSTRATIONS = [
  { url: '/hc_overview.png', label: 'Tổng quan' },
  { url: '/hc_new_user.png', label: 'Người dùng mới' },
  { url: '/hc_admin.png', label: 'Quản trị' },
]

/** CSS nền của tile. Chưa chọn slug (hoặc slug lạ) -> lấy theo vị trí cho khỏi trùng nhau. */
export function gradientCss(slug: string | null | undefined, index = 0): string {
  return (HOME_GRADIENTS.find((g) => g.slug === slug) ?? HOME_GRADIENTS[index % HOME_GRADIENTS.length]).css
}

/** Ảnh minh họa của tile. Chưa chọn -> lấy theo vị trí. */
export function illustrationUrl(url: string | null | undefined, index = 0): string {
  return url || HOME_ILLUSTRATIONS[index % HOME_ILLUSTRATIONS.length].url
}
