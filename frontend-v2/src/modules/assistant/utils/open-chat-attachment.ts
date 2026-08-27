import { toast } from 'sonner'

import { fetchBlobUrl } from '@/core/api'

/**
 * Mở XEM LẠI một tệp đã đính kèm chat trong tab mới (bấm chip trên bong bóng tin).
 *
 * Endpoint `/api/assistant/uploads/:id` cần token Bearer nên không gắn href thẳng
 * được — phải kéo blob qua `fetchBlobUrl` rồi trỏ tab sang `blob:` URL.
 *
 * ⚠️ Tab phải mở TRƯỚC khi fetch: `window.open` gọi sau `await` là đã ra khỏi
 * ngữ cảnh cú bấm, trình chặn popup nuốt mất tab (Chrome chặn im lặng luôn).
 * Mở tab trắng ngay trong cú bấm, tải xong mới trỏ nó sang tệp.
 */
export async function openChatAttachment(id: number): Promise<void> {
  const win = window.open('', '_blank')
  try {
    const url = await fetchBlobUrl(`/api/assistant/uploads/${id}`)
    if (win) {
      win.location.href = url
      //  Thu hồi TRỄ: gỡ ngay thì tab mới chưa kịp nạp blob. Một phút là quá đủ
      //  để trang load; ảnh/PDF đã hiện thì không cần URL sống nữa.
      setTimeout(() => URL.revokeObjectURL(url), 60_000)
    } else {
      URL.revokeObjectURL(url)
      toast.error('Trình duyệt chặn mở tab mới — cho phép popup rồi thử lại')
    }
  } catch {
    //  Lỗi GET không tự toast ở tầng API (chỉ non-GET mới tự) — báo tay ở đây.
    win?.close()
    toast.error('Không mở được tệp đính kèm')
  }
}
