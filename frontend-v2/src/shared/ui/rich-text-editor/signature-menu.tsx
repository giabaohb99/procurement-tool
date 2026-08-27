import type { Editor } from '@tiptap/core'
import { PenLine } from 'lucide-react'
import { useState } from 'react'

import { Button } from '@/shared/ui/button'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/shared/ui/popover'
import { SIGNATURE_DEFAULT_WIDTH } from './signature-extension'

interface SignatureMenuProps {
  /** `null` khi trình soạn thảo chưa dựng xong — nút tự tắt, không tự ẩn. */
  editor: Editor | null
  /** Ảnh chữ ký của CHÍNH người đang đăng nhập (`user.signature`). */
  signatureUrl?: string
  /** Mở trang cá nhân để tải chữ ký lên; bỏ trống thì chỉ hiện lời nhắc. */
  onOpenProfile?: () => void
}

/**
 * Nút **Chữ ký** ở hàng thao tác của trang chi tiết văn bản.
 *
 * Cố tình KHÔNG nằm trong thanh công cụ soạn thảo: thanh đó là một hàng tự
 * xuống dòng, nút nào đứng cuối cũng bị đẩy xuống hàng dưới rồi lẫn vào ba chục
 * nút định dạng. Ký là một việc của cả văn bản, cùng cấp với *Lưu nội dung* hay
 * *Gửi duyệt*, nên đứng cạnh chúng.
 *
 * Chỉ nạp chữ ký của **chính người đang đăng nhập** — không có đường chọn chữ ký
 * người khác. Đây là chốt chống giả mạo quan trọng nhất của tính năng: ảnh chữ ký
 * nằm trong nội dung là thứ AI MỞ BẢN IN CŨNG THẤY, nên nếu ai soạn được văn bản
 * cũng dán được chữ ký sếp vào thì bản in mất hết giá trị đối chứng.
 *
 * ⚠️ Ảnh này **không phải chữ ký pháp lý**. Chữ ký pháp lý là bản ghi
 * `tab_signature` (ai ký phiên bản nào, kèm mã băm nội dung) — xem thẻ *Chữ ký*
 * ở trang chi tiết văn bản.
 */
export function SignatureMenu({ editor, signatureUrl, onOpenProfile }: SignatureMenuProps) {
  const [open, setOpen] = useState(false)
  const hasSignature = Boolean((signatureUrl || '').trim())

  function insertSignature() {
    if (!hasSignature || !editor) return
    //  Đặt NGAY CHỖ CON TRỎ, lệch sang phải một quãng — người dùng đặt con trỏ
    //  dưới khối "NGƯỜI KÝ" rồi bấm chèn, chữ ký rơi đúng vào đó.
    //
    //  ⚠️ `left`/`top` là ĐỘ LỆCH so với mốc neo trong dòng chảy, KHÔNG phải toạ
    //  độ trên tờ giấy (xem `signature-extension`). Đặt `top: 620` như toạ độ tờ
    //  giấy là chữ ký rơi xuống tận 620px DƯỚI con trỏ — bài ngắn thì nằm ngoài
    //  trang, chèn xong không thấy đâu.
    editor
      .chain()
      .focus()
      .insertContent({
        type: 'documentSignature',
        attrs: {
          src: signatureUrl,
          left: 340,
          top: 0,
          width: SIGNATURE_DEFAULT_WIDTH,
          height: 0,
          rotate: 0,
        },
      })
      .run()
    setOpen(false)
  }

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <Button type="button" variant="outline" disabled={!editor} title="Chèn chữ ký của bạn">
          <PenLine className="size-4" />
          Chữ ký
        </Button>
      </PopoverTrigger>

      <PopoverContent align="start" className="w-72 space-y-3">
        <div>
          <p className="text-sm font-medium">Chèn chữ ký của bạn</p>
          <p className="text-xs text-muted-foreground">
            Đặt được ở bất kỳ đâu trên trang, kéo thả · phóng to · xoay tuỳ ý.
          </p>
        </div>

        {hasSignature ? (
          <>
            {/*  Cho xem trước rồi mới chèn: chữ ký đã tải lên có thể là ảnh cũ,
                 nền chưa tách sạch — nhìn thấy trước đỡ phải chèn rồi xoá. */}
            <div className="flex items-center justify-center rounded-md border bg-muted/40 p-3">
              <img
                src={signatureUrl}
                alt="Chữ ký của bạn"
                className="max-h-20 max-w-full object-contain"
              />
            </div>
            <Button type="button" className="w-full" onClick={insertSignature}>
              Chèn vào văn bản
            </Button>
          </>
        ) : (
          <>
            <p className="rounded-md bg-accent px-3 py-2 text-xs">
              Bạn <b>chưa tải chữ ký lên</b>. Vào Trang cá nhân để tải ảnh chữ ký, sau đó
              quay lại đây.
            </p>
            {onOpenProfile && (
              <Button type="button" variant="outline" className="w-full" onClick={onOpenProfile}>
                Mở Trang cá nhân
              </Button>
            )}
          </>
        )}

        <p className="text-xs text-muted-foreground">
          Đây là <b>hình ảnh</b> đặt lên bản in, không phải chữ ký phê duyệt. Chữ ký có
          giá trị pháp lý nằm ở thẻ <b>Chữ ký</b> của văn bản.
        </p>
      </PopoverContent>
    </Popover>
  )
}
