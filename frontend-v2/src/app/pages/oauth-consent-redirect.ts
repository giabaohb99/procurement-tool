/** Chuyển trình duyệt về ứng dụng AI sau khi đồng ý / từ chối OAuth (ai-CR-218) — tách tệp để bài kiểm thay được
 *  (jsdom không cho đổi `window.location`). */
export function goTo(url: string) {
  window.location.assign(url)
}

/** ai-CR-222: màn đồng ý đang bị nhúng trong khung (iframe) — lớp chặn thứ hai sau header chống nhúng của nginx. So sánh
 *  tham chiếu `window.top` được phép cả khi khung cha khác nguồn. */
export function isFramed(): boolean {
  try {
    return window.top !== window.self
  } catch {
    return true
  }
}
