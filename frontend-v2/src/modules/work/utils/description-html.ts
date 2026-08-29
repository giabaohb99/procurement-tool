/**
 * Mô tả công việc lưu HTML (ô nhập là trình soạn thảo rich text), nhưng cột
 * `work_task.description` đã có sẵn dữ liệu CHỮ TRƠN từ trước. Ba hàm dưới đây
 * là chỗ duy nhất biết cả hai dạng đó tồn tại.
 */

/** Bỏ thẻ, đổi vài thực thể hay gặp, gom khoảng trắng — dùng để ĐO RỖNG và để TÌM. */
export function plainText(value: string): string {
  return value
    .replace(/<[^>]*>/g, ' ')
    .replace(/&nbsp;/g, ' ')
    .replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/\s+/g, ' ')
    .trim()
}

/**
 * Mô tả có coi như trống không.
 *
 * Tiptap trả `<p></p>` cho ô vừa xóa sạch — chuỗi ấy dài 7 ký tự nhưng người
 * dùng thấy là trống, để nguyên thì panel hiện một khối trắng thay cho câu mời
 * «Thêm mô tả». Ngược lại, bài chỉ có MỘT TẤM ẢNH thì chữ trơn rỗng mà nội dung
 * thì có thật.
 */
export function isRichEmpty(value: string): boolean {
  if (/<(img|hr|table)\b/i.test(value)) return false
  return plainText(value) === ''
}

/**
 * Đưa giá trị đang lưu về HTML để nạp vào trình soạn thảo.
 *
 * Dữ liệu cũ là chữ trơn: nhét thẳng vào Tiptap thì mọi lần xuống dòng biến
 * mất (chữ trơn không có `<p>`), nên phải bọc từng dòng lại. Thoát `& < >`
 * trước, không thì một mô tả kiểu "a < b" tự biến thành thẻ.
 */
export function toRichHtml(value: string): string {
  if (!value) return ''
  //  Nhận ra HTML bằng một THẺ THẬT, không phải bằng dấu `<` lẻ: mô tả cũ
  //  "a < b" mà coi là HTML thì nó đi thẳng vào `dangerouslySetInnerHTML` và
  //  phần hiển thị hỏng từ chỗ đó trở đi.
  if (/<\/?[a-z][^>]*>/i.test(value)) return value
  return value
    .split('\n')
    .map((dong) => `<p>${escapeHtml(dong)}</p>`)
    .join('')
}

function escapeHtml(value: string): string {
  return value.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
}
