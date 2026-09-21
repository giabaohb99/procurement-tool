import { FileText, FolderOpen } from 'lucide-react'
import { Link } from 'react-router-dom'

import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Card } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { DossierExpiryBadge } from './dossier-status-badge'
import { useApplicableDossiers } from '../hooks/use-applicable-dossiers'
import type { DossierExpiryState } from '../types/dossier'
import type { DocKind } from '../types/dossier-applicability'

interface RequiredDossiersCardProps {
  docKind: DocKind
  /** `undefined` ở trang THÊM MỚI — chứng từ chưa có thì chưa có dòng nào để khớp. */
  docId: number | undefined
}

/**
 * THẺ «HỒ SƠ CẦN KÈM» — mọc ra ở chân trang chi tiết của bốn loại chứng từ
 * (YCMH · ĐMH · YCBG · Phiếu khảo sát) khi có dòng hàng khớp điều kiện áp dụng
 * của một tờ hồ sơ. Luật khớp ở `backend/.../dossier/applicability.py`.
 *
 * ⚠️ **KHÔNG có gì để bày thì KHÔNG vẽ gì cả** — kể cả khung rỗng hay câu «chưa
 * có hồ sơ nào». Khác hẳn mục *Bàn giao công việc* của Nghỉ phép, thứ luôn dựng
 * kể cả khi rỗng (CR-260): ở đó «không ai bàn giao» là một câu trả lời người
 * duyệt cần, còn ở đây «không hồ sơ nào khớp» là tình trạng của **gần như mọi**
 * chứng từ trong hệ. Dựng khung rỗng ở bốn màn đông người dùng nhất là thêm một
 * khối vô nghĩa vào trang của họ mỗi ngày.
 *
 * ⚠️ Câu lý do (`reason`) do **backend** dựng — đừng ghép lại ở đây. Bản in sau
 * này cần đúng câu đó, mà chép luật sang TypeScript thì hai bên lệch nhau lúc
 * nào không ai biết (cùng lý lẽ `approval/steps_service._summary`).
 */
export function RequiredDossiersCard({ docKind, docId }: RequiredDossiersCardProps) {
  const { data, isLoading } = useApplicableDossiers(docKind, docId)

  //  Thiếu `dossier.read` thì hook tự tắt, `data` mãi `undefined` → không vẽ.
  //  Đang nạp cũng không vẽ khung: phần lớn lượt trả về RỖNG, nên hiện khung rồi
  //  gỡ đi là trang giật một cái ở mỗi lần mở chứng từ.
  if (isLoading || !data || data.items.length === 0) return null

  return (
    <Card className="gap-0 p-0">
      <header className="flex items-center gap-2 border-b bg-muted/30 px-3 py-2.5 sm:px-4">
        <FolderOpen className="size-4 text-muted-foreground" />
        <h3 className="text-sm font-semibold">Hồ sơ cần kèm</h3>
        <Badge variant="secondary" className="ml-auto">
          {data.items.length}
        </Badge>
      </header>

      <ul className="divide-y">
        {data.items.map((row) => (
          <li key={row.id} className="px-3 py-2.5 sm:px-4">
            <div className="flex flex-wrap items-center gap-x-2 gap-y-1">
              {/*  Mở ra TAB MỚI: người đang đọc một tờ đơn mua hàng mà bấm vào
                   đây là đi tra cứu, không phải rời bỏ việc đang làm. Điều
                   hướng cùng tab thì họ mất chỗ đang cuộn tới và mọi ô vừa gõ
                   dở trên biểu mẫu chứng từ. */}
              <Link
                to={appRoutes.dossier.detail(row.id)}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1.5 font-medium text-primary hover:underline"
              >
                <FileText className="size-4 shrink-0" />
                {row.code}
              </Link>
              <span className="min-w-0 flex-1 truncate">{row.name}</span>
              <DossierExpiryBadge
                state={row.expiry_state as DossierExpiryState}
                days={row.expiry_days}
              />
            </div>
            <p className="mt-0.5 text-xs text-muted-foreground">
              {row.dossier_type_name && <span>{row.dossier_type_name} · </span>}
              {row.reason}
            </p>
          </li>
        ))}
      </ul>
    </Card>
  )
}

/** Khung chờ — chỉ dùng khi trang gọi muốn giữ chỗ, mặc định thẻ tự ẩn lúc nạp. */
export function RequiredDossiersSkeleton() {
  return <Skeleton className="h-24 w-full" />
}
