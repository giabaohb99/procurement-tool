/**
 * duoc-CR-784 (phase 03) — ô "Nguồn" của danh sách Báo giá VTBB: "Nhập tay", hoặc "Nhập Excel (lô #N)" bấm được để mở đợt nhập đó
 * ở Quản lý Import. Dừng nổi bọt cú bấm vì bảng mở hộp sửa khi bấm dòng.
 *
 * bao-CR-792 — trang lô nhập gác `import.read`: thiếu quyền đó thì chữ nguồn là chữ thường, không dẫn vào trang cấm.
 */
import { Link } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { appRoutes } from '@/shared/constants/app-routes'

import type { PackagingQuote } from '../types/packaging-cost-types'
import { hasQuoteImportBatch, packagingQuoteSourceText } from '../utils/packaging-quote-source'

export function PackagingQuoteSourceCell({ row }: { row: PackagingQuote }) {
  const { can } = usePermission()
  const text = packagingQuoteSourceText(row.source_type, row.source_id)
  if (!text) return null
  if (!hasQuoteImportBatch(row.source_type, row.source_id) || !can('import', 'read')) return <span>{text}</span>
  return (
    <Link
      to={appRoutes.system.importDetail(row.source_id)}
      title="Mở đợt nhập Excel đã ghi báo giá này"
      onClick={(event) => event.stopPropagation()}
      className="text-primary hover:underline"
    >
      {text}
    </Link>
  )
}
