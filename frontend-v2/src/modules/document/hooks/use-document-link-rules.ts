import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { documentLinkRuleApi } from '../api/document-link-rule-api'
import type { DocTypeLinkRule, DocTypeLinkRuleInput } from '../types/document-link-rule'

/** Quy tắc quan hệ theo LOẠI văn bản — danh mục nền, khai một lần (E01). */

/**
 * Bỏ trống = cả bảng; truyền id = chỉ quy tắc của MỘT loại văn bản.
 *
 * `enabled: false` cho trang đang TẠO loại mới: chưa có loại thì không có quy
 * tắc nào để đọc, mà bỏ trống tham số lại thành "nạp cả bảng" — đúng cú gọi
 * thừa mà người dùng phải chờ.
 */
export function useDocumentLinkRules(sourceTypeId?: number, enabled = true) {
  return useQuery({
    queryKey: queryKeys.document.linkRules(sourceTypeId),
    queryFn: () => documentLinkRuleApi.list(sourceTypeId),
    enabled,
  })
}

export function useDocumentLinkRule(id?: number) {
  return useQuery({
    queryKey: queryKeys.document.linkRule(id ?? 0),
    queryFn: () => documentLinkRuleApi.getById(id as number),
    enabled: typeof id === 'number' && id > 0,
  })
}

export function useLinkRuleOptions() {
  return useQuery({
    queryKey: queryKeys.document.linkRuleOptions(),
    queryFn: () => documentLinkRuleApi.options(),
    //  Nhãn của mười loại quan hệ không đổi trong một phiên làm việc.
    staleTime: Infinity,
  })
}

/**
 * Lưu quy tắc quan hệ — **một lần khai ra được nhiều dòng**.
 *
 * Quan hệ giữa các loại là một–nhiều: khai "Quy trình căn cứ theo Chính sách,
 * Quy chế, Quyết định" là ba dòng, người dùng chỉ mở form một lần. Sửa thì luôn
 * đúng một dòng (`id`) — dòng đã tồn tại không nhân bản ra được.
 *
 * Trả về `{ saved, failed }` thay vì ném lỗi: chèn năm dòng mà dòng thứ ba trùng
 * với một dòng đã có thì bốn dòng kia **đã ghi rồi**. Ném lỗi ở đây là bảo màn
 * hình rằng cả mẻ hỏng, người dùng khai lại và lần này trùng cả bốn.
 */
export function useSaveDocumentLinkRules() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async ({ id, rows }: { id?: number; rows: DocTypeLinkRuleInput[] }) => {
      if (id) {
        return { saved: [await documentLinkRuleApi.update(id, rows[0])], failed: [] as string[] }
      }

      //  Tuần tự chứ không song song: backend chặn trùng bằng UNIQUE, bắn cùng
      //  lúc thì câu báo lỗi không biết là của dòng nào.
      const saved: DocTypeLinkRule[] = []
      const failed: string[] = []
      for (const row of rows) {
        try {
          saved.push(await documentLinkRuleApi.create(row))
        } catch (error) {
          failed.push(extractErrorMessage(error))
        }
      }
      return { saved, failed }
    },

    onSuccess: ({ saved, failed }) => {
      if (saved.length > 1) toast.success(`Đã lưu ${saved.length} quan hệ`)
      else if (saved.length === 1) toast.success('Đã lưu quy tắc quan hệ')

      for (const message of failed) toast.error(message)

      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRulesAll })
      for (const rule of saved) {
        void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRule(rule.id) })
      }
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

/**
 * Xếp lại THỨ TỰ tiên quyết — nhận cả danh sách theo thứ tự MỚI.
 *
 * Chỉ gửi những dòng thật sự đổi chỗ: đẩy một dòng lên trên trong danh sách 8
 * dòng là hai lời gọi, không phải tám. Thứ tự đánh lại từ 1 nên không bao giờ
 * đụng số 0 ("chưa xếp") của dữ liệu cũ.
 */
export function useReorderDocumentLinkRules() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (rows: { id: number; values: DocTypeLinkRuleInput }[]) => {
      for (const [index, row] of rows.entries()) {
        const sortOrder = index + 1
        if (row.values.sort_order === sortOrder) continue
        await documentLinkRuleApi.update(row.id, { ...row.values, sort_order: sortOrder })
      }
    },
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRulesAll })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}

export function useDeleteDocumentLinkRule() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (id: number) => documentLinkRuleApi.remove(id),
    onSuccess: () => {
      toast.success('Đã xóa quy tắc quan hệ')
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.linkRulesAll })
    },
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
