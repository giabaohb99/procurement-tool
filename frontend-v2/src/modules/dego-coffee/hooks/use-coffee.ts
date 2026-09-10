import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { coffeeApi } from '../api/coffee-api'

export function useCoffeeMeta() {
  return useQuery({
    queryKey: queryKeys.coffee.meta(),
    queryFn: () => coffeeApi.meta(),
    //  Nhãn enum sinh từ backend, không đổi trong một phiên làm việc.
    staleTime: Infinity,
  })
}

export function useMyWallet() {
  return useQuery({
    queryKey: queryKeys.coffee.myWallet(),
    queryFn: () => coffeeApi.myWallet(),
    refetchOnWindowFocus: true,
  })
}

export function useCoffeePolicies() {
  return useQuery({
    queryKey: queryKeys.coffee.policies(),
    queryFn: () => coffeeApi.policies(),
  })
}

export function useCoffeeMembers(params?: Record<string, string>) {
  return useQuery({
    queryKey: queryKeys.coffee.members(params),
    queryFn: () => coffeeApi.members(params),
  })
}

export function useCoffeeLedger(params?: Record<string, string>) {
  return useQuery({
    queryKey: queryKeys.coffee.ledger(params),
    queryFn: () => coffeeApi.ledger(params),
  })
}

export function usePosOrders(params?: Record<string, string>) {
  return useQuery({
    queryKey: queryKeys.coffee.posOrders(params),
    queryFn: () => coffeeApi.posOrders(params),
  })
}

export function useCoffeeMenu() {
  return useQuery({
    queryKey: queryKeys.coffee.menu(),
    queryFn: () => coffeeApi.menu(),
    //  Thực đơn quán đổi theo ngày chứ không theo phút.
    staleTime: 5 * 60_000,
    retry: false,
  })
}

export function useSelfOrder() {
  return useCoffeeMutation(coffeeApi.selfOrder, '')
}

export function useResetPreview(period?: string, enabled = true) {
  return useQuery({
    queryKey: queryKeys.coffee.resetPreview(period),
    queryFn: () => coffeeApi.resetPreview(period),
    enabled,
    retry: false,
  })
}

export function useResetExecute() {
  return useCoffeeMutation((period: string) => coffeeApi.resetExecute(period), '')
}

export function usePosDashboard() {
  return useQuery({
    queryKey: queryKeys.coffee.posDashboard(),
    queryFn: () => coffeeApi.posDashboard(),
    //  Đọc thẳng từ POS365 — quay lại tab thì hỏi lại, nhưng đừng dồn dập.
    refetchOnWindowFocus: true,
    staleTime: 60_000,
    retry: false,
  })
}

export function useSyncRuns() {
  return useQuery({
    queryKey: queryKeys.coffee.syncRuns(),
    queryFn: () => coffeeApi.syncRuns({ limit: '50' }),
  })
}

/** Mutation chung: toast lỗi từ phong bì + nạp lại cả cụm coffee (sổ/thành viên/đơn). */
function useCoffeeMutation<TArgs, TData>(
  fn: (args: TArgs) => Promise<TData>,
  successMessage: string,
) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: fn,
    onSuccess: () => {
      if (successMessage) toast.success(successMessage)
      void queryClient.invalidateQueries({ queryKey: queryKeys.coffee.all })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useCreatePolicy() {
  return useCoffeeMutation(coffeeApi.createPolicy, 'Đã thêm dòng chính sách')
}

export function useUpdatePolicy() {
  return useCoffeeMutation(
    (args: {
      id: number
      body: {
        company_id: number
        level_code: number
        monthly_points: number
        effective_from: string
        note: string
      }
    }) => coffeeApi.updatePolicy(args.id, args.body),
    'Đã cập nhật dòng chính sách',
  )
}

export function useCreateMember() {
  return useCoffeeMutation(coffeeApi.createMember, 'Đã thêm thành viên')
}

export function useUpdateMember() {
  return useCoffeeMutation(
    (args: { id: number; body: { level_code?: number; status?: number; note?: string } }) =>
      coffeeApi.updateMember(args.id, args.body),
    'Đã cập nhật thành viên',
  )
}

export function useMatchMember() {
  return useCoffeeMutation(
    (args: { id: number; pos_partner_id: number; pos_partner_code: string }) =>
      coffeeApi.matchMember(args.id, {
        pos_partner_id: args.pos_partner_id,
        pos_partner_code: args.pos_partner_code,
      }),
    'Đã ghép khách POS365',
  )
}

export function useUnmatchMember() {
  return useCoffeeMutation((id: number) => coffeeApi.unmatchMember(id), 'Đã gỡ ghép')
}

export function useCreatePosPartner() {
  return useCoffeeMutation(
    (args: { id: number; name: string; phone: string }) =>
      coffeeApi.createPosPartner(args.id, { name: args.name, phone: args.phone }),
    'Đã tạo khách POS365 và ghép',
  )
}

export function useAdjustLedger() {
  return useCoffeeMutation(coffeeApi.adjust, 'Đã ghi dòng điều chỉnh')
}

export function useResolvePosOrder() {
  return useCoffeeMutation(
    (args: { id: number; employee_id: number; reason: string }) =>
      coffeeApi.resolvePosOrder(args.id, { employee_id: args.employee_id, reason: args.reason }),
    'Đã xử lý đơn',
  )
}

export function useRunSync() {
  return useCoffeeMutation(
    (args: { kind: number; period?: string }) => coffeeApi.runSync(args.kind, args.period),
    'Đã chạy đồng bộ — xem kết quả ở Nhật ký',
  )
}
