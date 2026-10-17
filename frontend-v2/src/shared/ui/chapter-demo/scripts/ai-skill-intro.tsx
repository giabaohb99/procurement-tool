import { Bot, Check, FileUp, KeyRound, ShieldOff } from 'lucide-react'

import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Checkbox } from '@/shared/ui/checkbox'
import { cn } from '@/shared/utils/cn'

import type { DemoChapter } from '../chapter-demo-types'
import { reached, typedText } from '../chapter-timeline'
import { DemoDialog, DemoToast, DemoTypedField, DemoWindow } from '../demo-stage'

import { Row, TickRow } from './scene-rows'

/**
 * Kịch bản giới thiệu KHO SKILL AI — 9 chương (ai-CR-214, K8 doc/erp/21 §6.4). Dữ liệu trong
 * cảnh là GIẢ, chỉ để minh họa; mỗi cảnh dựng bằng component v2 thật. Agent 3 gắn route trang
 * giới thiệu khi xong K5 (tệp này không đăng ký route nào).
 */

const DEPARTMENTS = ['Phòng Thu mua', 'Phòng Kế toán', 'Phòng Nhân sự', 'Nhà máy DEGO Organic']

const chooseDepartments: DemoChapter = {
  id: 'choose-departments',
  title: 'Chọn phòng ban sẽ dùng',
  caption: 'Bắt đầu từ một vài phòng: chọn phòng sẽ có cẩm nang riêng cho AI, phòng khác bật sau.',
  durationMs: 6000,
  cursor: [
    { at: 0, x: 80, y: 85 },
    { at: 0.3, x: 18, y: 35, click: true },
    { at: 0.6, x: 18, y: 62, click: true },
    { at: 0.9, x: 82, y: 86, click: true },
  ],
  render: ({ progress, reduced }) => (
    <DemoWindow title="Kho skill AI · Cấu hình" hint="Hệ thống / AI">
      <div className="grid h-full grid-cols-2 gap-3">
        <div className="space-y-2">
          <p className="text-xs font-medium">Phòng ban dùng Kho skill</p>
          {DEPARTMENTS.map((d, i) => (
            <TickRow key={d} label={d} checked={(i === 0 && reached(progress, 0.3)) || (i === 3 && reached(progress, 0.6))} />
          ))}
        </div>
        <div className="flex flex-col justify-end gap-2 text-xs text-muted-foreground">
          <p>Đã chọn {Number(reached(progress, 0.3)) + Number(reached(progress, 0.6))} phòng</p>
          <Button size="sm" className="self-end">Lưu cấu hình</Button>
        </div>
      </div>
      <DemoToast open={reached(progress, 0.92)} still={reduced}>
        Đã lưu: 2 phòng dùng Kho skill AI.
      </DemoToast>
    </DemoWindow>
  ),
}

const createSkillSet: DemoChapter = {
  id: 'create-skill-set',
  title: 'Tạo bộ skill',
  caption: 'Mỗi phòng một bộ cẩm nang; trưởng phòng là người chủ quản bộ của phòng mình.',
  durationMs: 7000,
  cursor: [
    { at: 0, x: 85, y: 20 },
    { at: 0.15, x: 85, y: 16, click: true },
    { at: 0.3, x: 50, y: 44, click: true },
    { at: 0.85, x: 62, y: 74, click: true },
  ],
  render: ({ progress, reduced }) => {
    const name = 'Quy trình thu mua'
    return (
      <DemoWindow title="Kho skill AI · Bộ skill" hint="3 bộ">
        <div className="flex justify-end">
          <Button size="sm">Tạo bộ</Button>
        </div>
        <div className="mt-2 space-y-1.5">
          <Row>Hướng dẫn nghỉ phép <Badge variant="secondary" className="ml-auto">Đang dùng</Badge></Row>
          <Row>Quy định đóng dấu <Badge variant="secondary" className="ml-auto">Đang dùng</Badge></Row>
        </div>
        <DemoDialog open={reached(progress, 0.17)} title="Tạo bộ skill" still={reduced}>
          <div className="space-y-2">
            <DemoTypedField label="Tên bộ" full={name} value={typedText(name, progress, 0.32, 0.6)} />
            <DemoTypedField label="Phòng chủ quản" full="Phòng Thu mua" value={reached(progress, 0.65) ? 'Phòng Thu mua' : ''} />
            <div className="flex justify-end">
              <Button size="sm">Tạo</Button>
            </div>
          </div>
        </DemoDialog>
      </DemoWindow>
    )
  },
}

const writeSkill: DemoChapter = {
  id: 'write-skill',
  title: 'Soạn hoặc tải skill lên',
  caption: 'Viết cẩm nang bằng chữ thường; bên phải là đúng thứ AI sẽ đọc. Có sẵn tài liệu thì tải gói lên.',
  durationMs: 8000,
  cursor: [
    { at: 0, x: 25, y: 40 },
    { at: 0.7, x: 25, y: 70 },
    { at: 0.8, x: 80, y: 88, click: true },
  ],
  render: ({ progress, reduced }) => {
    const body = '# Mua hàng gấp\n1. Ghi rõ lý do gấp trên YCMH.\n2. Trưởng phòng duyệt trong ngày.\n3. Thu mua báo giá tối thiểu 2 NCC.'
    const typed = typedText(body, progress, 0.05, 0.7)
    return (
      <DemoWindow title="Soạn skill · mua-hang-gap" hint="Bộ Quy trình thu mua">
        <div className="grid h-full grid-cols-2 gap-3">
          <pre className="overflow-hidden rounded-md border bg-muted/40 p-2 text-[11px] whitespace-pre-wrap">{typed}</pre>
          <div className="space-y-1 overflow-hidden rounded-md border p-2 text-[11px]">
            <p className="text-[10px] text-muted-foreground uppercase">Xem như AI đọc</p>
            {typed.split('\n').map((line, i) => (
              <p key={i} className={cn(line.startsWith('#') && 'text-sm font-semibold')}>{line.replace(/^#\s*/, '')}</p>
            ))}
          </div>
        </div>
        <DemoToast open={reached(progress, 0.82)} still={reduced}>
          <span className="flex items-center gap-1"><FileUp className="size-3" /> Đã tải gói quy-trinh-thu-mua.zip: 6 skill.</span>
        </DemoToast>
      </DemoWindow>
    )
  },
}

const assignReaders: DemoChapter = {
  id: 'assign-readers',
  title: 'Gán ai được đọc',
  caption: 'Chọn phòng ban (kể cả phòng con), chức vụ hoặc từng người; dòng cấm luôn thắng dòng cho phép.',
  durationMs: 7000,
  cursor: [
    { at: 0, x: 60, y: 20 },
    { at: 0.3, x: 12, y: 32, click: true },
    { at: 0.55, x: 12, y: 50, click: true },
    { at: 0.8, x: 78, y: 82 },
  ],
  render: ({ progress }) => (
    <DemoWindow title="Bộ Quy trình thu mua · Ai được đọc">
      <div className="grid h-full grid-cols-2 gap-3">
        <div className="space-y-1.5">
          <TickRow label="Phòng Thu mua (kể cả phòng con)" checked={reached(progress, 0.3)} />
          <TickRow label="Nhà máy DEGO Organic" checked={reached(progress, 0.55)} />
          <Row className="border-destructive/50 text-destructive">Cấm: Thực tập sinh</Row>
        </div>
        <div className="flex flex-col items-center justify-center rounded-md border bg-muted/30 text-center">
          <p className="text-2xl font-semibold tabular-nums">{reached(progress, 0.55) ? 37 : reached(progress, 0.3) ? 21 : 0}</p>
          <p className="text-xs text-muted-foreground">người đang thấy bộ này</p>
        </div>
      </div>
    </DemoWindow>
  ),
}

const issueKeys: DemoChapter = {
  id: 'issue-keys',
  title: 'Phát khóa cho từng người',
  caption: 'Quản trị phát khóa chỉ đọc cho cả phòng một lượt; mỗi người nhận chuông và tự bấm Nhận khóa.',
  durationMs: 7000,
  cursor: [
    { at: 0, x: 85, y: 18 },
    { at: 0.15, x: 85, y: 16, click: true },
    { at: 0.5, x: 50, y: 52, click: true },
    { at: 0.8, x: 62, y: 76, click: true },
  ],
  render: ({ progress, reduced }) => (
    <DemoWindow title="Khóa nhân sự" hint="Phòng Thu mua">
      <div className="flex justify-end">
        <Button size="sm"><KeyRound className="size-4" /> Phát khóa</Button>
      </div>
      <DemoDialog open={reached(progress, 0.17) && !reached(progress, 0.82)} title="Phát khóa kết nối AI" still={reduced}>
        <div className="space-y-2 text-xs">
          <Row>Nhận: <b>cả Phòng Thu mua (12 người)</b></Row>
          <Row>Mức: <Badge variant="outline">Chỉ đọc</Badge></Row>
          <Row>Hạn: <b>{reached(progress, 0.5) ? '90 ngày' : '30 ngày'}</b></Row>
          <div className="flex justify-end"><Button size="sm">Phát</Button></div>
        </div>
      </DemoDialog>
      <DemoToast open={reached(progress, 0.82)} still={reduced}>
        Đã phát 12 khóa, mỗi người sẽ nhận thông báo để lấy khóa.
      </DemoToast>
    </DemoWindow>
  ),
}

const connectAi: DemoChapter = {
  id: 'connect-ai',
  title: 'Nối AI của nhân sự',
  caption: 'Nhân sự chọn ứng dụng AI đang dùng, chép đoạn cấu hình có sẵn khóa, màn báo ngay khi đã nối.',
  durationMs: 7000,
  cursor: [
    { at: 0, x: 20, y: 25 },
    { at: 0.2, x: 20, y: 30, click: true },
    { at: 0.5, x: 86, y: 48, click: true },
  ],
  render: ({ progress }) => (
    <DemoWindow title="Trang cá nhân · AI của tôi">
      <div className="grid h-full grid-cols-[1fr_2fr] gap-3 text-xs">
        <div className="space-y-1.5">
          {['Claude Desktop', 'Claude Code', 'Cursor', 'Gemini CLI'].map((app, i) => (
            <Row key={app} className={cn(i === 0 && reached(progress, 0.2) && 'border-primary bg-accent')}>{app}</Row>
          ))}
        </div>
        <div className="space-y-2">
          <pre className="rounded-md border bg-muted/40 p-2 text-[10px] whitespace-pre-wrap">
            {'"dego-erp": { "command": "npx",\n  "args": ["-y", "mcp-remote", ".../api/mcp", ...] }'}
          </pre>
          <div className="flex items-center justify-between">
            <Button size="sm" variant="outline">{reached(progress, 0.5) ? <><Check className="size-4" /> Đã chép</> : 'Sao chép'}</Button>
            {reached(progress, 0.8) && <Badge>Đã nối · Claude Desktop</Badge>}
          </div>
        </div>
      </div>
    </DemoWindow>
  ),
}

const askAi: DemoChapter = {
  id: 'ask-ai',
  title: 'Hỏi AI một câu nghiệp vụ',
  caption: 'AI của nhân sự đọc đúng skill công ty rồi tra ERP dưới quyền người đó, trả lời có số thật.',
  durationMs: 9000,
  render: ({ progress }) => {
    const question = 'Đơn PO00358 mua gấp, bước tiếp theo là gì và đơn tới đâu rồi?'
    return (
      <DemoWindow title="Claude Desktop" hint="đã nối dego-erp">
        <div className="flex h-full flex-col gap-2 text-xs">
          <div className="self-end rounded-lg bg-primary px-3 py-2 text-primary-foreground">
            {typedText(question, progress, 0, 0.3)}
          </div>
          {reached(progress, 0.35) && (
            <Row className="w-fit"><Bot className="size-3" /> Đọc skill mua-hang-gap</Row>
          )}
          {reached(progress, 0.5) && (
            <Row className="w-fit"><Bot className="size-3" /> Tra erp_read: purchase_order PO00358</Row>
          )}
          {reached(progress, 0.65) && (
            <div className="max-w-[85%] rounded-lg border bg-background px-3 py-2">
              {typedText('Theo quy trình mua gấp: thu mua cần báo giá tối thiểu 2 NCC. Đơn PO00358 đã duyệt, nhận 2/3 lần giao, còn 1 lần hẹn 21/10.', progress, 0.65, 0.98)}
            </div>
          )}
        </div>
      </DemoWindow>
    )
  },
}

const watchUsage: DemoChapter = {
  id: 'watch-usage',
  title: 'Xem ai dùng gì',
  caption: 'Tổng quan và nhật ký cho biết ai đang dùng, đọc skill nào, gọi công cụ nào, lượt nào bị từ chối.',
  durationMs: 7000,
  render: ({ progress }) => (
    <DemoWindow title="Kho skill AI · Tổng quan">
      <div className="grid grid-cols-4 gap-2 text-xs">
        {[['Người đã nối', '24'], ['Lượt gọi 7 ngày', '1.284'], ['So 7 ngày trước', '+18%'], ['Từ chối và lỗi', '9']].map(([k, v]) => (
          <div key={k} className="rounded-md border p-2">
            <p className="text-muted-foreground">{k}</p>
            <p className="text-lg font-semibold tabular-nums">{v}</p>
          </div>
        ))}
      </div>
      <div className="mt-3 flex h-[45%] items-end gap-1" aria-hidden>
        {[30, 42, 38, 55, 61, 48, 70, 66, 74, 58, 80, 77, 85, 90].map((h, i) => (
          <span key={i} className="flex-1 rounded-t bg-primary/70" style={{ height: `${h * Math.min(1, progress * 1.6)}%` }} />
        ))}
      </div>
    </DemoWindow>
  ),
}

const revokeKeys: DemoChapter = {
  id: 'revoke-keys',
  title: 'Thu hồi khóa tức thì',
  caption: 'Người nghỉ hoặc đổi việc: thu hồi một khóa, mọi khóa của một người hoặc cả lượt phát, có hiệu lực ngay.',
  durationMs: 7000,
  cursor: [
    { at: 0, x: 10, y: 35 },
    { at: 0.25, x: 8, y: 36, click: true },
    { at: 0.5, x: 86, y: 18, click: true },
    { at: 0.75, x: 62, y: 70, click: true },
  ],
  render: ({ progress, reduced }) => {
    const revoked = reached(progress, 0.78)
    return (
      <DemoWindow title="Khóa nhân sự" hint="Phòng Thu mua">
        <div className="flex justify-end">
          <Button size="sm" variant="destructive"><ShieldOff className="size-4" /> Thu hồi</Button>
        </div>
        <div className="mt-2 space-y-1.5 text-xs">
          {[['Nguyễn Văn A', 'Claude Desktop'], ['Trần Thị B', 'Cursor'], ['Lê Văn C', 'Claude Code']].map(([who, app], i) => (
            <Row key={who} className={cn(i === 0 && reached(progress, 0.25) && 'border-primary bg-accent')}>
              <Checkbox checked={i === 0 && reached(progress, 0.25)} aria-label={who} />
              <span>{who}</span>
              <span className="text-muted-foreground">{app}</span>
              <Badge variant={i === 0 && revoked ? 'destructive' : 'secondary'} className="ml-auto">
                {i === 0 && revoked ? 'Đã thu hồi' : 'Đang dùng'}
              </Badge>
            </Row>
          ))}
        </div>
        <DemoDialog open={reached(progress, 0.52) && !revoked} title="Thu hồi 1 khóa?" still={reduced}>
          <p className="mb-3 text-xs text-muted-foreground">Ứng dụng AI của người này mất quyền ngay ở lượt gọi kế tiếp.</p>
          <div className="flex justify-end"><Button size="sm" variant="destructive">Thu hồi</Button></div>
        </DemoDialog>
      </DemoWindow>
    )
  },
}

export const AI_SKILL_INTRO_CHAPTERS: readonly DemoChapter[] = [
  chooseDepartments,
  createSkillSet,
  writeSkill,
  assignReaders,
  issueKeys,
  connectAi,
  askAi,
  watchUsage,
  revokeKeys,
]
