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
 * ĐỔ KHUÔN của loại vào bảng khi người dùng chọn một loại khác.
 *
 * Luật (khách chốt 17/09/2026): loại hồ sơ là **khuôn**, không phải luật. Chọn
 * loại thì các ô của nó hiện thành dòng trong bảng; người lập sửa/xóa tự do, và
 * xóa dòng nào thì TỜ NÀY không có ô đó — loại vẫn nguyên, hồ sơ khác cùng loại
 * vẫn có.
 *
 * Ba thứ phải giữ khi đổ, và mỗi thứ chữa một cách mất dữ liệu:
 *
 * 1. **Hàng người dùng TỰ THÊM ở lại.** Họ khai «Số quyết định» rồi mới chọn
 *    loại — cuốn phăng đi là mất công gõ.
 * 2. **Giá trị ĐÃ ĐIỀN ở lại** nếu khuôn mới cũng có khóa đó. Hai loại cùng
 *    dùng `so_giay_phep` thì đổi qua lại không được xóa thứ vừa gõ.
 * 3. **Hàng của khuôn CŨ bị gỡ** — chúng thuộc về loại vừa bỏ chọn. Giữ lại thì
 *    đổi loại vài lần là bảng phình ra toàn ô của những loại không còn chọn.
 *
 * `oldDefs` rỗng (lần đầu chọn loại) thì không có gì để gỡ — mọi hàng hiện có
 * đều là của người dùng.
 */
export function reseedFromType(
  rows: DossierCustomRow[],
  oldDefs: DossierFieldDef[],
  newDefs: DossierFieldDef[],
): DossierCustomRow[] {
  const oldKeys = new Set(oldDefs.map((d) => d.key))
  const byKey = new Map(rows.map((r) => [r.key, r]))

  //  Khuôn mới lên trước, giữ đúng thứ tự đã khai ở màn Loại hồ sơ.
  const seeded = newDefs.map((def) => ({
    ...def,
    value: byKey.get(def.key)?.value ?? (def.type === 'switch' ? false : ''),
  }))

  const seededKeys = new Set(newDefs.map((d) => d.key))
  const kept = rows.filter((r) => !seededKeys.has(r.key) && !oldKeys.has(r.key))

  return [...seeded, ...kept]
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
