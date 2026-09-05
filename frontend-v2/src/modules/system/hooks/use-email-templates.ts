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
