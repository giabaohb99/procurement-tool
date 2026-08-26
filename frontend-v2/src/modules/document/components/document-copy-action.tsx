import { Copy, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { cn } from '@/shared/utils/cn'
import { useCopyDocument } from '../hooks/use-documents'

/**
 * Nút trên DÒNG BẢNG phải cao **24px**, không phải 32px của `icon-sm`.
 *
 * Ô của `DataTable` là `min-h-9` + `py-1.5`, nên chỗ trống cho nội dung đúng
 * 23px: nhét một nút 32px vào là **cả bảng cao thêm 9px mỗi dòng** — đó là lý do
 * bảng «Văn bản đi» trông thưa hơn hẳn «Văn bản đến» dù hai bảng cùng một khung.
 * Vùng bấm 24px vẫn thoải mái vì cả ô là vùng chờ chuột.
 */
const ROW_ACTIONS = 'size-6 -my-px'

interface DocumentCopyActionProps {
  documentId: number
  canCreate: boolean
  placement?: 'header' | 'row'
}

/** Tạo ngay một bản nháp độc lập giống văn bản nguồn, dùng để dựng dữ liệu thử. */
export function DocumentCopyAction({
  documentId,
  canCreate,
  placement = 'header',
}: DocumentCopyActionProps) {
  const navigate = useNavigate()
  const copyDocument = useCopyDocument()

  if (!canCreate) return null

  return (
    <Button
      type="button"
      variant="outline"
      size={placement === 'row' ? 'icon-sm' : 'default'}
      className={cn(placement === 'row' && ROW_ACTIONS)}
      aria-label={placement === 'row' ? 'Sao chép' : undefined}
      disabled={copyDocument.isPending}
      title="Tạo một văn bản nháp mới giống bản ghi này"
      onClick={(event) => {
        // Dòng bảng tự mở trang chi tiết; nút sao chép phải giữ người dùng ở
        // đúng thao tác này cho tới khi API trả bản ghi mới.
        event.stopPropagation()
        copyDocument.mutate(documentId, {
          onSuccess: (copied) => navigate(appRoutes.document.documentDetail(copied.id)),
        })
      }}
    >
      {copyDocument.isPending ? (
        <Loader2 className="size-4 animate-spin" />
      ) : (
        <Copy className="size-4" />
      )}
      {placement === 'header' && 'Sao chép'}
    </Button>
  )
}
