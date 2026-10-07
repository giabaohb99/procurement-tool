import { describe, expect, it } from 'vitest'

import {
  TEMPLATE_MAX_BYTES,
  buildTemplateFormData,
  validateTemplateFile,
} from './labor-contract-template-api'

const docx = (name = 'mau.docx', size = 10) =>
  new File([new Uint8Array(size)], name, {
    type: 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
  })
const values = { name: ' Mẫu thử việc ', company_id: 3, contract_type: 1, note: ' ghi chú ' }

describe('buildTemplateFormData', () => {
  it('gửi đủ trường, cắt khoảng trắng đầu/cuối', () => {
    const form = buildTemplateFormData(values, docx())
    expect(form.get('name')).toBe('Mẫu thử việc')
    expect(form.get('company_id')).toBe('3')
    expect(form.get('contract_type')).toBe('1')
    expect(form.get('note')).toBe('ghi chú')
    expect(form.get('file')).toBeInstanceOf(File)
  })

  // 0 là «chưa chọn»: gửi đi sẽ gắn nhầm pháp nhân hoặc ăn 422 vô ích.
  it.each([0, -1, 1.5, Number.NaN])('chặn company_id = %p', (company_id) => {
    expect(() => buildTemplateFormData({ ...values, company_id }, docx())).toThrow('Chọn pháp nhân')
  })

  it.each([0, -3, Number.NaN])('chặn contract_type = %p', (contract_type) => {
    expect(() => buildTemplateFormData({ ...values, contract_type }, docx())).toThrow('Chọn loại hợp đồng')
  })
})

describe('validateTemplateFile', () => {
  it('nhận .docx hợp lệ, kể cả đuôi viết hoa', () => {
    expect(validateTemplateFile(docx('MAU.DOCX'))).toBeNull()
  })

  it('chặn thiếu tệp, sai đuôi, đuôi kép giả, tệp rỗng', () => {
    expect(validateTemplateFile(null)).not.toBeNull()
    expect(validateTemplateFile(undefined)).not.toBeNull()
    expect(validateTemplateFile(docx('mau.doc'))).not.toBeNull()
    expect(validateTemplateFile(docx('mau.docx.exe'))).not.toBeNull()
    expect(validateTemplateFile(docx('mau.docm'))).not.toBeNull()
    expect(validateTemplateFile(docx('mau.docx', 0))).not.toBeNull()
  })

  it('đúng 10 MB còn nhận, quá một byte thì chặn', () => {
    expect(validateTemplateFile(docx('a.docx', TEMPLATE_MAX_BYTES))).toBeNull()
    expect(validateTemplateFile(docx('a.docx', TEMPLATE_MAX_BYTES + 1))).not.toBeNull()
  })
})
