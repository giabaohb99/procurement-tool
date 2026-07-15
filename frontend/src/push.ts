// Web Push: đăng ký/hủy nhận thông báo đẩy trên thiết bị hiện tại.
// Service worker chỉ chạy ở bản build prod (đã cài), nên các hàm này chỉ hoạt động ở prod.
import { api } from './api/client'

function urlB64ToUint8Array(base64: string): Uint8Array {
  const padding = '='.repeat((4 - (base64.length % 4)) % 4)
  const b64 = (base64 + padding).replace(/-/g, '+').replace(/_/g, '/')
  const raw = atob(b64)
  const arr = new Uint8Array(raw.length)
  for (let i = 0; i < raw.length; i++) arr[i] = raw.charCodeAt(i)
  return arr
}

export function pushSupported(): boolean {
  return typeof navigator !== 'undefined' && 'serviceWorker' in navigator
    && 'PushManager' in window && 'Notification' in window
}

async function swReady(): Promise<ServiceWorkerRegistration> {
  // Không để treo vô hạn khi chưa có SW (vd bản dev)
  return Promise.race([
    navigator.serviceWorker.ready,
    new Promise<ServiceWorkerRegistration>((_, rej) =>
      setTimeout(() => rej(new Error('Chưa có service worker — hãy mở bản đã cài (prod) trên trình duyệt/điện thoại.')), 4000)),
  ])
}

export async function isPushSubscribed(): Promise<boolean> {
  if (!pushSupported()) return false
  try {
    const reg = await swReady()
    return !!(await reg.pushManager.getSubscription())
  } catch { return false }
}

export async function subscribePush(): Promise<void> {
  if (!pushSupported()) throw new Error('Trình duyệt không hỗ trợ thông báo đẩy.')
  const perm = await Notification.requestPermission()
  if (perm !== 'granted') throw new Error('Bạn chưa cho phép hiển thị thông báo.')
  const reg = await swReady()
  const keyRes = await api.get('/api/push/vapid-public-key')
  const sub = await reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlB64ToUint8Array(keyRes.data.data.key) as unknown as BufferSource,
  })
  await api.post('/api/push/subscribe', (sub as any).toJSON())
}

export async function unsubscribePush(): Promise<void> {
  if (!pushSupported()) return
  const reg = await swReady()
  const sub = await reg.pushManager.getSubscription()
  if (sub) {
    await api.post('/api/push/unsubscribe', { endpoint: sub.endpoint }).catch(() => {})
    await sub.unsubscribe()
  }
}
