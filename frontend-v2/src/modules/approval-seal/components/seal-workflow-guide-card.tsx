import { CheckCircle2, FileEdit, FileText, Stamp, UserCheck } from 'lucide-react'

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/shared/ui/card'

const WORKFLOW_STEPS = [
  {
    step: '01',
    title: 'Tạo yêu cầu',
    role: 'Người yêu cầu',
    desc: 'Lập phiếu, đính kèm văn bản, chọn pháp nhân công ty & loại con dấu cần đóng.',
    icon: FileEdit,
    color: 'text-blue-500 dark:text-blue-400 bg-blue-500/10 border-blue-500/20',
  },
  {
    step: '02',
    title: 'TBP Thẩm định',
    role: 'Trưởng bộ phận',
    desc: 'Kiểm tra tính hợp lệ của văn bản, mục đích sử dụng con dấu và phê duyệt.',
    icon: UserCheck,
    color: 'text-amber-500 dark:text-amber-400 bg-amber-500/10 border-amber-500/20',
  },
  {
    step: '03',
    title: 'Văn thư Đóng dấu',
    role: 'Văn thư pháp nhân',
    desc: 'Đối chiếu bản in/gốc, kiểm tra thẩm quyền ký và thực hiện đóng dấu theo quy định.',
    icon: Stamp,
    color: 'text-rose-500 dark:text-rose-400 bg-rose-500/10 border-rose-500/20',
  },
  {
    step: '04',
    title: 'Hoàn tất & Lưu trữ',
    role: 'Hệ thống & Lưu trữ',
    desc: 'Bàn giao tài liệu đã đóng dấu, lưu vết mã phiếu và số hóa tài liệu lưu trữ.',
    icon: CheckCircle2,
    color: 'text-emerald-500 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/20',
  },
]

export function SealWorkflowGuideCard() {
  return (
    <Card className="overflow-hidden border-border/80">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2 text-base font-semibold">
              <FileText className="size-4 text-primary" />
              Quy trình Trình ký & Đóng dấu văn bản
            </CardTitle>
            <CardDescription className="text-xs">
              Chu trình 4 bước chuẩn hóa theo quy chế quản lý & sử dụng con dấu của DEGO Holding
            </CardDescription>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-0">
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
          {WORKFLOW_STEPS.map((item, idx) => {
            const Icon = item.icon
            return (
              <div
                key={item.step}
                className="relative flex flex-col justify-between rounded-lg border border-border/60 bg-muted/20 p-3 transition-colors hover:border-border hover:bg-muted/30"
              >
                <div>
                  <div className="mb-2 flex items-center justify-between">
                    <div className={`flex size-8 items-center justify-center rounded-md border ${item.color}`}>
                      <Icon className="size-4" />
                    </div>
                    <span className="font-mono text-xs font-bold text-muted-foreground/60">
                      BƯỚC {item.step}
                    </span>
                  </div>
                  <h4 className="text-sm font-semibold text-foreground">{item.title}</h4>
                  <div className="mb-1.5 inline-block text-[11px] font-medium text-primary">
                    {item.role}
                  </div>
                  <p className="text-xs leading-relaxed text-muted-foreground">
                    {item.desc}
                  </p>
                </div>

                {idx < WORKFLOW_STEPS.length - 1 && (
                  <div className="absolute -right-2.5 top-1/2 hidden -translate-y-1/2 text-muted-foreground/40 lg:block">
                    →
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </CardContent>
    </Card>
  )
}
