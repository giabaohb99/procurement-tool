import { Table2 } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { Button } from '@/shared/ui/button'
import { PageHeader } from '@/shared/ui/page-header'

interface ReportPageHeaderProps {
  title: string
  description: string
  /** Trang BẢNG gốc bên phân hệ chủ — nơi soi từng dòng. Bỏ trống = ẩn nút. */
  sourcePath?: string
  /** Nút Xuất Excel đã dựng sẵn (`ReportExportButton`) — trang tự quyết có hay không. */
  exportButton?: ReactNode
}

/** Đầu trang của một báo cáo Haravan: tiêu đề · mô tả · "Xem bảng chi tiết" · Xuất Excel. */
export function ReportPageHeader({
  title,
  description,
  sourcePath,
  exportButton,
}: ReportPageHeaderProps) {
  return (
    <PageHeader
      title={title}
      description={<span className="max-md:hidden">{description}</span>}
      actions={
        <>
          {sourcePath && (
            <Button variant="outline" asChild>
              <Link to={sourcePath}>
                <Table2 />
                Xem bảng chi tiết
              </Link>
            </Button>
          )}
          {exportButton}
        </>
      }
    />
  )
}
