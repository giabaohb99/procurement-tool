import { AlertTriangle, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { apiGet, extractErrorMessage, fetchBlobUrl } from '@/core/api'
import { useAuth } from '@/core/auth/use-auth'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { isImage, viewAsHtml } from '../helpers/inline-viewable'
import { buildWordPreviewPage } from '../helpers/word-preview-page'

/**
 * Chiều cao «hết màn hình» của khung xem ở tab «Văn bản»: trừ thanh trên của
 * ứng dụng + tiêu đề văn bản + dải tab + lề trang (~11rem). Ảnh chụp màn
 * hình 24/09/2026: khung 70dvh chừa một khoảng trắng lớn phía dưới.
 */
const FILL_HEIGHT = 'h-[calc(100dvh-11rem)]'

export interface AttachmentViewerPaneProps {
  linkId: number
  filename: string
  contentType?: string
  /** Số hiệu văn bản, in vào watermark để ảnh chụp lọt ra ngoài còn truy được. */
  documentCode?: string
  className?: string
  /**
   * Báo LÊN NGOÀI khi tệp không mở được (403 hết hạn xem, 403 mất quyền giữa
   * chừng, 404…) — tab «Tệp» (phase 09) dùng để đánh dấu KHÓA trên cây và bỏ
   * qua tệp đó khi bấm nút trước/sau (bộ luật «Thấy một phần», phase 04).
   * Không truyền = chỉ hiện câu báo tại chỗ như trước, không báo ra ngoài.
   */
  onViewError?: (message: string) => void
  /**
   * In chìm tên người xem · giờ · số hiệu lên mặt tệp. Mặc định BẬT (hộp thoại
   * xem tệp). Tab «Văn bản» của văn bản chỉ gồm tệp TẮT (chốt 24/09/2026 —
   * đó là chỗ đọc tệp hằng ngày, lớp chữ phủ kín trang gây khó đọc).
   */
  watermark?: boolean
  /**
   * Khung xem cao HẾT màn hình còn lại (tab «Văn bản», 24/09/2026) thay vì
   * 70% chiều cao như trong hộp thoại.
   */
  fill?: boolean
}

/**
 * RUỘT của khung xem tệp đính kèm — tách khỏi `attachment-viewer-dialog.tsx`
 * (phase 09) để tab «Tệp» dùng lại được nguyên logic blob/HTML/watermark mà
 * không phải chép: `document-file-viewer-layout.tsx` nhúng thẳng component
 * này (không bọc `Dialog`), hộp thoại cũ gọi lại nó y như trước.
 *
 * Nội dung lấy qua `GET /api/attachments/{id}/view` (có kiểm quyền **và kiểm hạn
 * xem**), dựng thành `blob:` URL rồi nhúng bằng `<img>` với ảnh, `<iframe>` với
 * PDF. Không dùng thẳng `url` của kho lưu trữ: đó là đường đọc thẳng bucket,
 * không qua lớp kiểm nào.
 *
 * ⚠️ **WATERMARK KHÔNG PHẢI LÀ CHỐNG CHỤP MÀN HÌNH.** Trên nền web không có
 * cách nào làm ảnh chụp ra đen — cơ chế của Netflix (Widevine/FairPlay qua
 * EME → CDM → TEE) chỉ chạy cho **video mã hóa**, không áp được cho PDF hay
 * ảnh. Thứ lớp này làm được là **truy ngược**: ảnh chụp lọt ra ngoài thì trên
 * mặt nó có sẵn tên người xem, giờ xem và số hiệu văn bản. Răn đe + bằng chứng,
 * không phải hàng rào.
 *
 * ⚠️ Dùng `key={linkId}` ở nơi gọi — đổi tệp là DỰNG LẠI component này để nó
 * khởi động với state trống sẵn, không phải tự dọn state trong effect (vừa dễ
 * sót vừa là kiểu đặt state đồng bộ trong effect mà `react-hooks` chặn).
 */
export function AttachmentViewerPane({
  linkId,
  filename,
  contentType,
  documentCode,
  className,
  onViewError,
  watermark = true,
  fill = false,
}: AttachmentViewerPaneProps) {
  const { user } = useAuth()
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  //  Word/Markdown/HTML đi đường khác: máy chủ đổi sang HTML rồi mới trả về.
  const [html, setHtml] = useState<string | null>(null)
  const [loi, setLoi] = useState('')
  const toHtml = viewAsHtml(contentType, filename)

  useEffect(() => {
    let huy = false
    let createdUrl = ''

    function baoLoi(error: unknown) {
      if (huy) return
      const message = extractErrorMessage(error)
      setLoi(message)
      onViewError?.(message)
    }

    if (toHtml) {
      apiGet<{ html: string }>(`/api/attachments/${linkId}/preview`)
        .then((data) => !huy && setHtml(data.html))
        .catch(baoLoi)
      return () => {
        huy = true
      }
    }

    fetchBlobUrl(`/api/attachments/${linkId}/view`)
      .then((url) => {
        createdUrl = url
        //  Đóng khung trước khi tải xong thì thu hồi ngay, đừng gán vào state
        //  của một component sắp biến mất.
        if (huy) URL.revokeObjectURL(url)
        else setBlobUrl(url)
      })
      .catch(baoLoi)

    return () => {
      huy = true
      //  Blob sống tới khi đóng tab nếu không thu hồi — tệp 30MB thấy ngay.
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps -- `onViewError` cố ý không nằm trong deps: nó thường là một hàm mới mỗi lượt render của nơi gọi, đưa vào đây sẽ dựng lại yêu cầu tải liên tục dù `linkId` không đổi.
  }, [linkId, toHtml])

  const nhan = [user?.full_name || user?.email, formatDateTime(new Date()), documentCode]
    .filter(Boolean)
    .join(' · ')

  return (
    <div className={className}>
      {loi && (
        <p
          role="alert"
          className="flex items-start gap-2 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900"
        >
          <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
          {loi}
        </p>
      )}

      {/*  `relative` + lớp watermark tuyệt đối phủ lên trên. `select-none` và
             `pointer-events-none` để lớp chữ không chắn thao tác cuộn PDF. */}
      <div
        className={cn(
          'relative min-h-64 overflow-auto rounded-md border bg-muted/30',
          fill ? FILL_HEIGHT : 'max-h-[70dvh]',
        )}
      >
        {!blobUrl && !html && !loi && (
          <div className="flex h-64 items-center justify-center text-muted-foreground">
            <Loader2 className="size-5 animate-spin" />
          </div>
        )}

        {/*  WORD/MD/HTML: nội dung đã đổi sang HTML, đổ vào iframe bằng `srcDoc`.
             `sandbox=""` (rỗng = chặn HẾT) nên script trong đó không chạy được
             và không với tới trang cha — an toàn hơn hẳn chèn thẳng vào DOM của
             ứng dụng. Kèm theo: CSS của tài liệu không lem ra giao diện. */}
        {html !== null && (
          <iframe
            srcDoc={buildWordPreviewPage(html)}
            title={filename}
            sandbox=""
            className={cn('w-full bg-white', fill ? 'h-full' : 'h-[70dvh]')}
          />
        )}

        {blobUrl &&
          (isImage(contentType) ? (
            <img src={blobUrl} alt={filename} className="mx-auto block max-w-full" />
          ) : (
            //  `<iframe>` chứ không `<embed>`: trình xem PDF sẵn có của trình
            //  duyệt chạy trong khung riêng, và backend đã gắn
            //  `Content-Security-Policy: sandbox` cho nội dung này.
            <iframe
              src={blobUrl}
              title={filename}
              className={cn('w-full', fill ? 'h-full' : 'h-[70dvh]')}
            />
          ))}

        {watermark && (blobUrl || html !== null) && (
          <div
            aria-hidden
            className="pointer-events-none absolute inset-0 flex flex-wrap content-start gap-x-16 gap-y-20 overflow-hidden p-8 select-none"
          >
            {/*  Lặp lại đủ dày để cắt cúp một góc ảnh chụp vẫn còn nguyên một
                   dòng chữ. Nghiêng để khó xóa bằng công cụ sửa ảnh. */}
            {Array.from({ length: 24 }).map((_, index) => (
              <span
                key={index}
                className="rotate-[-24deg] text-[13px] font-semibold whitespace-nowrap text-black/12"
              >
                {nhan}
              </span>
            ))}
          </div>
        )}
      </div>

      {watermark && (
        <p className="text-xs text-muted-foreground">
          Tệp đang mở trong phiên của <strong>{user?.full_name || user?.email}</strong> — tên bạn
          được in chìm trên mặt tài liệu.
        </p>
      )}
    </div>
  )
}
