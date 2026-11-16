import { describe, expect, it } from 'vitest'

import type { WarehouseOption } from '../api/purchase-request-support-api'
import { resolveWarehouseCode, resolveWarehouseByName } from './warehouse-ref'

const WAREHOUSES: WarehouseOption[] = [
  { id: 1, code: 'Dego Cần Thơ', name: 'CÔNG TY TNHH DEGO HOLDING' },
  { id: 2, code: 'KHO-HN', name: 'Kho Hà Nội' },
  { id: 3, code: 'KHO-HN2', name: 'Kho Hà Nội' },
]

describe('resolveWarehouseCode (bao-CR-759)', () => {
  it('ưu tiên mã đã lưu trên dòng YCMH', () => {
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse_code: 'KHO-HN2', warehouse: 'Kho Hà Nội' })).toBe('KHO-HN2')
  })

  it('dòng cũ chưa có mã thì tra theo TÊN kho, khớp đúng tên', () => {
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse: 'CÔNG TY TNHH DEGO HOLDING' })).toBe('Dego Cần Thơ')
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse: ' CÔNG TY TNHH DEGO HOLDING ' })).toBe('Dego Cần Thơ')
  })

  it('trùng tên thì lấy kho đứng trước trong danh mục', () => {
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse: 'Kho Hà Nội' })).toBe('KHO-HN')
  })

  it('mã đã lưu vẫn dùng dù danh mục chưa nạp xong (kho mất khỏi danh mục cũng giữ)', () => {
    expect(resolveWarehouseCode([], { warehouse_code: 'KHO-CU', warehouse: 'Kho cũ' })).toBe('KHO-CU')
  })

  it('không khớp gì thì trả rỗng — để người lập chọn, đừng đoán', () => {
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse: 'Kho lạ' })).toBe('')
    expect(resolveWarehouseCode(WAREHOUSES, { warehouse: '' })).toBe('')
  })
})

describe('resolveWarehouseByName', () => {
  it('trả cả mã lẫn tên để ghi một lượt vào dòng YCMH', () => {
    expect(resolveWarehouseByName(WAREHOUSES, 'Kho Hà Nội')).toEqual({
      warehouse: 'Kho Hà Nội',
      warehouse_code: 'KHO-HN',
    })
    expect(resolveWarehouseByName(WAREHOUSES, '')).toEqual({ warehouse: '', warehouse_code: '' })
  })
})
