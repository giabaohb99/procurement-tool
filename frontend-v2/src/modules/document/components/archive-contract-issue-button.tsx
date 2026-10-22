import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Check } from 'lucide-react'
import { toast } from 'sonner'

import { laborContractApi } from '@/modules/hr/api/labor-contract-api'
import { CONTRACT_STATUS } from '@/modules/hr/utils/labor-contract-rules'
import { queryKeys } from '@/shared/constants/query-keys'
import { Button } from '@/shared/ui/button'
import { confirm } from '@/shared/ui/confirm-dialog'
import { formatDate, toDateInputValue } from '@/shared/utils/format-date'

interface ArchiveContractIssueButtonProps {
  contractId: number
}

/**
 * Nút «Ban hành» DUY NHẤT của bản lưu trữ hợp đồng lao động (duoc-CR-659).
 *
 * Văn bản này không có trạng thái riêng — nó chép trạng thái của HĐ gốc. Vì vậy «Ban hành» = KÝ hợp đồng gốc
 * (Nháp → Đã ký, ngày ký = hôm nay) qua đúng đường `/transition` của phân hệ Nhân sự; đồng bộ sau khi ký đưa văn bản
 * sang «Có hiệu lực». Backend vẫn chặn nếu HĐ còn biến bắt buộc trống, như khi ký ở hồ sơ nhân sự.
 */
export function ArchiveContractIssueButton({ contractId }: ArchiveContractIssueButtonProps) {
  const queryClient = useQueryClient()
  const issue = useMutation({
    mutationFn: (signedDate: string) =>
      laborContractApi.transition(contractId, { to_status: CONTRACT_STATUS.SIGNED, date: signedDate }),
    onSuccess: () => {
      toast.success('Đã ban hành hợp đồng lao động')
      //  Văn bản (trạng thái, quyền, tệp) và danh sách HĐ bên Nhân sự đều đổi theo.
      void queryClient.invalidateQueries({ queryKey: queryKeys.document.all })
      void queryClient.invalidateQueries({ queryKey: queryKeys.hr.all })
    },
  })

  async function handleClick() {
    const today = toDateInputValue(new Date())
    const ok = await confirm({
      title: 'Ban hành hợp đồng lao động?',
      message: `Hợp đồng sẽ chuyển sang «Đã ký» với ngày ký ${formatDate(today)}, văn bản chuyển sang «Có hiệu lực». Sau khi ban hành không quay lại nháp được.`,
      confirmLabel: 'Ban hành',
      tone: 'default',
    })
    if (ok) issue.mutate(today)
  }

  return (
    <Button type="button" onClick={() => void handleClick()} disabled={issue.isPending}>
      <Check className="size-4" />
      Ban hành
    </Button>
  )
}
