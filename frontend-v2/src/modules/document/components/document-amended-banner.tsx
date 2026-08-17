import { AlertTriangle, ArrowRight } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentAmendedBy } from '../hooks/use-document-links'

interface DocumentAmendedBannerProps {
  documentId: number
}

/**
 * BĂNG "ĐÃ BỊ SỬA ĐỔI" (J10) — **bắt buộc, không phải tùy chọn**.
 *
 * Quan hệ *sửa đổi* KHÔNG đổi trạng thái văn bản cũ: Quyết định 15 bị sửa Điều 5
 * vẫn hiện "Có hiệu lực". Người mở nó không có lý do gì để nghi ngờ, nên họ đọc
 * Điều 5 cũ rồi làm sai — và **không ai phát hiện ra**, vì trên màn hình mọi thứ
 * trông vẫn đúng.
 *
 * Vì thế băng này:
 *  - đặt trên cùng, trước cả nội dung;
 *  - không có nút đóng;
 *  - hiện ở MỌI tab, không giấu trong tab Quan hệ.
 */
export function DocumentAmendedBanner({ documentId }: DocumentAmendedBannerProps) {
  const { data: amendments = [] } = useDocumentAmendedBy(documentId)

  if (amendments.length === 0) return null

  return (
    <div className="mb-3 flex gap-3 rounded-md border border-amber-300 bg-amber-50 px-4 py-3">
      <AlertTriangle className="mt-0.5 size-4 shrink-0 text-amber-700" />
      <div className="min-w-0 flex-1 text-sm text-amber-900">
        <p className="font-medium">
          Văn bản này đã bị {amendments.length > 1 ? 'nhiều văn bản khác ' : ''}tác động —
          đọc bản mới trước khi làm theo.
        </p>
        <ul className="mt-1 space-y-1">
          {amendments.map((item) => (
            <li key={item.document_id} className="flex flex-wrap items-center gap-2">
              <span className="text-amber-800">{item.relation_label} bởi</span>
              <Link
                to={appRoutes.document.documentDetail(item.document_id)}
                className="inline-flex items-center gap-1 font-medium hover:underline"
              >
                {item.display_code ? `${item.display_code} · ` : ''}
                {item.title}
                <ArrowRight className="size-3.5" />
              </Link>
              {item.effective_date && (
                <span className="text-xs text-amber-800">
                  hiệu lực từ {formatDate(item.effective_date)}
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
