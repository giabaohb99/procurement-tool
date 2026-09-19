import { ChevronRight, Stamp, Users } from 'lucide-react'
import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { nameInitials } from '@/shared/utils/name-initials'
import { useSealClerks } from '../hooks/use-seal-clerks'
import { useSealTypes } from '../hooks/use-seal-types'
import { CompanyAvatarGroup } from './company-avatar-group'

/** Số văn thư bày trên thẻ; phần còn lại xem ở màn Phân công. */
const MAX_CLERKS = 4

/**
 * Hai thẻ chân trang Tổng quan: danh mục con dấu đang lưu hành và đội văn thư
 * phụ trách.
 *
 * ⚠️ Hai lỗi bố cục của bản trước, cả hai đều nhìn thấy trên máy thật:
 *
 * 1. `Card` khai `justify-between` mà hai thẻ lại nằm cùng một hàng lưới (ô
 *    lưới kéo cao bằng nhau). Thẻ con dấu chỉ có mấy con chip nên `justify-
 *    between` đẩy chúng xuống ĐÁY thẻ, chừa gần 300px trắng ở giữa — đọc ra
 *    như biểu đồ tải hỏng. Nay bỏ `justify-between` và cho lưới `items-start`.
 * 2. Mỗi dòng văn thư in TÊN ĐẦY ĐỦ của mọi công ty phụ trách, nối bằng dấu
 *    phẩy ("CÔNG TY TNHH N2SBIO VIỆT NAM, CÔNG TY TNHH XUẤT NHẬP KHẨU IDA
 *    GLOBAL, …") nên dòng gãy ba hàng và huy hiệu «Văn thư tổng» bị đẩy vào
 *    giữa đoạn chữ. Nay dùng cụm ảnh tròn công ty như ở màn danh sách văn thư.
 */
export function SealDirectoryGlanceCard() {
  const { data: typeData, isLoading: isLoadingTypes } = useSealTypes({ page: 1, page_size: 10 })
  const { data: clerkData, isLoading: isLoadingClerks } = useSealClerks({ page: 1, page_size: 10 })

  const sealTypes = typeData?.items ?? []
  const clerks = clerkData?.items ?? []

  return (
    <div className="grid items-start gap-4 md:grid-cols-2">
      <GlanceCard
        icon={<Stamp className="size-4 text-rose-600 dark:text-rose-400" />}
        title="Danh mục con dấu lưu hành"
        description="Các mẫu dấu pháp lý đang dùng tại DEGO Holding"
        actionLabel="Quản lý"
        actionTo={appRoutes.approvalSeal.sealTypes}
        isLoading={isLoadingTypes}
        isEmpty={sealTypes.length === 0}
        emptyLabel="Chưa có danh mục con dấu."
      >
        <div className="flex flex-wrap gap-2">
          {sealTypes.map((t) => (
            <span
              key={t.id}
              className="inline-flex items-center gap-1.5 rounded-full border bg-muted/30 px-2.5 py-1 text-xs font-medium"
            >
              <span className="size-1.5 rounded-full bg-rose-500" aria-hidden="true" />
              {t.name}
            </span>
          ))}
        </div>
      </GlanceCard>

      <GlanceCard
        icon={<Users className="size-4 text-sky-600 dark:text-sky-400" />}
        title="Văn thư phụ trách đóng dấu"
        description="Cán bộ đầu mối tiếp nhận và đóng dấu theo đơn vị"
        actionLabel="Phân công"
        actionTo={appRoutes.approvalSeal.clerks}
        isLoading={isLoadingClerks}
        isEmpty={clerks.length === 0}
        emptyLabel="Chưa phân công văn thư."
      >
        <ul className="flex flex-col divide-y">
          {clerks.slice(0, MAX_CLERKS).map((c) => (
            <li
              key={c.anchor_id || c.employee_id}
              className="flex items-center justify-between gap-3 py-2 first:pt-0 last:pb-0"
            >
              <div className="flex min-w-0 items-center gap-2.5">
                <span className="grid size-7 shrink-0 place-items-center rounded-full bg-sky-100 text-[11px] font-semibold text-sky-700 dark:bg-sky-950 dark:text-sky-300">
                  {nameInitials(c.employee_name || 'Văn thư')}
                </span>
                <div className="flex min-w-0 flex-col">
                  <span className="flex items-center gap-1.5">
                    <span className="truncate text-sm font-medium">
                      {c.employee_name || 'Văn thư'}
                    </span>
                    {c.is_head && (
                      <span className="shrink-0 rounded-full bg-amber-100 px-1.5 py-0.5 text-[10px] font-semibold text-amber-700 dark:bg-amber-950 dark:text-amber-300">
                        Văn thư tổng
                      </span>
                    )}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {c.companies?.length
                      ? `${c.companies.length} pháp nhân`
                      : 'Chưa gán pháp nhân'}
                  </span>
                </div>
              </div>
              {/*  Cụm ảnh tròn thay cho chuỗi tên công ty: tên pháp nhân ở đây
                  dài 30-45 ký tự, ba cái nối lại là gãy ba dòng. Rê chuột vào
                  ảnh là ra tên đầy đủ. */}
              <div className="shrink-0">
                <CompanyAvatarGroup
                  companies={c.companies ?? []}
                  maxVisible={3}
                  showNameWhenSingle={false}
                />
              </div>
            </li>
          ))}
        </ul>
      </GlanceCard>
    </div>
  )
}

/** Khung chung của hai thẻ: tiêu đề + liên kết quản lý + vùng nội dung. */
function GlanceCard({
  icon,
  title,
  description,
  actionLabel,
  actionTo,
  isLoading,
  isEmpty,
  emptyLabel,
  children,
}: {
  icon: ReactNode
  title: string
  description: string
  actionLabel: string
  actionTo: string
  isLoading: boolean
  isEmpty: boolean
  emptyLabel: string
  children: ReactNode
}) {
  return (
    <Card className="flex flex-col gap-0 p-0">
      <div className="flex items-start justify-between gap-3 border-b px-4 py-3">
        <div className="flex min-w-0 items-start gap-2.5">
          <span className="mt-0.5 shrink-0">{icon}</span>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-navy dark:text-foreground">{title}</p>
            <p className="truncate text-xs text-muted-foreground">{description}</p>
          </div>
        </div>
        <Link
          to={actionTo}
          className="flex shrink-0 items-center gap-0.5 text-xs font-medium text-muted-foreground hover:text-primary"
        >
          {actionLabel}
          <ChevronRight className="size-3.5" />
        </Link>
      </div>
      <div className="px-4 py-3">
        {isLoading ? (
          <div className="flex flex-col gap-2">
            <Skeleton className="h-8 w-full" />
            <Skeleton className="h-8 w-2/3" />
          </div>
        ) : isEmpty ? (
          <p className="py-4 text-center text-sm text-muted-foreground">{emptyLabel}</p>
        ) : (
          children
        )}
      </div>
    </Card>
  )
}
