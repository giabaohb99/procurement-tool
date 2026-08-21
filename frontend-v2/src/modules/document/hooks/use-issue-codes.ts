import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { toast } from 'sonner'

import { extractErrorMessage } from '@/core/api'
import { queryKeys } from '@/shared/constants/query-keys'
import { issueCodeApi } from '../api/issue-code-api'
import type { IssueCodeUpdateInput } from '../types/issue-code'

/** Mọi mã đang đi vào số hiệu, gom theo bốn thẻ của mẫu. */
export function useIssueCodes(enabled = true) {
  return useQuery({
    queryKey: queryKeys.document.issueCodes(),
    queryFn: () => issueCodeApi.list(),
    //  Chỉ nạp khi hộp thoại mở: đây là danh sách 60+ dòng gom từ năm bảng,
    //  không phải thứ cần sẵn ở mọi lần mở trang Quy tắc đánh số.
    enabled,
  })
}

export function useSaveIssueCode() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (payload: IssueCodeUpdateInput) => issueCodeApi.update(payload),
    onSuccess: () => {
      toast.success('Đã lưu mã')
      //  Nạp lại CẢ nhóm mã lẫn danh mục gốc: mã vừa đổi hiện cả ở màn Phòng
      //  ban / Pháp nhân / Thiết lập văn bản, để nguyên là hai chỗ nói khác nhau.
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.issueCodes() })
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
    //  Backend nói rõ vì sao chặn (mã có dấu, đã cấp số, trùng mã loại) — hiện
    //  nguyên văn, đừng thay bằng câu chung chung.
    onError: (error) => toast.error(extractErrorMessage(error)),
  })
}
