// Bắt sự kiện cài PWA SỚM & TOÀN CỤC. Phải import trong main.tsx trước khi render,
// vì Edge/Chrome bắn `beforeinstallprompt` rất sớm lúc load — nếu đợi component mount sẽ lỡ event.

type BIPEvent = Event & {
  prompt: () => Promise<void>
  userChoice: Promise<{ outcome: 'accepted' | 'dismissed' }>
}

let deferred: BIPEvent | null = null
const listeners = new Set<() => void>()
const emit = () => listeners.forEach((l) => l())

if (typeof window !== 'undefined') {
  window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault()          // chặn mini-infobar mặc định, tự hiện UI của mình
    deferred = e as BIPEvent
    emit()
  })
  window.addEventListener('appinstalled', () => { deferred = null; emit() })
}

/** Có sẵn prompt cài (Chromium: Edge/Chrome/Android) hay chưa. */
export const canInstall = () => deferred !== null

/** Đăng ký lắng nghe thay đổi trạng thái cài được; trả hàm huỷ đăng ký. */
export const onInstallChange = (cb: () => void) => {
  listeners.add(cb)
  return () => { listeners.delete(cb) }
}

/** Bật hộp thoại cài của trình duyệt. Trả true nếu user đồng ý cài. */
export async function promptInstall(): Promise<boolean> {
  if (!deferred) return false
  await deferred.prompt()
  const { outcome } = await deferred.userChoice
  deferred = null
  emit()
  return outcome === 'accepted'
}
