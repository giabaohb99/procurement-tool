import { describe, expect, it } from 'vitest'

import { SURVEY_APPROVE_ALL, filterSurveyLines } from './supplier-survey-filter'

interface Row {
  line_approve: string
  survey_code: string
  supplier_name: string
}

const ROWS: Row[] = [
  { line_approve: 'Chờ duyệt', survey_code: 'KS001', supplier_name: 'Công ty Bao bì ABC' },
  { line_approve: 'Đã duyệt', survey_code: 'KS002', supplier_name: 'Nhựa Tân Tiến' },
  { line_approve: 'Không duyệt', survey_code: 'KS003', supplier_name: 'Bao bì ABC Miền Nam' },
]

const searchable = (row: Row) => [row.survey_code, row.supplier_name]

describe('filterSurveyLines', () => {
  it('trả nguyên danh sách khi chưa gõ gì và đang để tất cả trạng thái', () => {
    expect(filterSurveyLines(ROWS, '', SURVEY_APPROVE_ALL, searchable)).toHaveLength(3)
  })

  it('lọc đúng một trạng thái duyệt', () => {
    const result = filterSurveyLines(ROWS, '', 'Đã duyệt', searchable)
    expect(result.map((r) => r.survey_code)).toEqual(['KS002'])
  })

  it('tìm không phân biệt hoa thường', () => {
    const result = filterSurveyLines(ROWS, 'ks00', SURVEY_APPROVE_ALL, searchable)
    expect(result).toHaveLength(3)
  })

  it('bỏ khoảng trắng thừa hai đầu từ khóa', () => {
    const result = filterSurveyLines(ROWS, '  Tân Tiến  ', SURVEY_APPROVE_ALL, searchable)
    expect(result.map((r) => r.survey_code)).toEqual(['KS002'])
  })

  it('cộng dồn cả hai điều kiện chứ không lấy điều kiện nào cũng được', () => {
    const result = filterSurveyLines(ROWS, 'ABC', 'Chờ duyệt', searchable)
    expect(result.map((r) => r.survey_code)).toEqual(['KS001'])
  })

  it('dò từng ô riêng, không nối các ô lại thành một chuỗi', () => {
    // Nối `survey_code` + `supplier_name` thành "KS001 Công ty Bao bì ABC" thì
    // chuỗi vắt qua ranh giới hai ô sẽ khớp — người dùng không giải thích nổi
    // vì sao dòng đó hiện ra.
    const result = filterSurveyLines(ROWS, 'KS001 Công', SURVEY_APPROVE_ALL, searchable)
    expect(result).toHaveLength(0)
  })

  it('trả danh sách rỗng khi không dòng nào khớp, không trả về nguyên bản', () => {
    expect(filterSurveyLines(ROWS, 'không có thật', SURVEY_APPROVE_ALL, searchable)).toEqual([])
  })
})
