import { Download } from 'lucide-react'
import { useSearchParams } from 'react-router-dom'

import { downloadFile } from '@/core/api'
import { Button } from '@/shared/ui/button'

interface CatalogExportButtonProps {
  /** Đường dẫn API danh mục (vd '/api/vehicles') — endpoint xuất là `<apiPath>/export/xlsx`. */
  apiPath: string
  /** Tên trường tìm kiếm nhanh của danh mục (vd 'license_plate') — để dịch `q` trên URL. */
  searchParam: string
  /** Tên tệp tải về (vd 'quan-ly-xe.xlsx'). */
  filename: string
}

/**
 * Nút "Xuất Excel" cho các danh mục dựng bằng khung CRUD chung — gắn qua
 * `config.renderToolbarExtra`. Nó XUẤT ĐÚNG bộ lọc đang xem: chép mọi tham số
 * trên URL trừ phân trang, và dịch ô tìm kiếm (`q`) sang đúng tên trường lọc
 * mà backend hiểu (`searchParam`), khớp cách `CrudListPage` gọi API danh sách.
 */
export function CatalogExportButton({ apiPath, searchParam, filename }: CatalogExportButtonProps) {
  const [searchParams] = useSearchParams()

  const handleExport = async () => {
    const q = new URLSearchParams()
    for (const [key, value] of searchParams.entries()) {
      if (key === 'page' || key === 'page_size') continue
      // Ô tìm kiếm ghi lên URL bằng `q`; API lọc theo TÊN TRƯỜNG (searchParam).
      if (key === 'q') {
        if (value) q.set(searchParam, value)
        continue
      }
      q.set(key, value)
    }
    const suffix = q.toString()
    await downloadFile(`${apiPath}/export/xlsx${suffix ? `?${suffix}` : ''}`, filename)
  }

  return (
    <Button variant="outline" size="sm" onClick={() => void handleExport()}>
      <Download className="mr-1.5 size-4" />
      Xuất Excel
    </Button>
  )
}
