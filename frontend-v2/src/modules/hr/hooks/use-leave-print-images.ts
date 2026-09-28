import { useEffect, useState } from 'react'

import { fetchBlobUrl } from '@/core/api'
import { leaveAttachmentViewUrl, type LeaveAttachment } from '../api/leave-attachment-api'

export interface PrintImageSource {
  id: number
  filename: string
  /** `blob:` URL đã giải mã xong; `null` = lấy không được; `undefined` = đang nạp. */
  src: string | null | undefined
}

/**
 * Giải mã ảnh TRƯỚC khi báo sẵn sàng: `window.print()` chụp trang ngay lúc gọi,
 * ảnh chưa vẽ xong là trang A4 đó in ra trắng. `decode()` không có ở mọi môi
 * trường (jsdom) — thiếu thì bỏ qua, `<img>` vẫn tự vẽ khi có.
 */
async function decodeImage(url: string): Promise<void> {
  const image = new Image()
  image.src = url
  if (typeof image.decode === 'function') await image.decode()
}

/**
 * Nạp ẢNH ĐÍNH KÈM cho bản in đơn nghỉ phép (bao-CR-505).
 *
 * Ảnh là tệp RIÊNG TƯ: `<img src="/api/attachments/1/view">` thì trình duyệt tự
 * đi lấy và KHÔNG mang token — 401. Phải lấy blob qua `httpClient` rồi dựng
 * `blob:` URL; hook tự thu hồi chúng khi rời trang hoặc danh sách ảnh đổi.
 *
 * `ready` chỉ bật khi MỌI ảnh đã về và giải mã xong (hoặc đã hỏng hẳn) — nút In
 * khóa tới lúc đó, không thì bấm sớm là mặt sau in ra trang trắng.
 */
export function useLeavePrintImages(images: readonly LeaveAttachment[]) {
  //  Khóa theo DANH SÁCH ID chứ không theo tham chiếu mảng: mỗi lượt render bên
  //  gọi dựng mảng mới, theo tham chiếu là effect chạy lại vô tận.
  const key = images.map((image) => image.id).join(',')
  const [loaded, setLoaded] = useState<{ key: string; urls: Record<number, string | null> }>({
    key: '',
    urls: {},
  })

  useEffect(() => {
    if (!key) return
    const ids = key.split(',').map(Number)
    let cancelled = false
    const created: string[] = []

    void Promise.all(
      ids.map(async (id): Promise<[number, string | null]> => {
        try {
          const url = await fetchBlobUrl(leaveAttachmentViewUrl(id))
          if (cancelled) {
            URL.revokeObjectURL(url)
            return [id, null]
          }
          created.push(url)
          await decodeImage(url).catch(() => undefined)
          return [id, url]
        } catch {
          return [id, null]
        }
      }),
    ).then((entries) => {
      if (!cancelled) setLoaded({ key, urls: Object.fromEntries(entries) })
    })

    return () => {
      cancelled = true
      for (const url of created) URL.revokeObjectURL(url)
    }
  }, [key])

  const settled = loaded.key === key
  const sources: PrintImageSource[] = images.map((image) => ({
    id: image.id,
    filename: image.filename,
    src: settled ? (loaded.urls[image.id] ?? null) : undefined,
  }))
  return { sources, ready: key === '' || settled }
}
