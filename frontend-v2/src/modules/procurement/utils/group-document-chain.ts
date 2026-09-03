import type { ChainAttachment } from '../types/document-chain'
import { CHAIN_SOURCE_LABELS, CHAIN_SOURCE_ORDER } from '../types/document-chain'

/** Một mục chứng từ (báo giá, hóa đơn GTGT…) bên trong một nấc. */
export interface ChainTypeGroup {
  label: string
  files: ChainAttachment[]
}

/** Một nấc chứng từ của chuỗi — PO · PYC · PKS · YCKS. */
export interface ChainSourceGroup {
  source: string
  label: string
  /** Mã chứng từ của nấc, lấy từ tệp đầu tiên; rỗng nếu backend không trả. */
  code: string
  total: number
  types: ChainTypeGroup[]
}

/** Nhãn cho tệp không khai loại — backend cho phép `doc_type` rỗng. */
const UNTYPED_LABEL = 'Khác'

/**
 * Gom chuỗi chứng từ thành: nấc → mục → tệp.
 *
 * Hai điều đáng chú ý, cả hai đều là bẫy có thật của endpoint `/chain`:
 *
 * ① **Phải khử trùng theo `link_id`.** `_resolve_chain` khai entity `survey_line`
 *    HAI LẦN — một lần với id dòng NCC, một lần với id dòng sản phẩm — nên một
 *    tệp có id nằm ở cả hai tập sẽ về hai lần. Bản v1 (`frontend/src/pages/
 *    Documents.tsx`) không khử nên đếm dôi và hiện tệp trùng.
 *
 * ② **Thứ tự nấc là cố định**, không theo thứ tự backend trả. Nấc lạ (thêm vào
 *    chuỗi sau này) vẫn phải hiện — xếp xuống cuối, còn hơn để tệp biến mất mà
 *    vẫn được đếm trong tổng số ở đầu trang.
 */
export function groupDocumentChain(files: ChainAttachment[]): ChainSourceGroup[] {
  const seen = new Set<number>()
  const bySource = new Map<string, ChainAttachment[]>()

  files.forEach((file) => {
    if (seen.has(file.link_id)) return
    seen.add(file.link_id)
    const bucket = bySource.get(file.source)
    if (bucket) bucket.push(file)
    else bySource.set(file.source, [file])
  })

  const ordered = new Set<string>(CHAIN_SOURCE_ORDER)
  const known: string[] = CHAIN_SOURCE_ORDER.filter((source) => bySource.has(source))
  const unknown = [...bySource.keys()].filter((source) => !ordered.has(source))

  return [...known, ...unknown].map((source) => {
    const bucket = bySource.get(source) ?? []
    return {
      source,
      label: CHAIN_SOURCE_LABELS[source] || source,
      code: bucket.find((file) => file.source_code)?.source_code ?? '',
      total: bucket.length,
      types: groupByType(bucket),
    }
  })
}

/** Gom trong một nấc theo nhãn loại chứng từ, giữ thứ tự gặp đầu tiên. */
function groupByType(files: ChainAttachment[]): ChainTypeGroup[] {
  const buckets = new Map<string, ChainAttachment[]>()
  files.forEach((file) => {
    // Backend đã tra nhãn sẵn, nhưng loại đã bị xóa khỏi danh mục thì nó trả về
    // chính mã thô hoặc "—"; cả hai đều không phải nhãn đọc được nên gộp về "Khác".
    const label = file.doc_type_label && file.doc_type_label !== '—' ? file.doc_type_label : UNTYPED_LABEL
    const bucket = buckets.get(label)
    if (bucket) bucket.push(file)
    else buckets.set(label, [file])
  })
  return [...buckets.entries()].map(([label, bucket]) => ({ label, files: bucket }))
}

/** Tệp xem trước được ngay trên trang: ảnh và PDF, và phải có đường đọc thật. */
export function isPreviewableChainFile(file: ChainAttachment): boolean {
  if (!file.url) return false
  return isChainImage(file) || isChainPdf(file)
}

export function isChainImage(file: ChainAttachment): boolean {
  return Boolean(file.content_type?.startsWith('image/'))
}

export function isChainPdf(file: ChainAttachment): boolean {
  return file.content_type === 'application/pdf' || /\.pdf$/i.test(file.filename)
}
