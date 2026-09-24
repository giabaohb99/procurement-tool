import { describe, expect, it } from 'vitest'

import {
  APPLY_FIELDS,
  APPLY_FIELD_LABEL,
  APPLY_OPS,
  APPLY_OP_LABEL,
  DOC_KINDS,
  DOC_KIND_LABEL,
  DOC_KIND_ORDER,
  DOC_KIND_WARNING,
  conditionValueToText,
  isMultiValueOp,
  textToConditionValue,
  type ApplyOp,
} from './dossier-applicability'
import { fromApplyRules, toApplyRules } from './dossier-apply-rules'

/**
 * Bộ mã này GÕ TAY, phải khớp `backend/app/modules/dossier/applicability.py`
 * (`gen_status_ts.py` chỉ sinh cho bộ mã trạng thái CHUỖI). Mấy bài đếm dưới
 * đây đỏ lên là dấu hiệu hai bên vừa lệch nhau.
 */
describe('bộ mã điều kiện áp dụng', () => {
  it('đúng 4 loại chứng từ, mỗi loại có nhãn — thừa một mã là hứa một màn không ai dựng', () => {
    const kinds = Object.values(DOC_KINDS)
    expect(kinds).toHaveLength(4)
    for (const kind of kinds) expect(DOC_KIND_LABEL[kind]).toBeTruthy()
  })

  it('thứ tự bày ô chọn liệt kê ĐỦ 4 mã, không trùng, không sót', () => {
    //  Sót một mã thì nó biến mất khỏi màn khai mà không có gì đỏ lên —
    //  người dùng không cách nào gắn hồ sơ vào màn đó nữa.
    expect([...DOC_KIND_ORDER].sort()).toEqual([...Object.values(DOC_KINDS)].sort())
    expect(new Set(DOC_KIND_ORDER).size).toBe(DOC_KIND_ORDER.length)
  })

  it('đúng 2 chiều và 5 phép so sánh, mỗi thứ có nhãn', () => {
    expect(Object.values(APPLY_FIELDS)).toHaveLength(2)
    expect(Object.values(APPLY_OPS)).toHaveLength(5)
    for (const f of Object.values(APPLY_FIELDS)) expect(APPLY_FIELD_LABEL[f]).toBeTruthy()
    for (const o of Object.values(APPLY_OPS)) expect(APPLY_OP_LABEL[o]).toBeTruthy()
  })

  it('YCBG phải có câu cảnh báo, vì dòng của nó KHÔNG mang mã sản phẩm', () => {
    //  Mất câu này thì người khai gắn điều kiện theo sản phẩm cho YCBG, thấy nó
    //  không bao giờ khớp, và đi tìm lỗi ở một chỗ không có lỗi nào.
    expect(DOC_KIND_WARNING[DOC_KINDS.SURVEY_REQUEST]).toMatch(/chốt phương án/)
  })

  it('chỉ «thuộc» và «không thuộc» nhận nhiều giá trị', () => {
    expect(isMultiValueOp(APPLY_OPS.IN)).toBe(true)
    expect(isMultiValueOp(APPLY_OPS.NOT_IN)).toBe(true)
    for (const op of [APPLY_OPS.EQ, APPLY_OPS.NE, APPLY_OPS.CONTAINS]) {
      expect(isMultiValueOp(op)).toBe(false)
    }
  })
})

describe('đọc/ghi giá trị của một dòng điều kiện', () => {
  it('mảng đọc ra chuỗi ngăn bằng dấu phẩy, chuỗi giữ nguyên', () => {
    expect(conditionValueToText(['SP-001', 'SP-002'])).toBe('SP-001, SP-002')
    expect(conditionValueToText('SP-001')).toBe('SP-001')
  })

  it('bỏ khoảng trắng thừa và mục rỗng khi ghi ngược lại', () => {
    //  Người dùng gõ `SP-001, , SP-002 ,` là chuyện thường. Không dọn thì lưu
    //  xuống một mã tên là `" SP-002"` — không bao giờ khớp, im lặng.
    expect(textToConditionValue('SP-001, , SP-002 ,', APPLY_OPS.IN)).toEqual([
      'SP-001',
      'SP-002',
    ])
  })

  it('phép MỘT giá trị không tách theo dấu phẩy', () => {
    //  «chứa» với chuỗi có dấu phẩy là hợp lệ — tách ra là đổi nghĩa điều kiện.
    expect(textToConditionValue('Thùng, carton', APPLY_OPS.CONTAINS)).toBe('Thùng, carton')
  })

  it('đi vòng mảng → chuỗi → mảng không mất mục nào', () => {
    const original = ['SP-001', 'SP-002', 'SP-003']
    const back = textToConditionValue(conditionValueToText(original), APPLY_OPS.IN)
    expect(back).toEqual(original)
  })

  it('chuỗi rỗng ra mảng rỗng, không ra mảng một phần tử rỗng', () => {
    expect(textToConditionValue('', APPLY_OPS.IN)).toEqual([])
    expect(textToConditionValue('   ,  ,', APPLY_OPS.IN)).toEqual([])
  })

  it.each([
    ['chỉ dấu phẩy', ',,,'],
    ['toàn khoảng trắng', '     '],
  ])('%s không đẻ ra giá trị ma', (_label, input) => {
    expect(textToConditionValue(input, APPLY_OPS.NOT_IN)).toEqual([])
  })
})

describe('gộp/tách điều kiện áp dụng giữa biểu mẫu và hai cột DB', () => {
  it('bản ghi cũ (chưa có hai cột) đọc ra rỗng chứ không nổ', () => {
    //  Mọi hồ sơ lập trước 21/09/2026 mang `NULL` ở cả hai cột.
    expect(toApplyRules(undefined, undefined)).toEqual({ docKinds: [], conditions: [] })
  })

  it('giá trị không phải mảng cũng đọc ra rỗng', () => {
    //  Dữ liệu hỏng từ DB (ai đó sửa tay) không được làm trắng cả biểu mẫu.
    const broken = 'purchase_order' as unknown as undefined
    expect(toApplyRules(broken, broken)).toEqual({ docKinds: [], conditions: [] })
  })

  it('bỏ chọn HẾT màn thì điều kiện cũng bị dọn theo', () => {
    //  ⚠️ Điều kiện treo không gắn màn nào vừa không chạy vừa còn nằm đó —
    //  lần sau mở ra sửa sẽ thấy một bảng trông như đang hoạt động.
    const out = fromApplyRules({
      docKinds: [],
      conditions: [{ field: APPLY_FIELDS.PRODUCT_CODE, op: APPLY_OPS.EQ, value: 'SP-001' }],
    })
    expect(out).toEqual({ apply_doc_kinds: [], apply_conditions: [] })
  })

  it('còn ít nhất một màn thì giữ nguyên điều kiện', () => {
    const conditions = [
      { field: APPLY_FIELDS.ITEM_GROUP, op: APPLY_OPS.CONTAINS as ApplyOp, value: 'Thiết bị' },
    ]
    expect(fromApplyRules({ docKinds: [DOC_KINDS.PURCHASE_ORDER], conditions })).toEqual({
      apply_doc_kinds: [DOC_KINDS.PURCHASE_ORDER],
      apply_conditions: conditions,
    })
  })

  it('không truyền gì thì ra hai mảng rỗng, không ra undefined', () => {
    //  `undefined` lọt xuống payload là backend giữ nguyên giá trị cũ — người
    //  dùng bấm xóa hết điều kiện rồi Lưu, và không có gì thay đổi.
    expect(fromApplyRules(undefined)).toEqual({ apply_doc_kinds: [], apply_conditions: [] })
  })
})
