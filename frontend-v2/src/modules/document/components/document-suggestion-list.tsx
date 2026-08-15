import { Info } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { formatDate } from '@/shared/utils/format-date'
import { useDocumentSuggestions } from '../hooks/use-documents'

interface DocumentSuggestionListProps {
  docTypeId: number
  departmentId: number | null
  companyId: number
  /** Bỏ chính văn bản đang sửa ra khỏi danh sách. */
  excludeId?: number
}

/**
 * "Đã có văn bản cùng loại cùng phòng đang hiệu lực" (B05).
 *
 * Bản 1 đã BỎ bước xin phép — ai có quyền tạo thì tạo thẳng (quyết định 7 của
 * plan). Mất đi chốt chặn ngăn mỗi phòng đẻ ra một quy trình rồi không ai biết
 * cái nào đang chạy; khối này là thứ rẻ nhất còn lại thay cho nó: đặt ngay dưới
 * ô tên văn bản, người soạn nhìn thấy trước khi ngồi gõ chứ không phải sau khi
 * đã gõ xong.
 *
 * Không có gì trùng thì **không hiện gì** — một khối rỗng nằm giữa form chỉ tổ
 * làm người dùng phải đọc lướt qua nó mỗi lần.
 */
export function DocumentSuggestionList({
  docTypeId,
  departmentId,
  companyId,
  excludeId,
}: DocumentSuggestionListProps) {
  const { data } = useDocumentSuggestions({
    doc_type_id: docTypeId,
    department_id: departmentId,
    company_id: companyId,
    exclude_id: excludeId,
  })

  if (!data?.length) return null

  return (
    <div className="rounded-md border border-amber-200 bg-amber-50 p-3 sm:col-span-2">
      <p className="flex items-center gap-2 text-sm font-medium text-amber-900">
        <Info className="size-4 shrink-0" />
        Đã có {data.length} văn bản cùng loại ở phòng này đang còn hiệu lực
      </p>
      <ul className="mt-2 space-y-1">
        {data.map((item) => (
          <li key={item.id} className="text-sm">
            <Link
              to={appRoutes.document.documentDetail(item.id)}
              // Mở tab mới: người đang soạn dở, bấm vào mà mất form đang nhập
              // thì lần sau không ai dám bấm nữa.
              target="_blank"
              rel="noreferrer"
              className="text-amber-900 underline underline-offset-2 hover:text-amber-950"
            >
              {item.display_code ? `${item.display_code} — ` : ''}
              {item.title}
            </Link>
            {item.effective_date && (
              <span className="text-amber-800"> · từ {formatDate(item.effective_date)}</span>
            )}
          </li>
        ))}
      </ul>
    </div>
  )
}
