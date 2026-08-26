import { usePermission } from '@/core/authorization/use-permission'
import { DocumentAttachmentsCard } from '@/modules/procurement/components/document-attachments-card'

/**
 * Tab "Tệp đính kèm" của Nhà cung cấp (ĐKKD, hồ sơ năng lực, chứng nhận ISO, bảng giá...).
 */
export function SupplierFilesTab({ supplierId }: { supplierId: number }) {
  const { can } = usePermission()

  return (
    <DocumentAttachmentsCard
      entity="supplier"
      entityId={supplierId}
      canManage={can('supplier', 'write') || can('supplier', 'create')}
    />
  )
}
