// Ép tab đang chạy bản cũ lên bản mới — được importScripts vào service worker do vite-plugin-pwa sinh.
//
// SW mới tự kích hoạt ngay (skipWaiting), nhưng tab đang mở vẫn chạy JS cũ. Lúc kích hoạt, SW hỏi
// từng tab: bản từ duoc-CR-685 trở đi có nghe tin nhắn này và trả lời (tự lo popup + tải lại lúc 0h);
// tab không trả lời là bản cũ, không biết tự cập nhật → SW điều hướng lại tab đó sang bản mới.
const PWA_PING = 'PWA_VERSION_PING'
const PWA_REPLY_TIMEOUT_MS = 3000

/** true = tab có trả lời (bản mới tự lo); false = im lặng (bản cũ). */
function askClientHandlesUpdate(client) {
  return new Promise((resolve) => {
    const channel = new MessageChannel()
    const timer = setTimeout(() => resolve(false), PWA_REPLY_TIMEOUT_MS)
    channel.port1.onmessage = () => { clearTimeout(timer); resolve(true) }
    try {
      client.postMessage({ type: PWA_PING }, [channel.port2])
    } catch (e) {
      clearTimeout(timer)
      resolve(false)
    }
  })
}

async function reloadOutdatedTabs() {
  const tabs = await self.clients.matchAll({ type: 'window' })
  await Promise.all(tabs.map(async (tab) => {
    if (await askClientHandlesUpdate(tab)) return
    try { await tab.navigate(tab.url) } catch (e) { /* tab đã đóng / khác nguồn → bỏ qua */ }
  }))
}

self.addEventListener('activate', (event) => {
  // Chỉ giữ activate tới lúc chiếm quyền tab (navigate() đòi tab phải do SW này điều khiển);
  // phần hỏi-đáp chạy sau, không bắt các request của trang chờ 3 giây.
  event.waitUntil(self.clients.claim().then(() => { reloadOutdatedTabs() }))
})
