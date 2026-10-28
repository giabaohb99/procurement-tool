import type {
  HeadcountPlanCostItemPayload,
  HeadcountPlanCreatePayload,
  HeadcountPlanDraftPayload,
  HeadcountPlanLinePayload,
  HeadcountPlanPayload,
} from '../types/headcount-plan'
import type { HrCostItem } from '../types/hr-cost'
import type { HeadcountPlanDraft } from './headcount-plan-draft'
import { finalizeCostItems } from './hr-cost-item-custom'
import { dropExcludedCostItems } from './hr-cost-item-rules'

/**
 * GÓI PAYLOAD của kế hoạch nhân sự. Backend khai `extra="forbid"` cho mọi schema nên chỉ gửi ĐÚNG các
 * khóa hợp đồng: khoản không mang `id`, dòng không mang `position_name`, bản xem trước không mang
 * `document_ids`. Thừa một khóa là 422 cho cả bản nháp.
 *
 * Người không được xem tiền: gửi `null` ở mọi ô tiền — backend hiểu là «giữ nguyên số đang lưu»; gửi
 * một con số khác 0 thì 403. Bản nháp của họ vốn đã `null` (backend che), nhưng ép lại ở đây để không
 * đường sửa nào lọt số tiền lên.
 */

const toInt = (v: unknown) => Math.max(0, Math.trunc(Number(v) || 0))

/**
 * Khoản chi phí → thân gửi lên, ĐÚNG 14 khóa (không `id`, không `custom_parts`, không `excluded`). Gọi
 * trên bộ đã qua `finalizeCostItems` để khoản gốc / thứ tự tự đặt khớp bộ hiện tại.
 */
export function toCostItemPayload(item: HrCostItem, canSeeMoney: boolean): HeadcountPlanCostItemPayload {
  return {
    code: item.code,
    name: item.name.trim(),
    group_id: item.group_id,
    calc_method: item.calc_method,
    rate: Number(item.rate) || 0,
    factor: Number(item.factor) || 0,
    cap_amount: canSeeMoney ? toInt(item.cap_amount) : null,
    amount: canSeeMoney ? toInt(item.amount) : null,
    base_codes: item.base_codes,
    applies_to: item.applies_to,
    position_ids: item.position_ids,
    months: [...item.months].sort((a, b) => a - b),
    actual_source: item.actual_source,
    sort_order: item.sort_order,
  }
}

function toLinePayload(line: HeadcountPlanDraft['lines'][number], canSeeMoney: boolean): HeadcountPlanLinePayload {
  //  Bỏ khóa mang giá trị rỗng: schema `amounts` là dict[str, int] — một `null` lẻ là 422 cả bản nháp.
  const amounts = canSeeMoney
    ? Object.fromEntries(
        Object.entries(line.amounts ?? {})
          .filter(([, v]) => v !== null && v !== undefined)
          .map(([k, v]) => [k, toInt(v)]),
      )
    : null
  return { position_id: line.position_id, headcounts: line.headcounts.map(toInt), amounts, note: line.note }
}

/**
 * Bản nháp `POST /compute` — header + khoản + dòng. Khoản người dùng đã TẮT ở khối «Chi phí khác» bị bỏ
 * ở đây, nên nó vừa không vào bảng Tổng vừa biến khỏi kế hoạch khi lưu.
 */
export function buildDraftPayload(draft: HeadcountPlanDraft, canSeeMoney: boolean): HeadcountPlanDraftPayload {
  const { items, lines } = dropExcludedCostItems(draft.cost_items, draft.lines)
  return {
    year: draft.year,
    period_type: draft.period_type,
    period_no: draft.period_no,
    company_id: draft.company_id,
    department_id: draft.department_id,
    basis_no: draft.basis_no.trim(),
    basis_date: draft.basis_date || null,
    approver_employee_id: draft.approver_employee_id,
    note: draft.note.trim(),
    cost_items: finalizeCostItems(items).map((i) => toCostItemPayload(i, canSeeMoney)),
    lines: lines.map((l) => toLinePayload(l, canSeeMoney)),
  }
}

/** `PUT /{id}` — thay nguyên, kèm văn bản liên kết. */
export function buildPlanPayload(draft: HeadcountPlanDraft, canSeeMoney: boolean): HeadcountPlanPayload {
  return {
    ...buildDraftPayload(draft, canSeeMoney),
    //  Giữ CẢ văn bản người này không xem được: PUT thay nguyên danh sách, bỏ đi là gỡ mất liên kết
    //  người khác đã gắn mà người lưu không hề nhìn thấy. Văn bản ĐÃ XÓA thì thôi giữ.
    document_ids: draft.documents.filter((d) => !d.deleted).map((d) => d.document_id),
  }
}

/**
 * `POST /` lúc tạo. Chi phí còn nguyên như vừa điền sẵn từ mẫu gợi ý → KHÔNG gửi `cost_items`, để backend
 * tự chép (giữ đúng số tiền của mẫu cả khi người lập không được xem tiền). Người dùng đã sửa, hoặc bộ dựng
 * ở giao diện (`template_id = 0`) → gửi đúng bộ trên form, không thì phần sửa mất im lặng.
 */
export function buildCreatePayload(draft: HeadcountPlanDraft, canSeeMoney: boolean): HeadcountPlanCreatePayload {
  const { cost_items: items, ...rest } = buildPlanPayload(draft, canSeeMoney)
  return {
    ...rest,
    template_id: draft.template_id,
    ...(draft.cost_items_edited || !draft.template_id ? { cost_items: items } : {}),
  }
}
