import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'

import { queryKeys } from '@/shared/constants/query-keys'

import { emailTemplateApi } from '../api/email-template-api'
import type { EmailTemplate } from '../types/email-template'

/** Danh sách mẫu email theo bước (đã gộp mặc định + bản đã sửa). */
export function useEmailTemplates() {
  return useQuery({
    queryKey: queryKeys.system.emailTemplates(),
    queryFn: () => emailTemplateApi.list(),
    staleTime: Infinity,
  })
}

/** Một mẫu email theo `event` — cho trang con sửa nội dung. */
export function useEmailTemplate(event: string) {
  return useQuery({
    queryKey: [...queryKeys.system.emailTemplates(), event],
    queryFn: () => emailTemplateApi.get(event),
    enabled: Boolean(event),
  })
}

/**
 * Bản RENDER thử của một mẫu email, dựng từ nội dung ĐANG SOẠN + dữ liệu mẫu.
 *
 * ⚠️ **Phải hỏi backend, không render được ở đây.** Thân mẫu đầy ô `{{ code }}`,
 * `{{ recipient_name }}`… mà bộ dữ liệu mẫu để thay vào chúng do backend giữ
 * (`/api/email-templates/:event/preview`). Tự ghép ở frontend thì bản xem trước
 * đầy dấu ngoặc nhọn — đúng thứ người soạn đang cần thấy đã thay xong.
 *
 * ⚠️ Khóa cache có CẢ `subject` lẫn `body` (bản đã hoãn nhịp): thiếu chúng thì
 * TanStack coi mọi lần soạn là cùng một truy vấn và trả bản cũ trong cache —
 * gõ xong thấy bản render của lần trước, im lặng.
 *
 * `enabled` chặn lượt gọi khi thân còn rỗng (lúc form chưa seed xong).
 */
export function useEmailTemplatePreview(event: string, subject: string, bodyHtml: string) {
  return useQuery({
    queryKey: [...queryKeys.system.emailTemplates(), event, 'preview', subject, bodyHtml],
    queryFn: () => emailTemplateApi.preview(event, { subject, body_html: bodyHtml }),
    enabled: Boolean(event) && Boolean(bodyHtml),
    //  Giữ bản render cũ trong lúc gọi bản mới: bỏ đi thì mỗi nhịp gõ khung xem
    //  trước chớp trắng một cái, nhìn như trang bị giật.
    placeholderData: (prev) => prev,
    staleTime: Infinity,
    retry: false,
  })
}

export function useSaveEmailTemplate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (input: {
      event: string
      enabled: boolean
      subject: string
      body_html: string
    }) => emailTemplateApi.update(input.event, input),
    onSuccess: (updated: EmailTemplate) => {
      // Backend trả lại bản có hiệu lực — vá thẳng vào cache danh sách.
      queryClient.setQueryData<EmailTemplate[]>(queryKeys.system.emailTemplates(), (prev) =>
        prev ? prev.map((t) => (t.event === updated.event ? updated : t)) : prev,
      )
    },
  })
}

export function useResetEmailTemplate() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: (event: string) => emailTemplateApi.reset(event),
    onSuccess: (updated: EmailTemplate) => {
      queryClient.setQueryData<EmailTemplate[]>(queryKeys.system.emailTemplates(), (prev) =>
        prev ? prev.map((t) => (t.event === updated.event ? updated : t)) : prev,
      )
    },
  })
}
