import type { AttachmentFile, DocumentTypeOption } from '../api/purchase-request-support-api'

/** Tệp không khai loại thì xếp vào "Khác" — backend cho phép `doc_type` rỗng. */
export const OTHER_DOC_TYPE = 'other'

export interface DocumentGroup {
  type: string
  label: string
  files: AttachmentFile[]
}

/** Danh mục loại chứng từ, luôn có sẵn mục "Khác" kể cả khi backend chưa trả về. */
export function withOtherType(types: DocumentTypeOption[]): DocumentTypeOption[] {
  if (types.some((type) => type.value === OTHER_DOC_TYPE)) return types
  return [...types, { value: OTHER_DOC_TYPE, label: 'Khác' }]
}

/**
 * Gom tệp đính kèm theo mục chứng từ.
 *
 * Xếp theo THỨ TỰ DANH MỤC của backend chứ không theo thứ tự tệp được tải lên —
 * để vị trí các mục đứng yên giữa hai lần mở, người dùng nhớ được chỗ.
 */
export function groupAttachmentsByType(
  files: AttachmentFile[],
  options: DocumentTypeOption[],
): DocumentGroup[] {
  const buckets = new Map<string, AttachmentFile[]>()
  files.forEach((file) => {
    const type = file.doc_type || OTHER_DOC_TYPE
    const bucket = buckets.get(type)
    if (bucket) bucket.push(file)
    else buckets.set(type, [file])
  })

  const known = options
    .filter((option) => buckets.has(option.value))
    .map<DocumentGroup>((option) => ({
      type: option.value,
      label: option.label,
      files: buckets.get(option.value) ?? [],
    }))
  // Loại lạ (danh mục đổi sau khi tệp đã tải lên) vẫn phải hiện, không thì tệp
  // biến mất khỏi màn hình mà vẫn được đếm trong tổng số ở tiêu đề thẻ.
  const unknown = [...buckets.entries()]
    .filter(([type]) => !options.some((option) => option.value === type))
    .map<DocumentGroup>(([type, bucket]) => ({ type, label: type, files: bucket }))

  return [...known, ...unknown]
}
