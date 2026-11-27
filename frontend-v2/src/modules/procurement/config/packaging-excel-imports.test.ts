// bao-CR-792 — mỗi loại nhập Excel của cụm Giá NVL sản xuất gác bằng khóa của màn chứa nút, và nút "Xóa dữ liệu của lô
// này" ở trang chi tiết lô (`IMPORT_PURGE_ENTITY`) phải hỏi ĐÚNG khóa đó — hai bảng khai ở hai phân hệ, canh cho khớp.
import { describe, expect, it } from 'vitest'

import {
  IMPORT_MODULE_PACKAGING_BOM,
  IMPORT_MODULE_PACKAGING_MISA,
  IMPORT_MODULE_PACKAGING_QUOTE,
  IMPORT_MODULES_WITH_PURGE,
  IMPORT_PURGE_ENTITY,
} from '@/modules/system/config/import-meta'

import {
  PACKAGING_BOM_IMPORT,
  PACKAGING_MISA_IMPORT,
  PACKAGING_QUOTE_IMPORT,
} from './packaging-excel-imports'

const KINDS = [PACKAGING_BOM_IMPORT, PACKAGING_QUOTE_IMPORT, PACKAGING_MISA_IMPORT]

describe('packaging Excel imports (bao-CR-792)', () => {
  it('guards each import kind with the key and action of the screen that owns the button', () => {
    expect(KINDS.map((kind) => [kind.module, kind.entity, kind.action])).toEqual([
      [IMPORT_MODULE_PACKAGING_BOM, 'packaging_bom', 'create'],
      [IMPORT_MODULE_PACKAGING_QUOTE, 'packaging_price_list', 'create'],
      [IMPORT_MODULE_PACKAGING_MISA, 'packaging_history', 'write'],
    ])
  })

  it('asks the same key to delete the data of a batch as to import that kind of batch', () => {
    for (const kind of KINDS) {
      expect(IMPORT_PURGE_ENTITY[kind.module], kind.label).toBe(kind.entity)
    }
  })

  it('declares a delete key for every batch type that shows the purge button', () => {
    for (const module of IMPORT_MODULES_WITH_PURGE) {
      expect(IMPORT_PURGE_ENTITY[module], `module ${module}`).toBeTruthy()
    }
  })
})
