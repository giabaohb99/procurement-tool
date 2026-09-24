import { ChevronRight } from 'lucide-react'
import { Fragment } from 'react'

import {
  Breadcrumb,
  BreadcrumbEllipsis,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/shared/ui/breadcrumb'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/shared/ui/dropdown-menu'
import { collapseBreadcrumb } from '../helpers/collapse-breadcrumb'
import type { FolderBreadcrumbItem } from '../types/document-folder'

interface FolderBreadcrumbProps {
  /** ĐẦY ĐỦ từ gốc pháp nhân tới chính thư mục đang xem (`folder.breadcrumb`, phần tử CUỐI là chính nó). */
  crumbs: FolderBreadcrumbItem[]
  onNavigate: (id: number) => void
  /**
   * Chữ NGẮN hiện thay tên pháp lý — `FolderBreadcrumbItem.name` LUÔN là tên
   * đầy đủ (backend chưa gộp `display_name` vào kiểu này), nên breadcrumb cần
   * tự tra qua chỗ khác (`useFolderDisplayNameLookup`). Bỏ trống = hiện
   * nguyên `crumb.name` (test cũ, hoặc nơi gọi chưa cần tra).
   */
  getDisplayName?: (id: number, fallbackName: string) => string
}

function CrumbLink({
  crumb,
  label,
  onNavigate,
}: {
  crumb: FolderBreadcrumbItem
  label: string
  onNavigate: (id: number) => void
}) {
  return (
    <BreadcrumbItem>
      <BreadcrumbLink asChild>
        <button type="button" onClick={() => onNavigate(crumb.id)} className="hover:text-foreground">
          {label}
        </button>
      </BreadcrumbLink>
    </BreadcrumbItem>
  )
}

/**
 * Đường dẫn thư mục kiểu Drive (đặc tả §4, duoc-CR-476; chốt dọn gọn lead
 * 24/09/2026 tối) — CHỈ hiện khi thư mục đang xem KHÔNG PHẢI gốc pháp nhân
 * (`crumbs.length > 1`): ở gốc, tiêu đề `FolderViewToolbar` ngay dưới đã đủ
 * nói "đang đứng ở đâu", một breadcrumb một đoạn chỉ lặp lại y hệt tên đó.
 * Mỗi đoạn bấm được, riêng ĐOẠN CUỐI (chính thư mục đang xem) là
 * `BreadcrumbPage` — không phải link vì bấm vào chính trang đang đứng không
 * có ý nghĩa gì. Đường dài GẬP đoạn giữa vào một `DropdownMenu`
 * (`collapseBreadcrumb`, hàm thuần có test riêng).
 */
export function FolderBreadcrumb({ crumbs, onNavigate, getDisplayName }: FolderBreadcrumbProps) {
  if (crumbs.length <= 1) return null
  const label = (crumb: FolderBreadcrumbItem) => getDisplayName?.(crumb.id, crumb.name) ?? crumb.name
  const { head, collapsed, tail } = collapseBreadcrumb(crumbs)
  const current = tail[tail.length - 1]
  const tailLinks = tail.slice(0, -1)

  return (
    <Breadcrumb>
      <BreadcrumbList className="flex-nowrap text-xs">
        {head.map((crumb) => (
          <Fragment key={crumb.id}>
            <CrumbLink crumb={crumb} label={label(crumb)} onNavigate={onNavigate} />
            <BreadcrumbSeparator>
              <ChevronRight className="size-3" />
            </BreadcrumbSeparator>
          </Fragment>
        ))}

        {collapsed.length > 0 && (
          <>
            <BreadcrumbItem>
              <DropdownMenu>
                <DropdownMenuTrigger aria-label="Xem các thư mục ở giữa đường dẫn">
                  <BreadcrumbEllipsis className="cursor-pointer rounded hover:bg-muted" />
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start">
                  {collapsed.map((crumb) => (
                    <DropdownMenuItem key={crumb.id} onSelect={() => onNavigate(crumb.id)}>
                      {label(crumb)}
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>
            </BreadcrumbItem>
            <BreadcrumbSeparator>
              <ChevronRight className="size-3" />
            </BreadcrumbSeparator>
          </>
        )}

        {tailLinks.map((crumb) => (
          <Fragment key={crumb.id}>
            <CrumbLink crumb={crumb} label={label(crumb)} onNavigate={onNavigate} />
            <BreadcrumbSeparator>
              <ChevronRight className="size-3" />
            </BreadcrumbSeparator>
          </Fragment>
        ))}

        {current && (
          <BreadcrumbItem>
            <BreadcrumbPage className="truncate font-medium text-foreground">{label(current)}</BreadcrumbPage>
          </BreadcrumbItem>
        )}
      </BreadcrumbList>
    </Breadcrumb>
  )
}
