import { describe, expect, it } from 'vitest'

import { hasQuoteImportBatch, packagingQuoteSourceText } from './packaging-quote-source'

describe('packagingQuoteSourceText', () => {
  it('writes "Nhập tay" and "Nhập Excel (lô #N)" — same words as the v1 screen', () => {
    expect(packagingQuoteSourceText(1, 0)).toBe('Nhập tay')
    expect(packagingQuoteSourceText(2, 57)).toBe('Nhập Excel (lô #57)')
  })

  it('drops the batch part when an Excel quote has no batch id, and stays empty without a source', () => {
    expect(packagingQuoteSourceText(2, 0)).toBe('Nhập Excel')
    expect(packagingQuoteSourceText(undefined, undefined)).toBe('')
    expect(packagingQuoteSourceText(null, 5)).toBe('')
  })

  it('only an Excel quote with a real batch id has an import batch to open', () => {
    expect(hasQuoteImportBatch(2, 57)).toBe(true)
    expect(hasQuoteImportBatch(2, 0)).toBe(false)
    expect(hasQuoteImportBatch(1, 0)).toBe(false)
    expect(hasQuoteImportBatch(undefined, undefined)).toBe(false)
  })
})
