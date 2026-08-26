import { AlertTriangle, Loader2 } from 'lucide-react'
import { useEffect, useState } from 'react'

import { apiGet, extractErrorMessage, fetchBlobUrl } from '@/core/api'
import { useAuth } from '@/core/auth/use-auth'
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { formatDateTime } from '@/shared/utils/format-date'
import { laAnh, viewAsHtml } from '../helpers/inline-viewable'

/**
 * Bọc HTML đã chuyển từ Word thành một trang hoàn chỉnh cho `<iframe srcdoc>`.
 *
 * Phải tự khai phông và lề: iframe là một tài liệu RIÊNG, không thừa hưởng CSS
 * của trang cha — không khai thì chữ ra phông mặc định của trình duyệt, dính sát
 * mép trái.
 */
function htmlPage(content: string): string {
  return `<!doctype html><html lang="vi"><head><meta charset="utf-8">
<style>
  body { margin: 0; padding: 24px 28px; background: #fff;
         font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Arial, sans-serif;
         font-size: 14px; line-height: 1.6; color: #172554; }
  img { max-width: 100%; height: auto; }
  table { border-collapse: collapse; max-width: 100%; }
  td, th { border: 1px solid #cbd5e1; padding: 6px 10px; }
</style></head><body>${content}</body></html>`
}

interface AttachmentViewerDialogProps {
  /** `id` của FileLink — `null` là đang đóng. */
  linkId: number | null
  filename: string
  contentType?: string
  /** Số hiệu văn bản, in vào watermark để ảnh chụp lọt ra ngoài còn truy được. */
  documentCode?: string
  onClose: () => void
}

/**
 * XEM TỆP ĐÍNH KÈM NGAY TRONG TRANG — không tải về máy.
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
 */
export function AttachmentViewerDialog({
  linkId,
  filename,
  contentType,
  documentCode,
  onClose,
}: AttachmentViewerDialogProps) {
  return (
    <Dialog open={linkId !== null} onOpenChange={(open) => !open && onClose()}>
      <DialogContent className="max-w-5xl">
        <DialogHeader>
          <DialogTitle className="truncate">{filename}</DialogTitle>
        </DialogHeader>

        {/*  `key` theo tệp: đổi tệp là DỰNG LẠI khung ruột, nên nó khởi động với
             state trống sẵn. Không có nó thì phải tự dọn state trong effect —
             vừa dễ sót (thấy nội dung tệp cũ một nhịp trước khi tệp mới về), vừa
             là kiểu đặt state đồng bộ trong effect mà `react-hooks` chặn. */}
        {linkId !== null && (
          <ViewerBody
            key={linkId}
            linkId={linkId}
            filename={filename}
            contentType={contentType}
            documentCode={documentCode}
          />
        )}
      </DialogContent>
    </Dialog>
  )
}

/** Phần ruột — mỗi tệp một lần dựng mới, xem ghi chú `key` ở trên. */
function ViewerBody({
  linkId,
  filename,
  contentType,
  documentCode,
}: {
  linkId: number
  filename: string
  contentType?: string
  documentCode?: string
}) {
  const { user } = useAuth()
  const [blobUrl, setBlobUrl] = useState<string | null>(null)
  //  Word/Markdown/HTML đi đường khác: máy chủ đổi sang HTML rồi mới trả về.
  const [html, setHtml] = useState<string | null>(null)
  const [loi, setLoi] = useState('')
  const toHtml = viewAsHtml(contentType, filename)

  useEffect(() => {
    let huy = false
    let createdUrl = ''

    if (toHtml) {
      apiGet<{ html: string }>(`/api/attachments/${linkId}/preview`)
        .then((data) => !huy && setHtml(data.html))
        .catch((error) => !huy && setLoi(extractErrorMessage(error)))
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
      .catch((error) => !huy && setLoi(extractErrorMessage(error)))

    return () => {
      huy = true
      //  Blob sống tới khi đóng tab nếu không thu hồi — tệp 30MB thấy ngay.
      if (createdUrl) URL.revokeObjectURL(createdUrl)
    }
  }, [linkId, toHtml])

  const nhan = [user?.full_name || user?.email, formatDateTime(new Date()), documentCode]
    .filter(Boolean)
    .join(' · ')

  return (
    <>
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
      <div className="relative max-h-[70vh] min-h-64 overflow-auto rounded-md border bg-muted/30">
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
            srcDoc={htmlPage(html)}
            title={filename}
            sandbox=""
            className="h-[70vh] w-full bg-white"
          />
        )}

        {blobUrl &&
          (laAnh(contentType) ? (
            <img src={blobUrl} alt={filename} className="mx-auto block max-w-full" />
          ) : (
            //  `<iframe>` chứ không `<embed>`: trình xem PDF sẵn có của trình
            //  duyệt chạy trong khung riêng, và backend đã gắn
            //  `Content-Security-Policy: sandbox` cho nội dung này.
            <iframe src={blobUrl} title={filename} className="h-[70vh] w-full" />
          ))}

        {(blobUrl || html !== null) && (
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

      <p className="text-xs text-muted-foreground">
        Tệp đang mở trong phiên của <strong>{user?.full_name || user?.email}</strong> — tên bạn được
        in chìm trên mặt tài liệu.
      </p>
    </>
  )
}
