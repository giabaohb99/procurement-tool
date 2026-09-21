/**
 * Ô GIỮ điều kiện áp dụng trên biểu mẫu hồ sơ.
 *
 * ⚠️ **Một ô trên biểu mẫu, HAI cột dưới DB** — cùng khuôn với `custom_rows`
 * (xem `dossier-custom-row.ts`). Người dùng nghĩ về «điều kiện áp dụng» như một
 * việc: *áp cho đơn mua hàng, khi có sản phẩm SP-001*. Dưới DB thì nó là
 * `apply_doc_kinds` + `apply_conditions`, hai cột JSON riêng.
 *
 * ⚠️ Tên ô cố ý KHÁC tên cột. Trùng thì `buildFormDefaults` thấy bản ghi đã có
 * khóa đó và lấy thẳng giá trị đã lưu, nên `defaultValue` dựng ở
 * `dossier-form-fields.ts` sẽ không bao giờ được dùng — đúng bẫy đã ghi ở
 * `CUSTOM_ROWS_FIELD`.
 */
import type { ApplyCondition, DocKind } from './dossier-applicability'

/** Tên ô giữ điều kiện áp dụng trên biểu mẫu. KHÔNG phải tên cột. */
export const APPLY_RULES_FIELD = 'apply_rules'

export interface DossierApplyRules {
  docKinds: DocKind[]
  conditions: ApplyCondition[]
}

export const EMPTY_APPLY_RULES: DossierApplyRules = { docKinds: [], conditions: [] }

/** Gộp hai cột của bản ghi thành một giá trị cho biểu mẫu. */
export function toApplyRules(
  docKinds: DocKind[] | undefined,
  conditions: ApplyCondition[] | undefined,
): DossierApplyRules {
  return {
    docKinds: Array.isArray(docKinds) ? docKinds : [],
    conditions: Array.isArray(conditions) ? conditions : [],
  }
}

/**
 * Tách ngược thành hai cột lúc gửi.
 *
 * ⚠️ **Chưa chọn màn nào thì điều kiện cũng xóa theo.** Điều kiện treo lơ lửng
 * không gắn màn nào vừa không chạy vừa còn nằm đó — lần sau ai mở ra sửa sẽ
 * thấy một bảng điều kiện trông như đang hoạt động. Dọn ngay lúc gửi.
 */
export function fromApplyRules(rules: DossierApplyRules | undefined): {
  apply_doc_kinds: DocKind[]
  apply_conditions: ApplyCondition[]
} {
  const docKinds = rules?.docKinds ?? []
  return {
    apply_doc_kinds: docKinds,
    apply_conditions: docKinds.length === 0 ? [] : (rules?.conditions ?? []),
  }
}
