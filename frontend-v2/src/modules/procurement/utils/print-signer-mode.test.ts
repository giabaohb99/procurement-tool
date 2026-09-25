import { beforeEach, describe, expect, it } from 'vitest'

import { pickHeadSigner, readPrintSignerMode, savePrintSignerMode } from './print-signer-mode'

describe('pickHeadSigner — bao-CR-490', () => {
  const sources = {
    approver_name: 'Phó phòng ký',
    approver_signature: 'https://cdn/pho.png',
    dept_head_name: 'Trưởng phòng hồ sơ',
    dept_head_signature: 'https://cdn/truong.png',
  }

  it('người duyệt là mặc định', () => {
    expect(pickHeadSigner('approver', sources)).toEqual({
      name: 'Phó phòng ký',
      signature: 'https://cdn/pho.png',
    })
  })

  it('chọn trưởng phòng thì lấy trưởng phòng theo hồ sơ', () => {
    expect(pickHeadSigner('dept_head', sources)).toEqual({
      name: 'Trưởng phòng hồ sơ',
      signature: 'https://cdn/truong.png',
    })
  })

  it('phòng chưa gán trưởng thì lùi về người duyệt, không in ô trống', () => {
    expect(pickHeadSigner('dept_head', { ...sources, dept_head_name: '' })).toEqual({
      name: 'Phó phòng ký',
      signature: 'https://cdn/pho.png',
    })
    expect(pickHeadSigner('dept_head', {})).toEqual({ name: '', signature: '' })
  })
})

describe('nhớ lựa chọn theo máy', () => {
  beforeEach(() => window.localStorage.clear())

  it('chưa lưu gì → người duyệt; lưu rồi → đọc lại đúng; giá trị lạ → người duyệt', () => {
    expect(readPrintSignerMode()).toBe('approver')
    savePrintSignerMode('dept_head')
    expect(readPrintSignerMode()).toBe('dept_head')
    window.localStorage.setItem('erp.print.signer-mode', 'rac')
    expect(readPrintSignerMode()).toBe('approver')
  })
})
