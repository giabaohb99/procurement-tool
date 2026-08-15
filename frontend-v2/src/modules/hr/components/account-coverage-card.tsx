import { AlertTriangle, UserX } from 'lucide-react'

import { ChartCard, ChartLegendItem } from '@/shared/ui/chart'
import { cn } from '@/shared/utils/cn'
import type { AccountCoverage } from '../hooks/use-hr-overview'

interface AccountCoverageCardProps {
  data: AccountCoverage
  loading: boolean
  /** Không có quyền đọc `user` thì hiện lời nhắn thay vì thẻ rỗng. */
  canRead: boolean
}

/**
 * Tỉ lệ nhân sự đang làm việc đã được cấp tài khoản, kèm hai cảnh báo hay gặp:
 * tài khoản chưa gán vai trò và tài khoản không còn hồ sơ nhân sự.
 *
 * Một tỉ lệ trên một tổng thì dùng THANH TỈ LỆ, không dùng biểu đồ tròn hai lát.
 */
export function AccountCoverageCard({ data, loading, canRead }: AccountCoverageCardProps) {
  const percent = data.totalActive > 0 ? Math.round((data.withAccount / data.totalActive) * 100) : 0

  if (!canRead) {
    return (
      <ChartCard
        title="Tình trạng tài khoản"
        isEmpty
        emptyLabel="Bạn không có quyền xem tài khoản đăng nhập."
      >
        <div />
      </ChartCard>
    )
  }

  return (
    <ChartCard
      title="Tình trạng tài khoản"
      description="Nhân sự đang làm việc đã được cấp tài khoản đăng nhập."
      loading={loading}
      isEmpty={data.totalActive === 0}
      emptyLabel="Chưa có nhân sự đang làm việc."
    >
      <div className="space-y-4">
        <div className="flex items-baseline gap-2">
          {/* Số lớn để chữ số theo bề rộng tự nhiên; tabular-nums chỉ dành cho
              cột số phải thẳng hàng. */}
          <span className="text-3xl font-semibold text-navy dark:text-foreground">
            {percent}%
          </span>
          <span className="text-sm text-muted-foreground">
            {data.withAccount}/{data.totalActive} nhân sự
          </span>
        </div>

        {/* Thanh tỉ lệ: phần đã cấp đậm, rãnh là bậc nhạt CÙNG tông xanh. */}
        <div
          className="h-2.5 w-full overflow-hidden rounded-full bg-chart-track"
          role="img"
          aria-label={`${data.withAccount} trên ${data.totalActive} nhân sự đã có tài khoản`}
        >
          <div
            className="h-full rounded-full bg-chart-1 transition-[width] duration-500"
            style={{ width: `${percent}%` }}
          />
        </div>

        <ul className="space-y-2">
          <ChartLegendItem
            color="var(--chart-1)"
            label="Đã có tài khoản"
            value={data.withAccount.toLocaleString('vi-VN')}
          />
          <ChartLegendItem
            color="var(--chart-track)"
            label="Chưa có tài khoản"
            value={data.withoutAccount.toLocaleString('vi-VN')}
          />
        </ul>

        {/* Hai ô nhỏ đặt cạnh nhau: số đứng ngay cạnh nhãn, không kéo nhãn một
            đầu số một đầu như dòng chú giải ở trên. */}
        <div className="grid grid-cols-2 gap-3 border-t pt-3">
          <IssueStat
            icon={AlertTriangle}
            label="Chưa gán vai trò"
            count={data.noRole}
            hint="Tài khoản đăng nhập được nhưng không mở được màn hình nào."
          />
          <IssueStat
            icon={UserX}
            label="Không có hồ sơ NS"
            count={data.orphan}
            hint="Hồ sơ nhân sự đã xóa nhưng tài khoản còn hiệu lực."
          />
        </div>
      </div>
    </ChartCard>
  )
}

/**
 * Ô cảnh báo nhỏ: số nằm ngay cạnh icon, nhãn xuống dòng dưới.
 * Chỉ tô màu cảnh báo khi thật sự có vấn đề — và luôn kèm icon + chữ, không để
 * riêng màu gánh ý nghĩa.
 */
function IssueStat({
  icon: Icon,
  label,
  count,
  hint,
}: {
  icon: typeof AlertTriangle
  label: string
  count: number
  hint: string
}) {
  const hasIssue = count > 0

  return (
    <div className="rounded-lg bg-muted/60 px-3 py-2" title={hint}>
      <div className="flex items-center gap-1.5">
        <Icon
          className={cn('size-4 shrink-0 text-muted-foreground', hasIssue && 'text-warning')}
        />
        <span
          className={cn('font-semibold tabular-nums text-foreground', hasIssue && 'text-warning')}
        >
          {count.toLocaleString('vi-VN')}
        </span>
      </div>
      <p className="mt-0.5 text-xs text-muted-foreground">{label}</p>
    </div>
  )
}
