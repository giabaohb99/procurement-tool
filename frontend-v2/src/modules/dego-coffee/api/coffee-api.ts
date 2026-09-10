import { apiGet, apiPatch, apiPost } from '@/core/api'
import type {
  CoffeeLedgerRow,
  CoffeeMember,
  CoffeeMeta,
  CoffeePolicy,
  CoffeeWallet,
  CounterLookupResult,
  MenuItem,
  PosDashboard,
  PosOrderRow,
  PosPartnerHit,
  PosSyncRun,
  ResetPreview,
  SelfOrderResult,
} from '../types/coffee'

/** API `/api/coffee/...` — phong bì đã được `@/core/api` bóc sẵn, trả thẳng data. */
export const coffeeApi = {
  meta: () => apiGet<CoffeeMeta>('/api/coffee/meta'),
  myWallet: () => apiGet<CoffeeWallet>('/api/coffee/my-wallet'),

  policies: () => apiGet<{ items: CoffeePolicy[] }>('/api/coffee/policies'),
  createPolicy: (body: {
    company_id: number
    level_code: number
    monthly_points: number
    effective_from: string
    note: string
  }) => apiPost<{ id: number }>('/api/coffee/policies', body),
  updatePolicy: (
    id: number,
    body: {
      company_id: number
      level_code: number
      monthly_points: number
      effective_from: string
      note: string
    },
  ) => apiPatch<{ id: number }>(`/api/coffee/policies/${id}`, body),

  members: (params?: Record<string, string>) =>
    apiGet<{ total: number; items: CoffeeMember[] }>('/api/coffee/members', { params }),
  createMember: (body: { employee_id: number; level_code: number; note?: string }) =>
    apiPost<CoffeeMember>('/api/coffee/members', body),
  updateMember: (id: number, body: { level_code?: number; status?: number; note?: string }) =>
    apiPatch<CoffeeMember>(`/api/coffee/members/${id}`, body),
  searchPosPartners: (q: string) =>
    apiGet<{ items: PosPartnerHit[] }>('/api/coffee/members/pos-search', { params: { q } }),
  matchMember: (id: number, body: { pos_partner_id: number; pos_partner_code: string }) =>
    apiPost<CoffeeMember>(`/api/coffee/members/${id}/match`, body),
  unmatchMember: (id: number) => apiPost<CoffeeMember>(`/api/coffee/members/${id}/unmatch`, {}),
  createPosPartner: (id: number, body: { name: string; phone: string }) =>
    apiPost<CoffeeMember>(`/api/coffee/members/${id}/create-partner`, body),

  ledger: (params?: Record<string, string>) =>
    apiGet<{ total: number; items: CoffeeLedgerRow[] }>('/api/coffee/ledger', { params }),
  adjust: (body: { employee_id: number; points: number; reason: string }) =>
    apiPost<{ balance: number }>('/api/coffee/ledger/adjust', body),

  counterLookup: (q: string) =>
    apiGet<CounterLookupResult>('/api/coffee/lookup', { params: { q } }),

  posOrders: (params?: Record<string, string>) =>
    apiGet<{ total: number; items: PosOrderRow[] }>('/api/coffee/pos-orders', { params }),
  resolvePosOrder: (id: number, body: { employee_id: number; reason: string }) =>
    apiPost<PosOrderRow>(`/api/coffee/pos-orders/${id}/resolve`, body),

  posDashboard: () => apiGet<PosDashboard>('/api/coffee/pos-dashboard'),

  menu: () => apiGet<{ items: MenuItem[] }>('/api/coffee/menu'),
  selfOrder: (body: { items: { product_id: number; quantity: number }[]; note?: string }) =>
    apiPost<SelfOrderResult>('/api/coffee/self-order', body),

  resetPreview: (period?: string) =>
    apiGet<ResetPreview>('/api/coffee/reset/preview', {
      params: period ? { period } : undefined,
    }),
  resetExecute: (period: string) =>
    apiPost<ResetPreview>('/api/coffee/reset/execute', { period }),

  runSync: (kind: number, period?: string) =>
    apiPost<{ status: string; run_id: number }>('/api/coffee/sync/run', { kind, period }),
  syncRuns: (params?: Record<string, string>) =>
    apiGet<{ total: number; items: PosSyncRun[] }>('/api/coffee/sync/runs', { params }),
}
