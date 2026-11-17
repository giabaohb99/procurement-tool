import { describe, expect, it } from 'vitest'

import type { PrintSignatureCell } from '../types/purchase-request-detail'
import type { PurchasingPrintData } from '../types/purchasing-print'
import {
  buildPurchasingGeneralInfo,
  buildPurchasingSignatureSource,
  buildPurchasingSupplier,
  buildRequestGeneralInfo,
} from './purchasing-print-sheet'
import {
  resolvePrintSignatureCells,
  type PrintSignatureSource,
} from './purchase-request-signature-cells'
import { resolvePrintTemplate } from './purchase-request-print-template'

type People = Pick<PurchasingPrintData, 'proposer' | 'manager'>

function makePeople(overrides: Partial<People> = {}): People {
  return {
    proposer: {
      employee_id: 7,
      name: 'Nguyen Thu Mua',
      position: 'Nhân viên thu mua',
      department: 'Phòng Thu mua',
      signature: 'https://cdn/ky-thu-mua.png',
    },
    manager: {
      employee_id: 8,
      name: 'Tran Quan Ly',
      position: 'Trưởng phòng',
      signature: 'https://cdn/ky-quan-ly.png',
    },
    ...overrides,
  }
}

const noManager = { employee_id: 0, name: '', position: '', signature: '' }

const fourCells: PrintSignatureCell[] = [
  { key: 'director', role: 'Giám đốc', name: 'Le Giam Doc', signature: 'https://cdn/ky-gd.png' },
  { key: 'purchasing_head', role: 'TP/BP mua hàng', name: 'Pham Mua Hang', signature: 'https://cdn/ky-mh.png' },
  { key: 'proposer', role: 'TP/BP đề xuất', name: 'Le Phuoc Huu', signature: 'https://cdn/ky-huu.png' },
  { key: 'preparer', role: 'Người lập', name: 'Nguoi Lap YCMH', signature: 'https://cdn/ky-lap.png' },
]

function makeSource(cells?: PrintSignatureCell[]): PrintSignatureSource {
  return {
    requester: 'Nguoi Lap YCMH',
    requester_signature: 'https://cdn/ky-lap.png',
    approver_name: 'Le Phuoc Huu',
    approver_signature: 'https://cdn/ky-huu.png',
    purchasing_head_name: 'Pham Mua Hang',
    purchasing_head_signature: 'https://cdn/ky-mh.png',
    print_signature_cells: cells,
  }
}

function cellsFor(source: PrintSignatureSource, template: string) {
  return resolvePrintSignatureCells(source, resolvePrintTemplate(template))
}

describe('general info (duoc-CR-777)', () => {
  it('purchasing template shows the person printing and their direct manager', () => {
    expect(buildPurchasingGeneralInfo(makePeople())).toEqual({
      requester: 'Nguyen Thu Mua',
      position: 'Nhân viên thu mua',
      department: 'Phòng Thu mua',
      headOfDept: 'Tran Quan Ly',
    })
  })

  it('missing position / department / manager print the same dots as the normal template', () => {
    const info = buildPurchasingGeneralInfo(
      makePeople({
        proposer: { employee_id: 0, name: 'admin', position: '', department: '', signature: '' },
        manager: noManager,
      }),
    )
    const normal = buildRequestGeneralInfo({
      requester: 'admin',
      requester_position: '',
      department: '',
      head_of_dept: '',
    })
    expect(info).toEqual(normal)
  })
})

describe('buildPurchasingSupplier (duoc-CR-777)', () => {
  const requestSupplier = { name: 'NCC Phieu', tax_code: '0301', contact: '0909' }

  it('prints the order supplier without tax code / contact when it differs from the request', () => {
    expect(
      buildPurchasingSupplier({ supplier: { code: 'S2', name: 'NCC Don' }, supplier_hidden: false }, requestSupplier),
    ).toEqual({ name: 'NCC Don', tax_code: '', contact: '' })
  })

  it('keeps tax code and contact when the order supplier is the one on the request', () => {
    expect(
      buildPurchasingSupplier({ supplier: { code: 'S1', name: 'NCC Phieu' }, supplier_hidden: false }, requestSupplier),
    ).toEqual(requestSupplier)
  })

  it('hidden supplier prints an empty cluster, never the request supplier or a stray name', () => {
    //  Máy chủ đã che, nhưng giả sử bản cũ vẫn lỡ gửi tên — cờ `supplier_hidden` phải thắng.
    for (const supplier of [
      { code: '', name: '' },
      { code: 'S1', name: 'NCC Phieu' },
    ]) {
      expect(buildPurchasingSupplier({ supplier, supplier_hidden: true }, requestSupplier)).toEqual({
        name: '',
        tax_code: '',
        contact: '',
      })
    }
  })

  it('an order without a supplier also prints an empty cluster, even if the request is empty too', () => {
    const empty = { name: '', tax_code: '', contact: '' }
    expect(buildPurchasingSupplier({ supplier: { code: '', name: '' }, supplier_hidden: false }, requestSupplier)).toEqual(empty)
    expect(
      buildPurchasingSupplier({ supplier: { code: '', name: '' }, supplier_hidden: false }, { ...empty, tax_code: 'X' }),
    ).toEqual(empty)
  })
})

describe('buildPurchasingSignatureSource (duoc-CR-777)', () => {
  it('signed: preparer = person printing, proposer = manager, other two cells untouched', () => {
    const cells = cellsFor(buildPurchasingSignatureSource(makeSource(fourCells), makePeople()), 'purchasing-signed')
    expect(cells).toEqual([
      fourCells[0],
      fourCells[1],
      { key: 'proposer', role: 'TP/BP đề xuất', name: 'Tran Quan Ly', signature: 'https://cdn/ky-quan-ly.png' },
      { key: 'preparer', role: 'Người lập', name: 'Nguyen Thu Mua', signature: 'https://cdn/ky-thu-mua.png' },
    ])
  })

  it('unsigned blanks every cell exactly like the normal unsigned template', () => {
    const cells = cellsFor(buildPurchasingSignatureSource(makeSource(fourCells), makePeople()), 'purchasing-unsigned')
    expect(cells).toEqual(cellsFor(makeSource(fourCells), 'normal-unsigned'))
    expect(cells.every((cell) => !cell.name && !cell.signature)).toBe(true)
  })

  it('no direct manager leaves "TP/BP đề xuất" empty instead of keeping the request approver', () => {
    const cells = cellsFor(
      buildPurchasingSignatureSource(makeSource(fourCells), makePeople({ manager: noManager })),
      'purchasing-signed',
    )
    expect(cells.find((cell) => cell.key === 'proposer')).toMatchObject({ name: '', signature: '' })
  })

  it('household cell set keeps "Chủ hộ" as the backend sent it', () => {
    const household = [{ ...fourCells[0], key: 'household_owner', role: 'Chủ hộ' }, ...fourCells.slice(1)]
    const cells = cellsFor(buildPurchasingSignatureSource(makeSource(household), makePeople()), 'purchasing-signed')
    expect(cells[0]).toEqual(household[0])
    expect(cells.map((cell) => cell.role)).toEqual(['Chủ hộ', 'TP/BP mua hàng', 'TP/BP đề xuất', 'Người lập'])
  })

  it('works on the legacy path when the backend sends no cell list (undefined or empty)', () => {
    for (const cells of [undefined, []]) {
      const resolved = cellsFor(buildPurchasingSignatureSource(makeSource(cells), makePeople()), 'purchasing-signed')
      expect(resolved.find((cell) => cell.key === 'preparer')?.name).toBe('Nguyen Thu Mua')
      expect(resolved.find((cell) => cell.key === 'proposer')?.name).toBe('Tran Quan Ly')
      expect(resolved.find((cell) => cell.key === 'purchasing_head')?.name).toBe('Pham Mua Hang')
    }
  })

  it('does not mutate the request data it was given', () => {
    const source = makeSource(fourCells.map((cell) => ({ ...cell })))
    const snapshot = JSON.parse(JSON.stringify(source))
    buildPurchasingSignatureSource(source, makePeople())
    expect(source).toEqual(snapshot)
  })
})
