import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'

/**
 * Tab "Tệp đính kèm" của hợp đồng.
 *
 * Dùng thẳng thẻ chứng từ dùng chung của phân hệ Mua hàng — backend đính kèm vốn
 * không phân biệt loại chứng từ cha (`POST /api/attachments` nhận `entity` +
 * `entity_id`), `FILE_POLICY` chỉ khai thêm dòng `contract` với hạn mức 30 MB.
 *
 * ⚠️ Bản tự dựng trước đó của tab này tự bịa danh sách loại chứng từ bằng tiếng
 * Việt ("Bản quét hợp đồng", "Phụ lục hợp đồng"…) trong khi backend chỉ nhận bộ
 * giá trị cố định ở `app/core/document_types.py`, nên MỌI lượt tải lên đều ăn
 * 400. Thẻ dùng chung lấy tùy chọn từ `useDocumentTypes()` nên không lệch được,
 * đồng thời tải tệp qua `/api/attachments/{id}/download` (có kiểm quyền) thay vì
 * mở thẳng đường dẫn kho lưu trữ.
 */
export function ContractFilesTab({ contractId }: { contractId: number }) {
  const { can } = usePermission()

  return (
    <DocumentAttachmentsCard
      entity="contract"
      entityId={contractId}
      canManage={can('contract', 'write') || can('contract', 'create')}
      maxSizeMb={30}
    />
  )
}
