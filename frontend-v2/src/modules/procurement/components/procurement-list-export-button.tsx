import { Download } from 'lucide-react'

import { Button } from '@/shared/ui/button'

interface ProcurementListExportButtonProps {
  /** Số phiếu đang tick — 0 thì xuất theo bộ lọc đang đặt. */
  selectedCount: number
  onExport: () => void
  className?: string
}

/**
 * Nút *Xuất Excel* của danh sách Thu mua — chữ và gợi ý đúng bản v1 (`CrudList.tsx`,
 * duoc-CR-741): có tick thì thành *Xuất Excel (n)* và chỉ xuất đúng n phiếu đó.
 */
export function ProcurementListExportButton({
  selectedCount,
  onExport,
  className,
}: ProcurementListExportButtonProps) {
  return (
    <Button
      type="button"
      variant="outline"
      className={className}
      title={
        selectedCount > 0
          ? `Xuất ${selectedCount} phiếu đã chọn ra Excel`
          : 'Xuất toàn bộ kết quả đang lọc ra Excel'
      }
      onClick={onExport}
    >
      <Download className="mr-1.5 size-4" />
      Xuất Excel{selectedCount > 0 ? ` (${selectedCount})` : ''}
    </Button>
  )
}
