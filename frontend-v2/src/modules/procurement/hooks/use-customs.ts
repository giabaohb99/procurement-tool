// bao-CR-470 — hook TanStack Query của màn Tra cứu giá hải quan.
//
// Khóa truy vấn khai TẠI CHỖ (`customsKeys`) chứ không ở `shared/constants/query-keys.ts`:
// mọi lượt bỏ hiệu lực của phân hệ này đều nằm trong chính tệp này (`useInvalidateCustoms`),
// không nơi nào khác cần với tới. Khóa vẫn mở đầu bằng `'procurement'` nên lệnh bỏ hiệu lực
// cả phân hệ Thu mua (`queryKeys.procurement.all`) vẫn quét được chúng.
import { useMutation, useQueries, useQuery, useQueryClient } from '@tanstack/react-query'
import { useCallback } from 'react'

import { canManageEntity } from '@/app/router/module-visibility'
import { usePermission } from '@/core/authorization/use-permission'

import {
  commitCustomsBatch,
  fetchCustomsAlerts,
  fetchCustomsBatch,
  fetchCustomsBatches,
  fetchCustomsBatchLogs,
  fetchCustomsCompare,
  fetchCustomsCoverage,
  fetchCustomsImporters,
  fetchCustomsLine,
  fetchCustomsLines,
  fetchCustomsOptions,
  fetchCustomsStats,
  lookupCustomsRegulations,
  lookupCustomsTariff,
  revertCustomsBatch,
  uploadCustomsFiles,
} from '../api/customs-api'
import type { CustomsImportBatch } from '../types/customs'
import { isBatchRunning } from '../utils/customs'

type Params = Record<string, unknown>

const customsKeys = {
  all: ['procurement', 'customs'] as const,
  coverage: () => ['procurement', 'customs', 'coverage'] as const,
  options: () => ['procurement', 'customs', 'options'] as const,
  lines: (params: Params) => ['procurement', 'customs', 'lines', params] as const,
  line: (id: number) => ['procurement', 'customs', 'line', id] as const,
  stats: (params: Params) => ['procurement', 'customs', 'stats', params] as const,
  compare: (params: Params) => ['procurement', 'customs', 'compare', params] as const,
  importers: (params: Params) => ['procurement', 'customs', 'importers', params] as const,
  alerts: (params: Params) => ['procurement', 'customs', 'alerts', params] as const,
  regulationLookup: (q: string) => ['procurement', 'customs', 'regulation-lookup', q] as const,
  tariff: (hsCode: string) => ['procurement', 'customs', 'tariff', hsCode] as const,
  batches: (params: Params) => ['procurement', 'customs', 'batches', params] as const,
  batch: (id: number) => ['procurement', 'customs', 'batch', id] as const,
  batchLogs: (id: number, params: Params) =>
    ['procurement', 'customs', 'batch', id, 'logs', params] as const,
}

/** Nhịp hỏi lại trạng thái lô đang chạy — khớp bản v1 (1,5 giây). */
const BATCH_POLL_MS = 1500

export function useCustomsCoverage() {
  return useQuery({ queryKey: customsKeys.coverage(), queryFn: fetchCustomsCoverage })
}

export function useCustomsOptions() {
  return useQuery({
    queryKey: customsKeys.options(),
    queryFn: fetchCustomsOptions,
    // Danh sách giá trị ô lọc chỉ đổi khi nạp tệp mới — nạp xong đã bỏ hiệu lực cả nhánh.
    staleTime: 5 * 60 * 1000,
  })
}

/** `enabled = false` khi thẻ Danh sách không mở — đổi bộ lọc ở thẻ khác không gọi thừa. */
export function useCustomsLines(params: Params, enabled = true) {
  return useQuery({
    queryKey: customsKeys.lines(params),
    queryFn: () => fetchCustomsLines(params),
    enabled,
    placeholderData: (previous) => previous,
  })
}

export function useCustomsLine(id: number | null) {
  return useQuery({
    queryKey: customsKeys.line(id ?? 0),
    queryFn: () => fetchCustomsLine(id ?? 0),
    enabled: id !== null,
  })
}

export function useCustomsStats(params: Params, enabled: boolean) {
  return useQuery({
    queryKey: customsKeys.stats(params),
    queryFn: () => fetchCustomsStats(params),
    enabled,
    placeholderData: (previous) => previous,
  })
}

/** `params = null` = người dùng chưa bấm So sánh, chưa gọi gì. */
export function useCustomsCompare(params: Params | null) {
  return useQuery({
    queryKey: customsKeys.compare(params ?? {}),
    queryFn: () => fetchCustomsCompare(params ?? {}),
    enabled: params !== null,
  })
}

export function useCustomsImporters(params: Params, enabled: boolean) {
  return useQuery({
    queryKey: customsKeys.importers(params),
    queryFn: () => fetchCustomsImporters(params),
    enabled,
    placeholderData: (previous) => previous,
  })
}

/** Cảnh báo pháp lý theo từ khóa — backend chỉ so khi từ khóa từ 3 ký tự. */
export function useCustomsAlerts(params: Params, enabled: boolean) {
  return useQuery({
    queryKey: customsKeys.alerts(params),
    queryFn: () => fetchCustomsAlerts(params),
    enabled,
  })
}

/** `term = ''` = chưa tra. */
export function useCustomsRegulationLookup(term: string) {
  return useQuery({
    queryKey: customsKeys.regulationLookup(term),
    queryFn: () => lookupCustomsRegulations(term),
    enabled: term !== '',
  })
}

/** `hsCode = ''` = chưa tra. */
export function useCustomsTariff(hsCode: string) {
  return useQuery({
    queryKey: customsKeys.tariff(hsCode),
    queryFn: () => lookupCustomsTariff(hsCode),
    enabled: hsCode !== '',
  })
}

export function useCustomsBatches(params: Params) {
  return useQuery({
    queryKey: customsKeys.batches(params),
    queryFn: () => fetchCustomsBatches(params),
    placeholderData: (previous) => previous,
  })
}

export function useCustomsBatchLogs(id: number | null, params: Params) {
  return useQuery({
    queryKey: customsKeys.batchLogs(id ?? 0, params),
    queryFn: () => fetchCustomsBatchLogs(id ?? 0, params),
    enabled: id !== null,
    placeholderData: (previous) => previous,
  })
}

/**
 * Trạng thái MỚI NHẤT của một nhóm lô vừa tạo: lô nào còn chờ / đang chạy thì hỏi lại
 * mỗi 1,5 giây, xong rồi thì thôi. Trả về đúng thứ tự đầu vào; lô chưa hỏi lại được thì
 * giữ bản đang cầm.
 */
export function useCustomsBatchPolling(batches: CustomsImportBatch[]): CustomsImportBatch[] {
  return useQueries({
    queries: batches.map((batch) => ({
      queryKey: customsKeys.batch(batch.id),
      queryFn: () => fetchCustomsBatch(batch.id),
      initialData: batch,
      // `initialData` coi là tươi mãi — chỉ nhịp hỏi lại bên dưới mới kéo trạng thái mới.
      staleTime: Infinity,
      refetchInterval: (query: { state: { data?: CustomsImportBatch } }) =>
        query.state.data && isBatchRunning(query.state.data) ? BATCH_POLL_MS : false,
    })),
    combine: (results) => results.map((result, index) => result.data ?? batches[index]),
  })
}

/** Bỏ hiệu lực mọi truy vấn của màn — dùng sau khi nạp / hoàn tác. */
export function useInvalidateCustoms() {
  const queryClient = useQueryClient()
  return useCallback(
    () => queryClient.invalidateQueries({ queryKey: customsKeys.all }),
    [queryClient],
  )
}

export function useUploadCustomsFiles() {
  return useMutation({ mutationFn: uploadCustomsFiles })
}

export function useCommitCustomsBatch() {
  return useMutation({ mutationFn: commitCustomsBatch })
}

export function useRevertCustomsBatch() {
  const invalidate = useInvalidateCustoms()
  return useMutation({
    mutationFn: revertCustomsBatch,
    onSuccess: () => invalidate(),
  })
}

/** Quyền trên màn — gom một chỗ cho các thành phần con khỏi gọi `can` rải rác. */
export function useCustomsPermissions() {
  const { can } = usePermission()
  return {
    canImport: can('customs_price', 'write'),
    canRevert: can('customs_price', 'delete'),
    canExport: can('customs_price', 'export'),
    canReadRegulations: can('customs_regulation', 'read'),
    //  bao-CR-501 — thẻ «Cấu hình» (từ khóa nhãn + từ đồng nghĩa): cùng luật hiện mục
    //  `manage: true` trên menu trước đây — có một trong ba quyền tạo / sửa / xóa.
    canConfigure: canManageEntity('customs_price', can),
  }
}
