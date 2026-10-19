/** Chuyển trình duyệt về ứng dụng AI sau khi đồng ý / từ chối OAuth (ai-CR-218) — tách tệp để bài kiểm thay được
 *  (jsdom không cho đổi `window.location`). */
export function goTo(url: string) {
  window.location.assign(url)
}
