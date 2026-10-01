import { describe, expect, it } from 'vitest'

import {
  buildPesticideListSearch,
  buildPesticideParams,
  formatBannedFilterLabel,
  resolvePesticideEmptyMessage,
} from './customs-pesticide'

describe('buildPesticideParams', () => {
  it('sends nothing for an empty filter set', () => {
    expect(buildPesticideParams({ q: '', status: '', pestGroup: '' })).toEqual({})
  })

  //  `status` ở backend là `int | None`: gửi chuỗi rỗng hay chữ thì FastAPI trả 422 và cả bảng đỏ.
  it.each(['', ' ', 'abc', '1a', '-1', '1.5'])('never sends a non-numeric status (%j)', (status) => {
    expect(buildPesticideParams({ q: '', status, pestGroup: '' })).not.toHaveProperty('status')
  })

  it('trims the keyword and drops a whitespace-only one', () => {
    expect(buildPesticideParams({ q: '  atrazine ', status: '1', pestGroup: 'Thuốc trừ cỏ' })).toEqual({
      q: 'atrazine',
      status: '1',
      pest_group: 'Thuốc trừ cỏ',
    })
    expect(buildPesticideParams({ q: '   ', status: '', pestGroup: '' })).toEqual({})
  })

  it('treats the «Tất cả …» option as no filter for both selects', () => {
    expect(buildPesticideParams({ q: '', status: 'all', pestGroup: 'all' })).toEqual({})
  })

  it('keeps status 0 (unknown) — it is a real filter value, not "all"', () => {
    expect(buildPesticideParams({ q: '', status: '0', pestGroup: '' })).toEqual({ status: '0' })
  })
})

describe('resolvePesticideEmptyMessage', () => {
  it('blames the filter when the catalog has data', () => {
    expect(resolvePesticideEmptyMessage(6919, true)).toMatch(/khớp bộ lọc/)
    expect(resolvePesticideEmptyMessage(1, false)).toMatch(/khớp bộ lọc/)
  })

  it('says the catalog is empty, and only offers the import button to those who can import', () => {
    expect(resolvePesticideEmptyMessage(0, true)).toMatch(/Nạp danh mục/)
    expect(resolvePesticideEmptyMessage(0, false)).not.toMatch(/Bấm/)
  })
})

describe('banned-ingredient filter', () => {
  it('sends banned_only only for the «only» choice', () => {
    expect(buildPesticideParams({ q: '', status: '', pestGroup: '', banned: 'only' })).toEqual({
      banned_only: 'true',
    })
    for (const banned of ['all', '', 'ONLY', 'true', undefined]) {
      expect(buildPesticideParams({ q: '', status: '', pestGroup: '', banned })).toEqual({})
    }
  })

  it('never shows a reassuring count when there is no banned list to compare against', () => {
    expect(formatBannedFilterLabel(0, 0)).toBe('Có hoạt chất cấm (chưa có danh sách cấm)')
    expect(formatBannedFilterLabel(-1, 5)).toMatch(/chưa có danh sách cấm/)
    expect(formatBannedFilterLabel(30, 0)).toBe('Có hoạt chất cấm (0)')
    expect(formatBannedFilterLabel(30, 1234)).toBe('Có hoạt chất cấm (1.234)')
  })

  it('reads an empty banned-only result as a clean catalog, not as a filter mistake', () => {
    expect(resolvePesticideEmptyMessage(6919, true, 30)).toMatch(/Không thuốc nào .* chứa hoạt chất cấm/)
    expect(resolvePesticideEmptyMessage(6919, true, 0)).toMatch(/Chưa có danh sách hoạt chất cấm/)
    expect(resolvePesticideEmptyMessage(6919, true)).toMatch(/khớp bộ lọc/)
    //  Chưa có danh mục thuốc thì nói chuyện đó trước, bộ lọc gì cũng vậy.
    expect(resolvePesticideEmptyMessage(0, true, 30)).toMatch(/Nạp danh mục/)
  })
})

describe('buildPesticideParams — sector', () => {
  it('sends the sector verbatim and drops the "all" choice', () => {
    expect(
      buildPesticideParams({ q: '', status: '', pestGroup: '', sector: 'THUỐC TRỪ MỐI' }),
    ).toEqual({ sector: 'THUỐC TRỪ MỐI' })
    expect(buildPesticideParams({ q: '', status: '', pestGroup: '', sector: 'all' })).toEqual({})
  })
})

describe('buildPesticideListSearch', () => {
  //  «Tra cứu nhanh» đếm trên MỌI tình trạng — mở danh sách mà để mặc định «Còn hiệu lực» là lệch số.
  it('always opens the list on every status', () => {
    expect(new URLSearchParams(buildPesticideListSearch({})).get('pstatus')).toBe('all')
  })

  it('maps the sidebar filters onto the list URL names and skips empty ones', () => {
    const params = new URLSearchParams(
      buildPesticideListSearch({ q: '  abamectin ', pestGroup: 'Thuốc trừ sâu', sector: 'all' }),
    )
    expect(params.get('pq')).toBe('abamectin')
    expect(params.get('pgroup')).toBe('Thuốc trừ sâu')
    expect(params.has('psector')).toBe(false)
  })

  it('encodes Vietnamese and "&" safely', () => {
    const search = buildPesticideListSearch({ q: 'A & B', sector: 'THUỐC XỬ LÝ HẠT GIỐNG' })
    const params = new URLSearchParams(search)
    expect(params.get('pq')).toBe('A & B')
    expect(params.get('psector')).toBe('THUỐC XỬ LÝ HẠT GIỐNG')
  })
})
