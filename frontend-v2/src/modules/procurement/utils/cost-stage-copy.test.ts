import { describe, expect, it } from 'vitest'

import type { PurchaseOrderImportCost } from '../types/purchase-order-detail'
import { copyCostStageAmounts } from './cost-stage-copy'

const row = (patch: Partial<PurchaseOrderImportCost>): PurchaseOrderImportCost =>
  ({ id: 1, estimate_amount: null, provisional_amount: null, final_amount: null, ...patch }) as PurchaseOrderImportCost

const always = () => true

describe('copyCostStageAmounts — nút chép số hàng loạt (bao-CR-478)', () => {
  it('chép Dự toán sang Tạm tính còn trống, kèm tỷ giá', () => {
    const { costs, copied } = copyCostStageAmounts(
      [row({ estimate_amount: 850, estimate_rate: 25_000 })],
      'estimate',
      'provisional',
      always,
    )
    expect(copied).toBe(1)
    expect(costs[0].provisional_amount).toBe(850)
    expect(costs[0].provisional_rate).toBe(25_000)
  })

  it('KHÔNG đè số đã gõ ở cột đích', () => {
    const { costs, copied } = copyCostStageAmounts(
      [row({ provisional_amount: 1_200, final_amount: 999 })],
      'provisional',
      'final',
      always,
    )
    expect(copied).toBe(0)
    expect(costs[0].final_amount).toBe(999)
  })

  it('ô đích bằng 0 (bản cũ lưu ô trống thành 0) vẫn được chép', () => {
    const { costs } = copyCostStageAmounts(
      [row({ provisional_amount: 1_200, final_amount: 0 })],
      'provisional',
      'final',
      always,
    )
    expect(costs[0].final_amount).toBe(1_200)
  })

  it('ô nguồn trống hoặc 0 thì bỏ qua, không chép số 0 sang', () => {
    const { copied } = copyCostStageAmounts(
      [row({ estimate_amount: null }), row({ id: 2, estimate_amount: 0 })],
      'estimate',
      'provisional',
      always,
    )
    expect(copied).toBe(0)
  })

  it('dòng đã khóa (đã quyết toán) không bị đụng', () => {
    const locked = row({ estimate_amount: 500 })
    const { costs, copied } = copyCostStageAmounts([locked], 'estimate', 'provisional', () => false)
    expect(copied).toBe(0)
    expect(costs[0]).toBe(locked)
  })

  it('có tick thì chỉ chép dòng đã tick; dòng mới chưa lưu (chưa có id) không tính là đã tick', () => {
    const { costs, copied } = copyCostStageAmounts(
      [row({ id: 1, estimate_amount: 100 }), row({ id: 2, estimate_amount: 200 }), row({ id: undefined, estimate_amount: 300 })],
      'estimate',
      'provisional',
      always,
      new Set([2]),
    )
    expect(copied).toBe(1)
    expect(costs.map((c) => c.provisional_amount)).toEqual([null, 200, null])
  })

  it('bộ tick rỗng nghĩa là chép mọi dòng', () => {
    const { copied } = copyCostStageAmounts(
      [row({ estimate_amount: 100 }), row({ id: 2, estimate_amount: 200 })],
      'estimate',
      'provisional',
      always,
      new Set(),
    )
    expect(copied).toBe(2)
  })
})
