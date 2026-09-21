import { describe, expect, it } from 'vitest'

import { OUT_OF_CATALOG_SUFFIX, resolveCatalogSelection } from './catalog-selection'

/**
 * bao-CR-372 (port v2). Lỗi đã gặp trên prod: dòng hàng mang phân loại `ICARE` không có
 * trong danh mục — ngoài bảng ô Select nuốt thành "-- Phân loại --", popup vẫn hiện ICARE.
 */
describe('resolveCatalogSelection', () => {
  const catalog = [
    { value: 'Bao bì', label: 'Bao bì' },
    { value: 'Hóa chất', label: 'Hóa chất' },
  ]

  it('keeps a value that is not in the catalog visible with an explicit label', () => {
    const result = resolveCatalogSelection('ICARE', catalog)
    expect(result.selected).toBe('ICARE')
    expect(result.options[0]).toEqual({ value: 'ICARE', label: `ICARE${OUT_OF_CATALOG_SUFFIX}` })
    expect(result.options).toHaveLength(catalog.length + 1)
  })

  it('snaps a case-insensitive match to the catalog spelling instead of flagging it', () => {
    const result = resolveCatalogSelection('bao BÌ', catalog)
    expect(result.selected).toBe('Bao bì')
    expect(result.options).toBe(catalog)
  })

  it('does not flag anything while the catalog has not loaded yet', () => {
    // Danh mục rỗng = chưa tải xong. Chèn option để chữ không biến mất, nhưng KHÔNG dán
    // nhãn "(ngoài danh mục)" kẻo lần vẽ đầu của mọi phiếu cũ gắn nhãn sai rồi mới tự sửa.
    const result = resolveCatalogSelection('ICARE', [])
    expect(result.selected).toBe('ICARE')
    expect(result.options).toEqual([{ value: 'ICARE', label: 'ICARE' }])
  })

  it('treats blank and whitespace-only values as nothing selected', () => {
    expect(resolveCatalogSelection('', catalog)).toEqual({ selected: '', options: catalog })
    expect(resolveCatalogSelection('   ', catalog)).toEqual({ selected: '', options: catalog })
  })

  it('trims the stored value before matching and before inserting it', () => {
    expect(resolveCatalogSelection(' Hóa chất ', catalog).selected).toBe('Hóa chất')
    expect(resolveCatalogSelection(' ICARE ', catalog).options[0].value).toBe('ICARE')
  })
})
