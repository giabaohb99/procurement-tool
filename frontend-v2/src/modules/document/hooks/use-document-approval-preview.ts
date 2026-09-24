import { keepPreviousData, useQuery } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'
import { useDebouncedValue } from '@/shared/hooks/use-debounced-value'
import { documentApi } from '../api/document-api'
import type { ApprovalPreviewInput, ApprovalPreviewResult } from '../types/approval-preview'

/** Ngưng đổi bao lâu thì mới gọi lại API xem trước (phase 01, duoc-CR-473). */
const DEBOUNCE_MS = 400

/**
 * XEM TRƯỚC «Người duyệt dự kiến» ở màn tạo văn bản / chi tiết nháp.
 *
 * Chỉ theo dõi ĐÚNG bảy trường ảnh hưởng tới luồng duyệt — Loại · Pháp nhân ·
 * Phòng ban · Độ mật · Độ khẩn · Người ký · bản gốc (đổi sang bản clone) —
 * KHÔNG theo `title` hay các ô khác, kẻo mỗi lần gõ tiêu đề lại bắn một request.
 * `useDebouncedValue` hoãn `input` 400ms nên gõ liên tục cũng chỉ gọi một lần
 * sau khi ngừng; `keepPreviousData` giữ thẻ cũ trên màn hình trong lúc chờ,
 * khỏi chớp về rỗng.
 *
 * Không gọi API khi chưa có `doc_type_id`/`company_id` — hai ô luôn phải chọn
 * trước khi có gì để xem trước (khớp `Field(gt=0)` phía backend).
 */
export function useDocumentApprovalPreview(input: ApprovalPreviewInput) {
  const debounced = useDebouncedValue(input, DEBOUNCE_MS)

  const watchedKey = {
    doc_type_id: debounced.doc_type_id,
    company_id: debounced.company_id,
    department_id: debounced.department_id ?? 0,
    secrecy_level: debounced.secrecy_level ?? 0,
    urgency: debounced.urgency ?? 0,
    signer_employee_id: debounced.signer_employee_id ?? 0,
    source_document_id: debounced.source_document_id ?? 0,
  }
  const enabled = watchedKey.doc_type_id > 0 && watchedKey.company_id > 0

  return useQuery<ApprovalPreviewResult>({
    queryKey: queryKeys.document.approvalPreview(watchedKey),
    queryFn: () => documentApi.previewApproval(debounced),
    enabled,
    placeholderData: keepPreviousData,
  })
}
