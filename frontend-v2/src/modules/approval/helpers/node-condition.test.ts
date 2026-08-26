import { describe, expect, it } from 'vitest'

import { buildCondition, describeRow, parseCondition } from './node-condition'

const VALID_CELL = (field: string) => ['secrecy_level', 'doc_type_id'].includes(field)

describe('parseCondition', () => {
  it('chuỗi rỗng = không có điều kiện, KHÔNG phải khai tay', () => {
    expect(parseCondition('', VALID_CELL)).toEqual({ rows: [], advanced: false })
    expect(parseCondition('   ', VALID_CELL)).toEqual({ rows: [], advanced: false })
  })

  it('đọc được điều kiện một dòng', () => {
    const result = parseCondition('[{"field":"secrecy_level","op":"gte","value":3}]', VALID_CELL)

    expect(result.advanced).toBe(false)
    expect(result.rows).toEqual([{ field: 'secrecy_level', op: 'gte', value: 3 }])
  })

  it('phép "thuộc" giữ nguyên danh sách số', () => {
    const result = parseCondition('[{"field":"doc_type_id","op":"in","value":[3,5]}]', VALID_CELL)

    expect(result.rows).toEqual([{ field: 'doc_type_id', op: 'in', value: [3, 5] }])
  })

  it('JSON hỏng thì báo KHAI TAY, không im lặng trả về rỗng', () => {
    //  Trả rỗng lặng lẽ là bộ dựng ghi đè mất điều kiện người khác đã viết —
    //  luồng đổi hành vi mà không ai bấm gì.
    expect(parseCondition('[{"field":', VALID_CELL).advanced).toBe(true)
  })

  it('ô không nằm trong danh mục thì xếp vào khai tay', () => {
    const result = parseCondition('[{"field":"total","op":"gte","value":50000000}]', VALID_CELL)

    expect(result.advanced).toBe(true)
    expect(result.rows).toEqual([])
  })

  it('phép lạ hoặc giá trị không phải số cũng là khai tay', () => {
    expect(parseCondition('[{"field":"secrecy_level","op":"like","value":3}]', VALID_CELL).advanced).toBe(
      true,
    )
    expect(
      parseCondition('[{"field":"secrecy_level","op":"eq","value":"cao"}]', VALID_CELL).advanced,
    ).toBe(true)
  })

  it('danh sách rỗng của phép "thuộc" là khai tay — nó không bao giờ khớp', () => {
    expect(parseCondition('[{"field":"doc_type_id","op":"in","value":[]}]', VALID_CELL).advanced).toBe(
      true,
    )
  })

  it('một dòng hỏng thì cả chuỗi coi như khai tay, không lấy phần đọc được', () => {
    const raw = '[{"field":"secrecy_level","op":"gte","value":3},{"field":"total","op":"gte","value":1}]'

    expect(parseCondition(raw, VALID_CELL).advanced).toBe(true)
  })
})

describe('buildCondition', () => {
  it('không dòng nào = chuỗi rỗng (luôn chạy)', () => {
    expect(buildCondition([])).toBe('')
  })

  it('bỏ dòng thang chưa chọn mức (giá trị 0)', () => {
    //  `{"value":0}` là điều kiện không mức nào khớp — bước lặng lẽ không chạy.
    expect(buildCondition([{ field: 'secrecy_level', op: 'gte', value: 0 }])).toBe('')
  })

  it('bỏ dòng "thuộc" chưa chọn giá trị nào', () => {
    //  Gửi `in: []` xuống backend là điều kiện không bao giờ khớp: bước lặng lẽ
    //  không chạy và người khai tưởng mình khai thiếu ở chỗ khác.
    const raw = buildCondition([
      { field: 'doc_type_id', op: 'in', value: [] },
      { field: 'secrecy_level', op: 'gte', value: 3 },
    ])

    expect(JSON.parse(raw)).toEqual([{ field: 'secrecy_level', op: 'gte', value: 3 }])
  })

  it('đi vòng tròn parse → build ra đúng chuỗi ban đầu', () => {
    const rows = parseCondition(
      '[{"field":"secrecy_level","op":"gte","value":3},{"field":"doc_type_id","op":"in","value":[2]}]',
      VALID_CELL,
    ).rows

    expect(buildCondition(rows)).toBe(
      '[{"field":"secrecy_level","op":"gte","value":3},{"field":"doc_type_id","op":"in","value":[2]}]',
    )
  })
})

describe('describeRow', () => {
  it('mỗi phép có khuôn câu riêng, không ghép máy móc', () => {
    expect(describeRow('gte', 'Mức mật', 'Mật')).toBe('Mức mật từ Mật trở lên')
    expect(describeRow('lte', 'Độ khẩn', 'Khẩn')).toBe('Độ khẩn từ Khẩn trở xuống')
    expect(describeRow('eq', 'Mức mật', 'Nội bộ')).toBe('Mức mật là Nội bộ')
    expect(describeRow('in', 'Loại văn bản', 'Quy chế, Quy trình')).toBe(
      'Loại văn bản thuộc Quy chế, Quy trình',
    )
    expect(describeRow('not_in', 'Pháp nhân', 'DEGO')).toBe('Pháp nhân không thuộc DEGO')
  })
})
