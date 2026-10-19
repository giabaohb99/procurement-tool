import { describe, expect, it } from 'vitest'

import { buildCsv, escapeCsvCell } from './csv-export'

describe('escapeCsvCell', () => {
  it('quotes every cell and doubles inner quotes so commas and newlines stay in one column', () => {
    expect(escapeCsvCell('a,b')).toBe('"a,b"')
    expect(escapeCsvCell('dòng 1\ndòng 2')).toBe('"dòng 1\ndòng 2"')
    expect(escapeCsvCell('nói "không"')).toBe('"nói ""không"""')
  })

  it('neutralises spreadsheet formulas coming from outside strings (client name, tool name)', () => {
    for (const evil of ['=HYPERLINK("http://x","bam")', '+1+1', '-2', '@SUM(A1)', '\tx', '\rx']) {
      expect(escapeCsvCell(evil).startsWith(`"'`)).toBe(true)
    }
    //  Số âm thật của cột thời gian không có — nhưng chuỗi thường có gạch ngang ở GIỮA thì giữ nguyên.
    expect(escapeCsvCell('purchase-report')).toBe('"purchase-report"')
  })

  it('writes empty for null and undefined, and keeps zero', () => {
    expect(escapeCsvCell(null)).toBe('""')
    expect(escapeCsvCell(undefined)).toBe('""')
    expect(escapeCsvCell(0)).toBe('"0"')
  })
})

describe('buildCsv', () => {
  const columns = [
    { header: 'Công cụ', value: (r: { tool: string; n: number }) => r.tool },
    { header: 'Số', value: (r: { tool: string; n: number }) => r.n },
  ]

  it('starts with a UTF-8 BOM so Excel reads Vietnamese, uses CRLF between lines', () => {
    const csv = buildCsv([{ tool: 'a', n: 1 }, { tool: 'b', n: 2 }], columns)
    expect(csv.charCodeAt(0)).toBe(0xfeff)
    expect(csv.slice(1).split('\r\n')).toEqual(['"Công cụ","Số"', '"a","1"', '"b","2"'])
  })

  it('still writes the header row when there is nothing to export', () => {
    expect(buildCsv([], columns).slice(1)).toBe('"Công cụ","Số"')
  })
})
