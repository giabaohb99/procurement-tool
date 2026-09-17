import type { DossierFieldValue } from './dossier'
import { emptyDossierField, type DossierFieldDef } from './dossier-field'

/**
 * MỘT DÒNG của trình khai trường riêng: khai báo + giá trị, đi chung.
 *
 * ⚠️ Đây là hình dạng của BIỂU MẪU, không phải của kho dữ liệu. Dưới DB chúng
 * nằm ở hai chỗ — khai báo ở `tab_dossier.custom_fields`, giá trị ở
 * `tab_dossier.extra_fields` (chung kho với ô của loại). Gộp lại ở tầng biểu
 * mẫu vì người dùng nhìn thấy MỘT hàng: *«Số QĐ | Chữ | bắt buộc | 1234/QĐ»*;
 * tách đôi ngay trên màn hình là bắt họ gõ tên ở một chỗ rồi đi tìm ô giá trị
 * ở chỗ khác.
 *
 * Việc tách/ghép làm ở đúng hai hàm dưới đây, không rải ra nơi khác.
 */
export interface DossierCustomRow extends DossierFieldDef {
  value: DossierFieldValue
}

/** Dòng trắng cho nút «Thêm trường». */
export function emptyCustomRow(): DossierCustomRow {
  return { ...emptyDossierField(), value: '' }
}

/**
 * BẢN GHI → DÒNG BIỂU MẪU: ghép khai báo với giá trị tương ứng.
 *
 * Dùng lúc dựng giá trị khởi tạo cho form (`defaultValue` của ô tự vẽ). Giá trị
 * thiếu thì về rỗng — hồ sơ cũ có thể mang khai báo mà chưa ai điền.
 */
export function toCustomRows(
  defs: DossierFieldDef[] | undefined,
  extra: Record<string, DossierFieldValue> | undefined,
): DossierCustomRow[] {
  return (defs ?? []).map((def) => ({
    ...def,
    value: extra?.[def.key] ?? (def.type === 'switch' ? false : ''),
  }))
}

/**
 * DÒNG BIỂU MẪU → BẢN GHI: tách lại thành (khai báo, giá trị).
 *
 * ⚠️ **Bỏ dòng chưa đặt tên.** Người dùng bấm «Thêm trường» rồi đổi ý và không
 * gõ gì — gửi lên thì backend trả 422 «Mã trường không được để trống» cho một
 * hàng trống mà họ coi như không tồn tại. Lặng lẽ bỏ đúng ở ca này là đúng: nó
 * không mang dữ liệu nào để mà mất.
 */
export function fromCustomRows(rows: DossierCustomRow[] | undefined): {
  defs: DossierFieldDef[]
  values: Record<string, DossierFieldValue>
} {
  const defs: DossierFieldDef[] = []
  const values: Record<string, DossierFieldValue> = {}

  for (const row of rows ?? []) {
    if (!row.key || !row.label.trim()) continue
    const { value, ...def } = row
    defs.push(def)
    values[row.key] = value
  }
  return { defs, values }
}
