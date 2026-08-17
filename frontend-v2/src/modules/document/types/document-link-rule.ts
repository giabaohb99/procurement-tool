/**
 * QUY TẮC QUAN HỆ CHA–CON theo LOẠI văn bản (E01).
 *
 * Mỗi dòng là một câu: *"loại X có quan hệ Y tới loại Z, bắt buộc hay không,
 * được mấy cái"*. Khoảng 15–25 dòng cho cả hệ.
 */

export interface DocTypeLinkRule {
  id: number
  source_type_id: number
  source_type_name: string
  relation: number
  relation_label: string
  /** Rỗng = loại nào cũng được. Backend trả tên là "Loại bất kỳ". */
  target_type_id: number | null
  target_type_name: string
  is_required: boolean
  min_count: number
  /** 0 = không giới hạn. */
  max_count: number
  /** 1 không làm gì · 2 đánh dấu con cần rà lại · 3 con hết hiệu lực theo cha. */
  on_parent_obsolete: number
  /** 1 không làm gì · 2 đánh dấu con cần rà lại · 3 hỏi người ban hành rồi ghi nhật ký. */
  on_parent_new_version: number
  inherit_code: boolean
  inherit_secrecy: boolean
  /**
   * Dòng «trích từ» — ba cột `on_parent_*` và `inherit_secrecy` bị khóa cứng ở
   * tầng dịch vụ, khai gì cũng bị ép lại. Giao diện tắt ô và nói rõ vì sao.
   */
  is_locked: boolean
  /** Tắt thì không khai thêm và không chặn gửi duyệt nữa; quan hệ cũ vẫn còn. */
  is_active: boolean
}

export interface DocTypeLinkRuleInput {
  source_type_id: number
  relation: number
  target_type_id: number | null
  is_required: boolean
  min_count: number
  max_count: number
  on_parent_obsolete: number
  on_parent_new_version: number
  inherit_code: boolean
  inherit_secrecy: boolean
  is_active: boolean
}

export interface LinkRuleOption {
  value: number
  label: string
}

/** Nhãn tiếng Việt do backend cấp — không chép cứng ở giao diện. */
export interface LinkRuleOptions {
  relations: LinkRuleOption[]
  on_parent_obsolete: LinkRuleOption[]
  on_parent_new_version: LinkRuleOption[]
}
