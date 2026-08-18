import { RELATION } from '../types/document-link'
import type { DocTypeLinkRule, DocTypeLinkRuleInput } from '../types/document-link-rule'

/**
 * Một dòng quy tắc quan hệ TRỐNG.
 *
 * `on_parent_*` mặc định theo tài liệu: cha lên phiên bản mới thì **hỏi người
 * ban hành**, cha bị bãi bỏ thì **đánh dấu con cần rà lại** — hai mặc định an
 * toàn, không tự đụng vào văn bản con.
 */
export const EMPTY_LINK_RULE: DocTypeLinkRuleInput = {
  source_type_id: 0,
  relation: RELATION.guide,
  target_type_id: null,
  is_required: false,
  min_count: 0,
  max_count: 0,
  //  Chưa xếp thứ tự. Thẻ quan hệ gán số thật khi thêm dòng (xuống cuối danh
  //  sách) — form không hỏi ô này, thứ tự khai bằng nút lên/xuống dễ hơn nhiều.
  sort_order: 0,
  on_parent_obsolete: 2,
  on_parent_new_version: 3,
  inherit_code: false,
  inherit_secrecy: false,
  is_active: true,
}

/**
 * Bản ghi đọc về → bộ giá trị khai được.
 *
 * Bản ghi mang thêm ba trường CHỈ ĐỌC do backend tính (`*_name`, `is_locked`) —
 * gửi ngược lên là backend từ chối. Bóc ở đúng một chỗ để chỗ khác khỏi tự nhớ.
 */
export function linkRuleToInput(rule: DocTypeLinkRule): DocTypeLinkRuleInput {
  return {
    source_type_id: rule.source_type_id,
    relation: rule.relation,
    target_type_id: rule.target_type_id,
    is_required: rule.is_required,
    min_count: rule.min_count,
    max_count: rule.max_count,
    sort_order: rule.sort_order,
    on_parent_obsolete: rule.on_parent_obsolete,
    on_parent_new_version: rule.on_parent_new_version,
    inherit_code: rule.inherit_code,
    inherit_secrecy: rule.inherit_secrecy,
    is_active: rule.is_active,
  }
}
