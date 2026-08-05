// Quill mặc định: nút trên thanh công cụ KHÔNG có tooltip (người soạn bài nhìn icon không đoán ra
// nút nào là nút gì — nhất là nút "nhúng video" trông như cuộn phim), và ô dán URL thì ghi tiếng Anh.
// Bù cả hai bằng tay sau khi Quill dựng xong thanh công cụ. Nhãn còn lại của ô dán URL
// (Dán URL nhúng: / Lưu / Xóa) đổi bằng CSS trong styles/article-content.css.

/** Chọn nút trên thanh công cụ -> nội dung tooltip. Nút nào Quill không dựng thì bỏ qua. */
const TITLES: Record<string, string> = {
  '.ql-header': 'Cỡ chữ / tiêu đề',
  '.ql-bold': 'In đậm (Ctrl+B)',
  '.ql-italic': 'In nghiêng (Ctrl+I)',
  '.ql-underline': 'Gạch chân (Ctrl+U)',
  '.ql-strike': 'Gạch ngang',
  '.ql-color': 'Màu chữ',
  '.ql-background': 'Màu nền chữ',
  '.ql-list[value="ordered"]': 'Danh sách đánh số',
  '.ql-list[value="bullet"]': 'Danh sách gạch đầu dòng',
  '.ql-align': 'Canh lề',
  '.ql-link': 'Chèn liên kết',
  '.ql-image': 'Chèn ảnh (tải từ máy lên)',
  '.ql-video': 'Nhúng video / demo — dán URL nhúng (YouTube, Guideflow...)',
  '.ql-clean': 'Xóa định dạng',
}

/** Gợi ý trong ô dán URL. Quill gán placeholder từ chính data-attribute này lúc mở ô. */
const URL_PLACEHOLDERS: Record<string, string> = {
  link: 'https://vi-du.com/trang-can-dan',
  video: 'Dán URL nhúng, vd https://app.guideflow.com/embed/abc123',
}

/** Việt hóa thanh công cụ Quill trong `root`. Gọi lại được nhiều lần (idempotent). */
export function applyQuillVietnameseLabels(root: ParentNode | null = document): void {
  if (!root) return

  root.querySelectorAll('.hc-editor .ql-toolbar').forEach((toolbar) => {
    Object.entries(TITLES).forEach(([selector, title]) => {
      toolbar.querySelectorAll<HTMLElement>(selector).forEach((el) => {
        el.title = title
      })
    })
  })

  root.querySelectorAll<HTMLInputElement>('.hc-editor .ql-tooltip input[type="text"]').forEach((input) => {
    Object.entries(URL_PLACEHOLDERS).forEach(([mode, text]) => {
      input.dataset[mode] = text
    })
  })
}
