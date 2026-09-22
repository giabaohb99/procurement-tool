import { UserCheck } from 'lucide-react'

import { Card } from '@/shared/ui/card'
import type { SealRequest } from '../types/seal-request'
import { SealInfoRow } from './seal-info-row'
import { SealSectionHeader } from './seal-section-header'

/**
 * Thẻ **NGƯỜI YÊU CẦU & ĐƠN VỊ** — đứng ở CỘT PHẢI (dời 22/09/2026, trước đó là
 * khối 3 của thân phiếu).
 *
 * ⚠️ Xếp kiểu NHÃN TRÁI — GIÁ TRỊ PHẢI (`SealInfoRow`), KHÔNG phải lưới
 * `sm:grid-cols-2` như hồi còn ở cột chính. Ngưỡng `sm:` của Tailwind đo BỀ
 * NGANG MÀN HÌNH chứ không đo bề ngang thẻ, nên trong cột 380px nó vẫn bật và
 * cắt thành hai ô ~170px — "Nhân sự · Sản xuất -Thu mua" gãy thành ba dòng.
 *
 * Nhãn rút ngắn ("Chức danh" thay vì "Chức danh / Phòng ban") vì tiêu đề thẻ đã
 * nói rõ đây là thông tin người yêu cầu; nhãn dài thì đẩy giá trị xuống dòng.
 */
export function SealRequesterCard({ request }: { request: SealRequest }) {
  return (
    <Card className="flex flex-col gap-3 p-5">
      <SealSectionHeader
        icon={UserCheck}
        title="Người yêu cầu & Đơn vị"
        iconColor="text-indigo-600 dark:text-indigo-400"
      />

      {/*  Bốn dòng để NGUYÊN kiểu chữ của `SealInfoRow`, không tự thêm
          `font-mono` / `text-xs` / `text-muted-foreground` — xem chú thích ở
          `seal-info-row.tsx`. */}
      <SealInfoRow label="Họ và tên">{request.requester || '—'}</SealInfoRow>

      <SealInfoRow label="Chức danh">{request.requester_role || '—'}</SealInfoRow>

      <SealInfoRow label="Email">{request.requester_email || '—'}</SealInfoRow>

      <SealInfoRow label="Điện thoại">
        <span className="tabular-nums">{request.requester_phone || '—'}</span>
      </SealInfoRow>
    </Card>
  )
}
