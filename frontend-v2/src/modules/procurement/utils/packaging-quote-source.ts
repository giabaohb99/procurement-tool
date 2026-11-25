/**
 * duoc-CR-784 (phase 03) — chữ cột "Nguồn" của Báo giá VTBB: "Nhập tay" / "Nhập Excel (lô #N)".
 *
 * Nhãn lấy từ bộ mã SINH TỰ ĐỘNG `QUOTE_SOURCE_TYPE` (`shared/constants/statuses.ts`, nguồn
 * `backend/app/core/packaging_price_codes.py`); chữ "(lô #N)" ghép từ `source_id` = id đợt nhập. Bản v1 (`frontend/`) viết đúng
 * cùng chữ ở `utils/packaging-price.ts` — đổi một bên phải đổi bên kia.
 */
import { labelOf, QUOTE_SOURCE_TYPE, QUOTE_SOURCE_TYPE_CODE } from '@/shared/constants/statuses'

/** Mã máy chủ chưa được giao diện biết (máy chủ mới hơn) rơi về "Mã n" chứ không thành ô trống. */
export function packagingQuoteSourceText(
  sourceType: number | null | undefined,
  sourceId: number | null | undefined,
): string {
  if (sourceType == null) return ''
  const label = labelOf(QUOTE_SOURCE_TYPE, String(sourceType)) || `Mã ${sourceType}`
  if (sourceType === QUOTE_SOURCE_TYPE_CODE.EXCEL_IMPORT && sourceId != null && sourceId > 0) {
    return `${label} (lô #${sourceId})`
  }
  return label
}

/** Chỉ báo giá nhập Excel có đợt nhập thật để mở (nhập tay `source_id` = 0). */
export function hasQuoteImportBatch(
  sourceType: number | null | undefined,
  sourceId: number | null | undefined,
): sourceId is number {
  return sourceType === QUOTE_SOURCE_TYPE_CODE.EXCEL_IMPORT && sourceId != null && sourceId > 0
}
