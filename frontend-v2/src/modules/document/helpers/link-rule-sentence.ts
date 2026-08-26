import type { DocTypeLinkRuleInput } from '../types/document-link-rule'

/**
 * Đọc một dòng quy tắc quan hệ thành CÂU TIẾNG VIỆT.
 *
 * Bảng quy tắc lưu bốn cột rời — `relation`, `target_type_id`, `is_required`,
 * `min_count`/`max_count` — và trước đây giao diện bày đúng bốn cột đó ra thành
 * một hàng chip: *"Căn cứ theo → Thư công · Bắt buộc · Từ 1"*. Người khai phải
 * tự ghép bốn mảnh lại mới hiểu, và ghép sai thì không có gì báo.
 *
 * Câu đầy đủ nói thẳng ra điều luật: *"Mỗi văn bản «Trích lục» phải căn cứ theo
 * ít nhất 1 văn bản «Thư công»."* — đọc một lần là biết mình vừa khai cái gì.
 */
interface LinkRuleSentenceArgs {
  rule: Pick<DocTypeLinkRuleInput, 'is_required' | 'min_count' | 'max_count'>
  /** Nhãn quan hệ do backend cấp: "Căn cứ theo", "Hướng dẫn"… */
  relationLabel: string
  /** Bỏ trống = quy tắc không kén loại đích ("loại bất kỳ"). */
  targetTypeName?: string
  /** Bỏ trống (đang tạo loại mới, chưa có tên) thì câu mở bằng "Văn bản loại này". */
  sourceTypeName?: string
}

export function linkRuleSentence({
  rule,
  relationLabel,
  targetTypeName,
  sourceTypeName,
}: LinkRuleSentenceArgs): string {
  const subject = sourceTypeName ? `Mỗi văn bản «${sourceTypeName}»` : 'Văn bản loại này'
  //  Nhãn quan hệ viết hoa chữ đầu vì đứng riêng ở cột bảng; vào giữa câu thì
  //  phải thường xuống, không thì đọc thành hai câu ghép vụng.
  const verb = relationLabel.toLowerCase()

  //  Không kén loại thì KHÔNG bỏ vào ngoặc kép: «Loại bất kỳ» đọc ra thành tên
  //  một loại văn bản có thật, mà đó lại là chỗ duy nhất không có loại nào.
  const dich = targetTypeName ? `«${targetTypeName}»` : 'thuộc loại bất kỳ'
  return `${subject} ${quantified(rule)} ${verb} ${documentFlow(rule)} ${dich}.`
}

/** "phải" hay "có thể" — phần quyết định người soạn có bị chặn gửi duyệt không. */
function quantified(rule: LinkRuleSentenceArgs['rule']): string {
  return rule.is_required ? 'phải' : 'có thể'
}

/** Phần số lượng: "đúng 1 văn bản", "ít nhất 2 văn bản", "một hoặc nhiều văn bản"… */
function documentFlow({ is_required, min_count, max_count }: LinkRuleSentenceArgs['rule']): string {
  //  Bắt buộc mà khai tối thiểu 0 thì backend vẫn tính là 1 (`max(min_count, 1)`
  //  trong `missing_required`). Câu phải nói đúng cái backend làm, không thì
  //  người khai đọc "0" rồi ngạc nhiên vì bị chặn gửi duyệt.
  const minimum = is_required ? Math.max(min_count, 1) : min_count

  if (max_count > 0 && minimum === max_count) return `đúng ${max_count} văn bản`
  if (max_count > 0 && minimum > 0) return `${minimum}–${max_count} văn bản`
  if (max_count > 0) return `tối đa ${max_count} văn bản`
  if (minimum > 0) return `ít nhất ${minimum} văn bản`
  return 'một hoặc nhiều văn bản'
}
