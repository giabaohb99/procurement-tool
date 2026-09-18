import { Building2, ChevronRight, Stamp, Users } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'
import { useSealClerks } from '../hooks/use-seal-clerks'
import { useSealTypes } from '../hooks/use-seal-types'

export function SealDirectoryGlanceCard() {
  const { data: typeData, isLoading: isLoadingTypes } = useSealTypes({ page: 1, page_size: 10 })
  const { data: clerkData, isLoading: isLoadingClerks } = useSealClerks({ page: 1, page_size: 10 })

  const sealTypes = typeData?.items ?? []
  const clerks = clerkData?.items ?? []

  return (
    <div className="grid gap-4 md:grid-cols-2">
      {/* Khối 1: Danh mục con dấu */}
      <Card className="flex flex-col justify-between border-border/80">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Stamp className="size-4 text-primary" />
                Danh mục con dấu lưu hành
              </CardTitle>
              <CardDescription className="text-xs">
                Các mẫu dấu pháp lý được sử dụng tại DEGO Holding
              </CardDescription>
            </div>
            <Button asChild variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground">
              <Link to={appRoutes.approvalSeal.sealTypes}>
                Quản lý
                <ChevronRight className="ml-1 size-3" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoadingTypes ? (
            <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
              Đang tải danh mục con dấu...
            </div>
          ) : sealTypes.length === 0 ? (
            <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
              Chưa có danh mục con dấu.
            </div>
          ) : (
            <div className="flex flex-wrap gap-2">
              {sealTypes.map((t) => (
                <div
                  key={t.id}
                  className="flex items-center gap-1.5 rounded-md border border-border/70 bg-background/50 px-2.5 py-1.5 text-xs font-medium shadow-xs"
                >
                  <span className="size-1.5 rounded-full bg-rose-500" />
                  <span>{t.name}</span>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Khối 2: Văn thư phụ trách theo pháp nhân */}
      <Card className="flex flex-col justify-between border-border/80">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2 text-sm font-semibold">
                <Users className="size-4 text-primary" />
                Văn thư phụ trách đóng dấu
              </CardTitle>
              <CardDescription className="text-xs">
                Cán bộ đầu mối tiếp nhận và thực hiện đóng dấu theo đơn vị
              </CardDescription>
            </div>
            <Button asChild variant="ghost" size="sm" className="h-7 text-xs text-muted-foreground">
              <Link to={appRoutes.approvalSeal.clerks}>
                Phân công
                <ChevronRight className="ml-1 size-3" />
              </Link>
            </Button>
          </div>
        </CardHeader>
        <CardContent className="pt-0">
          {isLoadingClerks ? (
            <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
              Đang tải danh sách văn thư...
            </div>
          ) : clerks.length === 0 ? (
            <div className="flex h-24 items-center justify-center text-xs text-muted-foreground">
              Chưa phân công văn thư.
            </div>
          ) : (
            <div className="space-y-2">
              {clerks.slice(0, 4).map((c) => (
                <div
                  key={c.anchor_id || c.employee_id}
                  className="flex items-center justify-between rounded-md border border-border/60 bg-muted/20 px-2.5 py-1.5 text-xs"
                >
                  <div className="flex items-center gap-2">
                    <div className="flex size-6 items-center justify-center rounded-full bg-primary/10 text-[11px] font-bold text-primary">
                      {(c.employee_name || 'VT')[0].toUpperCase()}
                    </div>
                    <div>
                      <div className="font-medium text-foreground">{c.employee_name || 'Văn thư'}</div>
                      <div className="flex items-center gap-1 text-[11px] text-muted-foreground">
                        <Building2 className="size-3" />
                        {c.companies?.map((cp) => cp.name).join(', ') || 'Chưa gán'}
                      </div>
                    </div>
                  </div>
                  {c.is_head && (
                    <Badge variant="outline" className="border-amber-300 bg-amber-50 text-[10px] text-amber-800 dark:border-amber-700 dark:bg-amber-950 dark:text-amber-200">
                      Văn thư tổng
                    </Badge>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
