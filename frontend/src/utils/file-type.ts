// Tiện ích chung cho file đính kèm: dung lượng + icon/màu theo định dạng.
// Dùng chung ở trang Chứng từ, Đơn mua hàng, Yêu cầu mua hàng… để đồng bộ hiển thị.

export const fmtSize = (n: number) =>
  n > 1024 * 1024
    ? (n / 1048576).toFixed(1) + " MB"
    : Math.max(1, Math.round((n || 0) / 1024)) + " KB";

export const isImageFile = (filename = "", contentType = "") =>
  /^image\//.test(contentType) || /\.(png|jpe?g|webp|gif|bmp)$/i.test(filename);

export const isPdfFile = (filename = "", contentType = "") =>
  contentType === "application/pdf" || /\.pdf$/i.test(filename);

// Icon + màu theo định dạng → nhận diện nhanh (PDF đỏ · ảnh teal · Excel xanh lá · Word xanh dương)
export function fileIcon(
  filename = "",
  contentType = "",
): { icon: string; color: string } {
  const n = filename.toLowerCase();
  if (isImageFile(filename, contentType))
    return { icon: "ti-photo", color: "var(--teal)" };
  if (isPdfFile(filename, contentType))
    return { icon: "ti-file-type-pdf", color: "#dc2626" };
  if (/\.(xlsx?|csv)$/.test(n))
    return { icon: "ti-file-type-xls", color: "#16a34a" };
  if (/\.(docx?)$/.test(n))
    return { icon: "ti-file-type-docx", color: "#2563eb" };
  return { icon: "ti-file", color: "var(--muted)" };
}
