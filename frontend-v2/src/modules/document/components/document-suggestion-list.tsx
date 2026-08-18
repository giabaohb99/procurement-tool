import { Info } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { cn } from '@/shared/utils/cn'
import { formatDate } from '@/shared/utils/format-date'
import { shouldWarnDuplicate } from '../helpers/should-warn-duplicate'
import { useDocumentSuggestions } from '../hooks/use-documents'
import { useActiveDocumentTypes } from '../hooks/use-document-types'

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
 * Chỉ nhắc ở **văn bản quản trị** (quy chế, quy định, quy trình…). Một phòng ra
 * hàng chục công văn, thông báo, biên bản mỗi tháng — nhắc ở đó thì lần tạo nào
 * cũng thấy băng vàng và người dùng học được đúng một điều: bỏ qua nó. Luật
 * nhận diện nằm ở `shouldWarnDuplicate`.
 *
 * Không có gì trùng thì **không hiện gì** — một khối rỗng nằm giữa form chỉ tổ
 * làm người dùng phải đọc lướt qua nó mỗi lần.
 *
 * Nhưng "không hiện gì" chỉ đúng khi đã biết là không có gì. Trong lúc đang hỏi
 * lại (đổi loại, đổi phòng), khối vẫn **giữ nguyên kết quả cũ và làm mờ** thay
 * vì biến mất: nó chiếm cả hai cột giữa lưới, mất đi một nhịp là hai ô nhập bên
 * dưới nhảy lên rồi tụt xuống. Làm mờ vì nội dung đang là của lựa chọn trước —
 * bày y như thật thì người ta đọc phải con số sai.
 */
export function DocumentSuggestionList({
  docTypeId,
  departmentId,
  companyId,
  excludeId,
}: DocumentSuggestionListProps) {
  const docTypes = useActiveDocumentTypes()
  const canNhac = shouldWarnDuplicate(docTypes.find((type) => type.id === docTypeId))

  const { data, isFetching } = useDocumentSuggestions({
    doc_type_id: canNhac ? docTypeId : 0,
    department_id: departmentId,
    company_id: companyId,
    exclude_id: excludeId,
  })

  if (!canNhac || !data?.length) return null

  return (
    <div
      aria-busy={isFetching}
      className={cn(
        'rounded-md border border-amber-200 bg-amber-50 p-3 transition-opacity sm:col-span-2',
        isFetching && 'opacity-50',
      )}
    >
      <p className="flex items-center gap-2 text-sm font-medium text-amber-900">
        <Info className="size-4 shrink-0" />
        Đã có {data.length} văn bản cùng loại ở phòng này đang còn hiệu lực — bản mới
        có thay thế bản dưới đây không?
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
