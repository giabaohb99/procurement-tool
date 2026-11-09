// Thẻ khổ điện thoại của bốn danh mục trong thẻ "Cấu hình" của Tra cứu thị trường (duoc-CR-720).
// Tách khỏi `customs-config-tab.tsx` cho tệp đó khỏi phình; mỗi hàm trả nội dung MỘT thẻ để
// truyền thẳng vào `mobileCard` của `CustomsCatalogCard`.
import { CircleCheck, CircleX, Tag } from 'lucide-react'

import { CrudRecordCard } from '@/shared/crud'
import type { IdentityChip } from '@/shared/ui/record-identity-card'

import { CUSTOMS_REGULATION_CRUD_CONFIG } from '../../config/customs-regulation-crud'
import type { CustomsRegulation } from '../../types/customs'
import {
  formatProductKindLabel,
  type CustomsFormulationCode,
  type CustomsKindKeyword,
  type CustomsSearchSynonym,
} from '../../types/customs-admin'

/** Chip "Đang dùng / Ngừng dùng" — bốn danh mục đều có cột `is_active`. */
function buildActiveChip(isActive: boolean): IdentityChip {
  return isActive
    ? { icon: CircleCheck, text: 'Đang dùng', tone: 'ok' }
    : { icon: CircleX, text: 'Ngừng dùng', tone: 'muted' }
}

//  Thẻ khổ điện thoại của bốn danh mục (bảng 4–11 cột). Khai Ở ĐÂY chứ không ở `CrudConfig`:
//  bốn cấu hình đó không thuộc màn này, và chỉ thẻ "Cấu hình" của Tra cứu thị trường dựng chúng
//  bằng `CustomsCatalogCard`. Khung `CrudRecordCard` dùng chung với mọi danh mục: tên · dòng
//  phụ · chip; bảng khai `onRowClick` (mở hộp sửa) nên trong thẻ không có nút.
export function renderKindKeywordCard(row: CustomsKindKeyword) {
  const kind = formatProductKindLabel(row.kind)
  return (
    <CrudRecordCard
      title={row.keyword}
      subtitle={row.note}
      chips={[...(kind ? [{ icon: Tag, text: kind }] : []), buildActiveChip(row.is_active)]}
    />
  )
}

export function renderSynonymCard(row: CustomsSearchSynonym) {
  const synonyms = row.synonyms
    .split(';')
    .map((item) => item.trim())
    .filter(Boolean)
    .join(' · ')
  return (
    <CrudRecordCard title={row.term} subtitle={synonyms} chips={[buildActiveChip(row.is_active)]} />
  )
}

export function renderFormulationCard(row: CustomsFormulationCode) {
  return (
    <CrudRecordCard
      title={[row.code, row.name_vi || row.name_en].filter(Boolean).join(' — ')}
      subtitle={row.description}
      chips={[buildActiveChip(row.is_active)]}
    />
  )
}

/** Chip của hóa chất lấy đúng `chips` của cấu hình (văn bản · CAS · đang dùng) — một chỗ khai. */
export function renderRegulationCard(row: CustomsRegulation) {
  const subtitle = [row.name_vi ? row.name : '', row.formula].filter(Boolean).join(' · ')
  return (
    <CrudRecordCard
      title={row.name_vi || row.name}
      subtitle={subtitle}
      chips={CUSTOMS_REGULATION_CRUD_CONFIG.chips?.(row) ?? [buildActiveChip(row.is_active)]}
    />
  )
}
