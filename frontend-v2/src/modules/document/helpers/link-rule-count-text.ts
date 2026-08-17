import type { DocTypeLinkRule } from '../types/document-link-rule'

/**
 * Cột "Số lượng" đọc từ CẶP `min_count`/`max_count`, còn tài liệu mô tả bằng
 * lời: *"đúng 1"*, *"từ 1"*, *"0 trở lên"*. Dịch sai chỗ này thì người khai quy
 * tắc tưởng mình đặt một đằng, hệ thống chặn một nẻo.
 */
export function countText(rule: DocTypeLinkRule): string {
  if (rule.max_count > 0 && rule.min_count === rule.max_count) return `Đúng ${rule.max_count}`
  if (rule.min_count > 0 && rule.max_count > 0) {
    return `Từ ${rule.min_count} tới ${rule.max_count}`
  }
  if (rule.min_count > 0) return `Từ ${rule.min_count}`
  if (rule.max_count > 0) return `Tối đa ${rule.max_count}`
  return '0 trở lên'
}
