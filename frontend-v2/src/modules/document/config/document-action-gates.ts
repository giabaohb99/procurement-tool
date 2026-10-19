import type { PermissionAction, PermissionEntity } from '@/core/authorization/permission-types'
import type { DocumentPermissions } from '../types/document-record'

type CanFn = (entity: PermissionEntity, action: PermissionAction) => boolean

export interface DocumentActionGates {
  /** Bản lưu trữ hợp đồng lao động (duoc-CR-640). */
  isArchive: boolean
  canApprove: boolean
  canCreate: boolean
  canWrite: boolean
  canDelete: boolean
  /** Chia sẻ, phạm vi áp dụng, quan hệ, phê duyệt, chữ ký — ẩn hẳn với bản lưu trữ (backend chặn 409). */
  showSharingAndWorkflow: boolean
}

/**
 * Cờ hiện nút của trang chi tiết văn bản — hàm thuần để test.
 *
 * Quyền sửa / xóa lấy từ backend (`permissions`), không tự ghép. Bản lưu trữ HĐLĐ: người có `labor_contract.write`
 * sửa được thông tin / nội dung / tệp (`write = true`), còn các thao tác đẩy văn bản tới người khác (duyệt, ký, sao
 * chép, chia sẻ, quan hệ…) ẩn dù người xem có quyền vai trò Văn bản.
 */
export function resolveDocumentActionGates(
  permissions: DocumentPermissions | undefined,
  can: CanFn,
  readonlyFromLink: boolean,
): DocumentActionGates {
  const isArchive = permissions?.is_archive ?? false
  return {
    isArchive,
    canApprove: !readonlyFromLink && !isArchive && can('document', 'approve'),
    canCreate: !readonlyFromLink && !isArchive && can('document', 'create'),
    canWrite: !readonlyFromLink && (permissions?.write ?? false),
    canDelete: !readonlyFromLink && (permissions?.delete ?? false),
    showSharingAndWorkflow: !isArchive,
  }
}
