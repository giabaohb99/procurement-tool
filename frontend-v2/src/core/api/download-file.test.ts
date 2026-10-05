// `filenameFromContentDisposition`: rút tên tệp từ header trả về bởi backend (xem
// `app/core/export_xlsx.py` — chỉ `filename=`; `customs/controller.py` — kèm cả `filename*=`
// RFC 5987). `downloadFile`: tên THẬT từ header phải THẮNG tên dự phòng truyền vào — lỗi M4 của
// review «Xuất Excel Thuốc BVTV» là mọi lượt xuất đều lưu cùng một tên cứng, bất kể backend trả
// tên gì (vd kèm ngày giờ xuất, hoặc khác nhau theo phạm vi xuất).
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { downloadFile, filenameFromContentDisposition } from './download-file'

const { httpClientGet } = vi.hoisted(() => ({ httpClientGet: vi.fn() }))

vi.mock('./http-client', () => ({
  httpClient: { get: httpClientGet },
}))

describe('filenameFromContentDisposition', () => {
  it('returns undefined for an empty, missing or header-less value', () => {
    expect(filenameFromContentDisposition(undefined)).toBeUndefined()
    expect(filenameFromContentDisposition(null)).toBeUndefined()
    expect(filenameFromContentDisposition('')).toBeUndefined()
    //  Hacker gửi header không có `filename` nào cả — đừng vớ bậy một đoạn chữ khác làm tên tệp.
    expect(filenameFromContentDisposition('attachment')).toBeUndefined()
    expect(filenameFromContentDisposition('inline; size=0')).toBeUndefined()
  })

  it('reads a plain quoted filename — the only form export_xlsx.py sends', () => {
    expect(
      filenameFromContentDisposition('attachment; filename="thuoc-bvtv-toan-bo-02102026.xlsx"'),
    ).toBe('thuoc-bvtv-toan-bo-02102026.xlsx')
  })

  it('reads an unquoted filename too', () => {
    expect(filenameFromContentDisposition('attachment; filename=plain.xlsx')).toBe('plain.xlsx')
  })

  it('prefers the RFC 5987 filename* over the plain ASCII fallback, decoding percent-escapes', () => {
    const disposition =
      'attachment; filename="ten.xlsx"; filename*=UTF-8\'\'t%C3%AAn-c%C3%B3-d%E1%BA%A5u.xlsx'
    expect(filenameFromContentDisposition(disposition)).toBe('tên-có-dấu.xlsx')
  })

  it('falls back to the plain filename when filename* has broken percent-encoding', () => {
    //  `%` lẻ (không đủ hai chữ số theo sau) làm `decodeURIComponent` ném lỗi — không được để lỗi
    //  đó rơi ra ngoài, phải tự rơi xuống nhánh `filename` thường.
    const disposition = 'attachment; filename="ascii.xlsx"; filename*=UTF-8\'\'%'
    expect(filenameFromContentDisposition(disposition)).toBe('ascii.xlsx')
  })

  it('returns undefined rather than an empty string when the filename value is blank', () => {
    expect(filenameFromContentDisposition('attachment; filename=""')).toBeUndefined()
  })
})

describe('downloadFile', () => {
  beforeEach(() => {
    //  jsdom không cài hai hàm này (xem `survey-report-page.test.tsx`) — chỉ cần chúng tồn tại để
    //  nhánh tải xuống chạy hết, không ném `TypeError`.
    URL.createObjectURL = vi.fn(() => 'blob:test')
    URL.revokeObjectURL = vi.fn()
    httpClientGet.mockReset()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  it('names the saved file after Content-Disposition, ignoring the fallback name', async () => {
    httpClientGet.mockResolvedValue({
      data: new Blob(['x']),
      headers: { 'content-disposition': 'attachment; filename="tu-backend-02102026.xlsx"' },
    })

    let downloadedName = ''
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloadedName = this.download
    })

    await downloadFile('/api/x/export', 'ten-du-phong.xlsx')

    expect(downloadedName).toBe('tu-backend-02102026.xlsx')
    clickSpy.mockRestore()
  })

  it('falls back to the given name when the backend sends no Content-Disposition', async () => {
    httpClientGet.mockResolvedValue({ data: new Blob(['x']), headers: {} })

    let downloadedName = ''
    const clickSpy = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(function (
      this: HTMLAnchorElement,
    ) {
      downloadedName = this.download
    })

    await downloadFile('/api/x/export', 'ten-du-phong.xlsx')

    expect(downloadedName).toBe('ten-du-phong.xlsx')
    clickSpy.mockRestore()
  })

  it('forwards params and requests a blob response', async () => {
    httpClientGet.mockResolvedValue({ data: new Blob(['x']), headers: {} })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})

    await downloadFile('/api/x/export', 'fallback.xlsx', { scope: 'all' })

    expect(httpClientGet).toHaveBeenCalledWith('/api/x/export', {
      responseType: 'blob',
      params: { scope: 'all' },
    })
  })

  it('revokes the object URL even when the click handler throws', async () => {
    httpClientGet.mockResolvedValue({ data: new Blob(['x']), headers: {} })
    vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {
      throw new Error('boom')
    })

    await expect(downloadFile('/api/x/export', 'fallback.xlsx')).rejects.toThrow('boom')
    expect(URL.revokeObjectURL).toHaveBeenCalledWith('blob:test')
  })
})
