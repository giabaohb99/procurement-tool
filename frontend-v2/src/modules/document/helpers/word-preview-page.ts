/**
 * Giãn dòng kiểu Word do `docx_html.py` ghi là `line-height: 1.079em` — `em`
 * tính theo cỡ chữ của CHÍNH đoạn `<p>`, có chủ ý cho trình soạn thảo (xem chú
 * thích ở backend). Trong trang XEM TRƯỚC thì đoạn mang cỡ chữ mặc định của
 * trang, còn chữ thật nằm trong `<span style="font-size: 13pt">` to hơn — mỗi
 * dòng thấp hơn chữ của nó và các dòng ĐÈ lên nhau (ảnh chụp 24/09/2026). Đổi
 * về số KHÔNG đơn vị để mỗi dòng nhân theo đúng cỡ chữ đang dùng.
 *
 * Chỉ đổi `em`; `px` (giãn dòng «chính xác» của Word) giữ nguyên.
 */
export function unitlessWordLineHeights(html: string): string {
  return html.replace(/line-height:\s*(\d*\.?\d+)em/g, 'line-height: $1')
}

/**
 * Bọc HTML đã đổi từ Word thành một trang hoàn chỉnh cho `<iframe srcdoc>` —
 * dựng như TRANG GIẤY A4 căn giữa trên nền xám (24/09/2026), thay vì chữ trải
 * hết bề ngang khung xem. Phải tự khai phông/lề: iframe là tài liệu RIÊNG,
 * không thừa hưởng CSS của trang cha.
 */
export function buildWordPreviewPage(content: string): string {
  return `<!doctype html><html lang="vi"><head><meta charset="utf-8">
<style>
  html { background: #eef1f5; }
  body { margin: 0; padding: 24px 16px; }
  .page { box-sizing: border-box; max-width: 794px; min-height: 1123px; margin: 0 auto;
          padding: 72px 76px; background: #fff; box-shadow: 0 1px 4px rgba(15, 23, 42, 0.12);
          font-family: 'Times New Roman', Times, serif; font-size: 13pt; line-height: 1.3;
          color: #111827; overflow-wrap: break-word; }
  img { max-width: 100%; height: auto; }
  table { border-collapse: collapse; max-width: 100%; }
  td, th { border: 1px solid #cbd5e1; padding: 4px 8px; vertical-align: top; }
  p { margin: 0 0 6px; }
</style></head><body><div class="page">${unitlessWordLineHeights(content)}</div></body></html>`
}
