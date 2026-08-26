import { GitBranch, ShieldAlert } from 'lucide-react'
import { useNavigate } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { Switch } from '@/shared/ui/switch'
import { engineRowStatus, type EngineRowTone } from '../helpers/engine-row-status'
import { CAC_LOAI, ENTITY_LABELS } from '../helpers/entity-link'
import {
  useApprovalFlows,
  useApprovalSwitches,
  useSetApprovalSwitch,
} from '../hooks/use-approvals'

/** Chỉ loại đang thật sự chạy bộ máy mới mới tô đậm. */
const BADGE_VARIANT: Record<EngineRowTone, 'default' | 'outline'> = {
  running: 'default',
  idle: 'outline',
  off: 'outline',
}

/**
 * I26 — BẬT BỘ MÁY DUYỆT MỚI theo từng loại chứng từ.
 *
 * Đây là **đường lui của cả phase**: tắt một loại là loại đó quay về đường
 * duyệt cũ ngay, không cần deploy lại. Phiếu đã bắt đầu chạy bằng bộ máy mới
 * thì vẫn chạy tiếp cho hết — cắt ngang giữa chừng là bỏ rơi phiếu ở trạng
 * thái không màn hình nào nhặt lên.
 *
 * Tách thành màn riêng chứ không nằm trên đầu danh sách luồng: đây là công tắc
 * mức hệ thống, dùng vài lần một năm, mà đặt cùng chỗ với việc khai luồng hằng
 * ngày thì vừa chiếm mất chỗ của bảng, vừa mời người ta gạt nhầm.
 */
export function ApprovalEnginePage() {
  const navigate = useNavigate()
  const { data: switches } = useApprovalSwitches()
  const { data: flows } = useApprovalFlows()
  const setSwitch = useSetApprovalSwitch()

  const isOn = new Map((switches ?? []).map((row) => [row.entity, row.is_enabled]))
  //  Đếm luồng ĐANG DÙNG: luồng đã tắt không được tính, nếu không màn này báo
  //  "có 2 luồng" trong khi cả hai đều nằm im.
  const quantity = new Map(
    CAC_LOAI.map((ma) => [
      ma,
      (flows?.items ?? []).filter((row) => row.entity === ma && row.is_active).length,
    ]),
  )
  const runningNumber = CAC_LOAI.filter((ma) => isOn.get(ma) && quantity.get(ma)).length

  return (
    <PageContainer>
      <PageHeader
        title="Bật bộ máy duyệt"
        description="Chọn loại chứng từ nào chạy theo luồng đã khai, loại nào giữ đường duyệt cũ."
        actions={
          <Button variant="outline" onClick={() => navigate(appRoutes.approval.flows)}>
            <GitBranch className="size-4" />
            Luồng duyệt
          </Button>
        }
      />

      <Card className="mb-4 flex-row items-start gap-3 p-4">
        <ShieldAlert className="mt-0.5 size-5 shrink-0 text-muted-foreground" />
        <div className="space-y-1 text-sm">
          <p>
            Mặc định <b>TẮT</b> cho mọi loại. Tắt thì chứng từ đi theo đường duyệt cũ đang
            chạy — đây là <b>đường lui</b> khi bộ máy mới có sự cố, giữ nguyên để còn quay
            về được.
          </p>
          <p className="text-muted-foreground">
            Tắt giữa chừng <b>không cắt ngang</b> phiếu đang chạy: chúng đi hết bản luồng
            đã chụp lúc trình. Chỉ phiếu tạo sau đó mới quay về đường cũ.
          </p>
        </div>
      </Card>

      <Card className="gap-0 p-0">
        <div className="flex items-baseline justify-between gap-3 border-b px-4 py-3">
          <h2 className="text-sm font-medium">Theo loại chứng từ</h2>
          <span className="text-xs text-muted-foreground">
            {runningNumber}/{CAC_LOAI.length} loại đang chạy bộ máy mới
          </span>
        </div>

        <ul className="divide-y">
          {CAC_LOAI.map((ma) => {
            const bat = isOn.get(ma) ?? false
            const status = engineRowStatus(quantity.get(ma) ?? 0, bat)

            return (
              <li key={ma} className="flex items-center justify-between gap-4 px-4 py-3">
                <div className="min-w-0">
                  <p className="text-sm font-medium">{ENTITY_LABELS[ma]}</p>
                  <p className="text-xs text-muted-foreground">{status.hint}</p>
                </div>

                <div className="flex shrink-0 items-center gap-3">
                  <Badge variant={BADGE_VARIANT[status.tone]}>{status.label}</Badge>
                  <Switch
                    checked={bat}
                    disabled={setSwitch.isPending}
                    aria-label={`Bật bộ máy duyệt mới cho ${ENTITY_LABELS[ma]}`}
                    onCheckedChange={(value) =>
                      setSwitch.mutate({ entity: ma, is_enabled: value, note: '' })
                    }
                  />
                </div>
              </li>
            )
          })}
        </ul>
      </Card>
    </PageContainer>
  )
}
