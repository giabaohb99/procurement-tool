import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { purchaseRequestSupportApi } from '@/modules/procurement/api/purchase-request-support-api'
import { documentAccessApi } from '../api/document-api'
import type { PendingAccess } from '../components/document-access-fields'

/**
 * Gửi QUYỀN + TỆP đang xếp hàng ngay sau khi văn bản có id — dùng chung cho
 * trang tạo 3 bước và hộp «Tạo nhanh từ tệp» ở trang Thư mục.
 *
 * Quyền gửi tuần tự để dòng nào hỏng thì báo đúng dòng đó. Tệp gửi MỘT LƯỢT
 * (API nhận nhiều tệp trong một lần gọi) và treo vào PHIÊN BẢN, nên thiếu
 * `versionId` là không có chỗ treo. Hỏng phần nào cũng chỉ báo, không ném:
 * văn bản đã tồn tại rồi, mỗi phần đều khai lại được ở trang chi tiết.
 */
export async function sendPendingAccessAndFiles(
  documentId: number,
  versionId: number | null,
  access: PendingAccess[],
  files: File[],
): Promise<void> {
  const permissionFailed: string[] = []
  for (const row of access) {
    try {
      await documentAccessApi.grant(documentId, row.values)
    } catch {
      permissionFailed.push(row.subjectLabel || 'một đối tượng')
    }
  }
  if (permissionFailed.length > 0) {
    toast.error(
      `Chưa chia được quyền cho ${permissionFailed.join(', ')} — mở tab Thông tin để khai lại.`,
    )
  }

  if (files.length > 0 && versionId) {
    try {
      await purchaseRequestSupportApi.uploadAttachments('document_version', versionId, files)
      toast.success(`Đã đính kèm ${files.length} tệp`)
    } catch (error) {
      //  Nói nguyên câu của backend: gần như luôn là "tệp quá lớn" hoặc "đuôi
      //  tệp không cho phép" — người dùng cần biết tệp nào phải đổi.
      toast.error(`Chưa tải được tệp đính kèm — ${extractErrorMessage(error)}`)
    }
  }
}
