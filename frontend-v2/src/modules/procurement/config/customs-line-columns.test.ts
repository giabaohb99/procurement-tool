// bao-CR-470 — chốt bố cục bảng dòng hàng theo yêu cầu đại ca 23/09/2026: HIỆN ĐỦ mọi cột,
// đúng thứ tự + đúng tiêu đề của tệp Excel GTT02 (`COLUMNS` ở
// backend/app/modules/customs/constants.py), hai cột suy ra nằm CUỐI, không có cột giá
// hiệu lực riêng. Backend đổi `COLUMNS` mà bảng không theo thì bài này đỏ.
import { describe, expect, it } from 'vitest'

import { CUSTOMS_LINE_COLUMNS } from './customs-line-columns'

/** Bản chép tay của `COLUMNS` (backend) — giữ nguyên cả chính tả của tệp gốc. */
const EXCEL_COLUMNS: [string, string][] = [
  ['reg_date', 'Ngày đăng ký'],
  ['office_code', 'Tên nơi mở tờ khai'],
  ['importer_tax_code', 'Mã doanh nghiệp XNK'],
  ['importer_name', 'Tên doanh nghiệp XNK'],
  ['partner_name', 'Đơn vị đối tác'],
  ['hs_code', 'Mã hàng khai báo'],
  ['line_no', 'Số thứ tự hàng'],
  ['product_name', 'Tên hàng'],
  ['price_usd', 'Đơn giá khai báo(USD)'],
  ['price_nt', 'Đơn giá NT khai báo'],
  ['adj_price_usd', 'Đơn giá điều chỉnh(USD)'],
  ['adj_price_nt', 'Đơn giá NT điều chỉnh'],
  ['currency', 'Nguyên tệ'],
  ['fx_rate', 'Tỷ giá nguyên tệ'],
  ['usd_rate', 'Tỷ giá USD'],
  ['quantity', 'Lượng'],
  ['unit_code', 'Đơn vị tính'],
  ['origin_country', 'Tên nuớc xuất xứ'],
  ['contract_no', 'Số hợp đồng'],
  ['contract_date', 'Ngày hợp đồng'],
  ['incoterm', 'Điều kiện giao hàng'],
  ['transport_mode', 'Phương tiện vận chuyển'],
  ['rate_import', 'Thuế suất XNK'],
  ['rate_excise', 'Thuế suất TTĐB'],
  ['rate_vat', 'Thuế suất VAT'],
  ['rate_safeguard', 'Thuế suất tự vệ'],
  ['tax_import', 'Thuế XNK'],
  ['tax_excise', 'Thuế TTĐB'],
  ['tax_vat', 'Thuế VAT'],
  ['tax_environment', 'Thuế môi trường'],
  ['tax_safeguard', 'Thuế tự vệ'],
  ['import_country', 'Nước nhận hàng'],
]

describe('CUSTOMS_LINE_COLUMNS', () => {
  it('follows the GTT02 Excel order and headers, then the derived and VND columns last', () => {
    const actual = CUSTOMS_LINE_COLUMNS.map((column) => [column.key, column.header])
    expect(actual).toEqual([
      //  bao-CR-608 — cột ID đầu bảng, khớp cột "ID" đầu Excel xuất ra.
      ['id', 'ID'],
      ...EXCEL_COLUMNS,
      //  bao-CR-603 — không còn chữ "(suy ra)": tệp nạp có cột thì giá trị lấy từ tệp.
      ['active_ingredient', 'Hoạt chất'],
      ['formulation', 'Hàm lượng / dạng'],
      //  bao-CR-493 — cùng thứ tự với Excel xuất ra.
      ['price_vnd_flat', 'Giá VND (thuế NK 7%)'],
      ['price_vnd_line_tax', 'Giá VND (thuế suất dòng)'],
      //  bao-CR-494 — nhãn Thành phẩm / Nguyên liệu, sau hai cột VND.
      ['product_kind', 'Phân loại'],
    ])
  })

  it('shows every column by default — nothing is pre-hidden', () => {
    expect(CUSTOMS_LINE_COLUMNS.filter((column) => column.defaultHidden)).toEqual([])
  })

  it('has no separate effective-price column and no duplicate keys', () => {
    const keys = CUSTOMS_LINE_COLUMNS.map((column) => column.key)
    expect(keys).not.toContain('effective_price_usd')
    expect(new Set(keys).size).toBe(keys.length)
  })

  //  duoc-CR-744 — trước đây KHÔNG cột nào khai `sortable`: bấm tiêu đề không có gì xảy ra, người dùng báo
  //  "không sort được". Canh hai chiều: cột nào cũng bấm được, và khóa gửi đi nằm trong danh sách khóa xếp được ở
  //  backend (`line_sort.LINE_SORT_KEYS`, bản chép tay — đổi một bên thì sửa bên kia, bài
  //  test_sap_xep_tra_cuu_thi_truong_cr744.py canh phía backend).
  it('makes every column sortable and every sort key one the backend knows', () => {
    const backendKeys = new Set([
      'id',
      ...EXCEL_COLUMNS.map(([key]) => key),
      'active_ingredient',
      'formulation',
      'price_vnd_flat',
      'price_vnd_line_tax',
      'product_kind',
    ])
    expect(CUSTOMS_LINE_COLUMNS.filter((column) => !column.sortable).map((column) => column.key)).toEqual([])
    expect(new Set(CUSTOMS_LINE_COLUMNS.map((column) => column.sortKey ?? column.key))).toEqual(backendKeys)
  })

  it('starts amount, quantity, rate and date columns from the largest / newest value', () => {
    const descFirst = (key: string) => CUSTOMS_LINE_COLUMNS.find((column) => column.key === key)?.sortDescFirst
    for (const key of ['reg_date', 'contract_date', 'price_usd', 'quantity', 'tax_vat', 'rate_import', 'price_vnd_flat']) {
      expect(descFirst(key), key).toBe(true)
    }
    for (const key of ['product_name', 'hs_code', 'currency', 'importer_name']) {
      expect(descFirst(key), key).toBeFalsy()
    }
  })
})
