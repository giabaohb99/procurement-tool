import { Copy, Loader2 } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { useCopyDocument } from '../hooks/use-documents'

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
