import { describe, expect, it } from 'vitest'

import type { ApprovalFlow } from '../types/approval'
import { ALL, filterApprovalFlows } from './filter-approval-flows'

function luong(overrides: Partial<ApprovalFlow> = {}): ApprovalFlow {
  return {
    id: 1,
    entity: 'purchase_order',
    code: 'PO-STD',
    name: 'Luồng mua hàng',
    description: 'Áp cho mọi đơn thường',
    version_no: 1,
    is_active: true,
    company_id: null,
    priority: 0,
    condition: '',
    node_count: 2,
    duplicate_default_warning: '',
    ...overrides,
  }
}

const KHONG_LOC = { entity: ALL, dung: ALL, keyword: '' }

describe('filterApprovalFlows', () => {
  it('không khai điều kiện nào thì giữ nguyên cả danh sách', () => {
    const rows = [luong({ id: 1 }), luong({ id: 2, is_active: false })]
    expect(filterApprovalFlows(rows, KHONG_LOC)).toHaveLength(2)
  })

  it('lọc theo loại chứng từ', () => {
    const rows = [luong({ id: 1, entity: 'purchase_order' }), luong({ id: 2, entity: 'document' })]

    const ket_qua = filterApprovalFlows(rows, { ...KHONG_LOC, entity: 'document' })
    expect(ket_qua.map((r) => r.id)).toEqual([2])
  })

  it('"Ngừng" lấy đúng luồng đã tắt, không phải luồng đang dùng', () => {
    //  `dung === 'active'` so với `is_active` — đảo dấu ở đây thì màn hình vẫn
    //  hiện một bảng trông hợp lý, chỉ là ngược hẳn ý người lọc.
    const rows = [luong({ id: 1, is_active: true }), luong({ id: 2, is_active: false })]

    expect(filterApprovalFlows(rows, { ...KHONG_LOC, dung: 'inactive' }).map((r) => r.id)).toEqual([
      2,
    ])
    expect(filterApprovalFlows(rows, { ...KHONG_LOC, dung: 'active' }).map((r) => r.id)).toEqual([1])
  })

  it('tìm được theo MÃ luồng, không chỉ theo tên', () => {
    const rows = [luong({ id: 1, code: 'PO-STD' }), luong({ id: 2, code: 'PO-GAP' })]

    expect(filterApprovalFlows(rows, { ...KHONG_LOC, keyword: 'gap' }).map((r) => r.id)).toEqual([2])
  })

  it('tìm được theo mô tả', () => {
    const rows = [
      luong({ id: 1, description: 'Áp cho đơn trên 100 triệu' }),
      luong({ id: 2, description: 'Đơn nhỏ' }),
    ]

    expect(filterApprovalFlows(rows, { ...KHONG_LOC, keyword: '100 triệu' }).map((r) => r.id)).toEqual(
      [1],
    )
  })

  it('bỏ qua hoa thường và khoảng trắng thừa hai đầu', () => {
    const rows = [luong({ id: 1, name: 'Luồng mua hàng' })]

    expect(filterApprovalFlows(rows, { ...KHONG_LOC, keyword: '  MUA HÀNG  ' })).toHaveLength(1)
  })

  it('ba điều kiện cùng lúc thì phải thỏa CẢ BA', () => {
    const rows = [
      luong({ id: 1, entity: 'document', is_active: true, name: 'Duyệt quy chế' }),
      luong({ id: 2, entity: 'document', is_active: false, name: 'Duyệt quy chế cũ' }),
      luong({ id: 3, entity: 'purchase_order', is_active: true, name: 'Duyệt quy chế mua' }),
    ]

    const ket_qua = filterApprovalFlows(rows, {
      entity: 'document',
      dung: 'active',
      keyword: 'quy chế',
    })
    expect(ket_qua.map((r) => r.id)).toEqual([1])
  })

  it('mô tả rỗng không làm hỏng phép tìm', () => {
    //  Backend trả chuỗi rỗng, nhưng dữ liệu cũ nhập tay từng lọt `null` xuống.
    const rows = [luong({ id: 1, description: null as unknown as string, name: 'Luồng A' })]

    expect(filterApprovalFlows(rows, { ...KHONG_LOC, keyword: 'luồng' })).toHaveLength(1)
  })
})
