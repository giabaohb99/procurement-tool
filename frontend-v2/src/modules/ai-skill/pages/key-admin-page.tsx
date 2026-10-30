import { BookOpen, KeyRound, Link2, Plus, ShieldOff } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { DataTable, createSelectionColumn, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useRowSelection } from '@/shared/hooks/use-row-selection'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { KEY_KIND, LIVE_KEY_STATES, upperFirst } from '../config/ai-skill-constants'
import { KeyStateBadge } from '../config/ai-skill-meta'
import { ConnectGuide } from '../components/connect-guide'
import { KeyIssueDialog } from '../components/key-issue-dialog'
import { useKeyAdminKeys, useKeyAdminMeta, useRevokeKeys } from '../hooks/use-ai-usage'
import type { AdminMcpKey } from '../types/ai-skill'

const ALL = 'all'

/**
 * G5 — khóa kết nối AI của nhân sự (doc 21 §6.2, K4 ai-CR-212). Bảng mọi khóa trong phạm vi người xem; phát hộ khóa
 * chỉ đọc cho người / cả phòng; tick chọn để thu hồi hàng loạt. Người phát không bao giờ thấy chuỗi khóa — chỉ 4 ký
 * tự cuối để đối chiếu.
 */
export function KeyAdminPage() {
  const meta = useKeyAdminMeta()
  const { data: departments } = useDepartments({ page_size: 500 })
  const [departmentId, setDepartmentId] = useUrlParamState('department', ALL)
  const [state, setState] = useUrlParamState('state', ALL)
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([departmentId, state])
  const [issueOpen, setIssueOpen] = useState(false)
  const [guideOpen, setGuideOpen] = useState(false)
  const selection = useRowSelection()
  const revoke = useRevokeKeys()

  const canRead = meta.data?.can_read ?? false
  const canCreate = meta.data?.can_create ?? false
  const canDelete = meta.data?.can_delete ?? false

  const params = {
    department_id: departmentId === ALL ? undefined : Number(departmentId),
    state: state === ALL ? undefined : Number(state),
    page,
    size: pageSize,
  }
  const { data, isLoading, isError } = useKeyAdminKeys(params, canRead)
  const rows = data?.items
  const idsOnPage = useMemo(() => (rows ?? []).map((k) => k.id), [rows])
  //  Khóa đã thu hồi / hết hạn không còn gì để thu hồi — đếm riêng số khóa CÒN HIỆU LỰC trong lượt chọn để hộp xác nhận
  //  nói đúng số sẽ đổi.
  const selectedLive = (rows ?? []).filter(
    (k) => selection.selectedIds.has(k.id) && LIVE_KEY_STATES.includes(k.state),
  )

  const { selectedIds, toggleRow, toggleAllOnPage } = selection
  const columns = useMemo<DataTableColumn<AdminMcpKey>[]>(() => {
    const allOnPage = idsOnPage.length > 0 && idsOnPage.every((id) => selectedIds.has(id))
    const someOnPage = idsOnPage.some((id) => selectedIds.has(id))
    const base: DataTableColumn<AdminMcpKey>[] = [
      {
        key: 'owner',
        header: 'Người',
        width: 200,
        hideable: false,
        cell: (k) => <span className="font-medium text-navy dark:text-foreground">{k.owner_label || `#${k.user_id}`}</span>,
      },
      { key: 'department', header: 'Phòng', width: 180, cell: (k) => <span className="text-muted-foreground">{k.department || '—'}</span> },
      {
        key: 'name',
        header: 'Tên khóa',
        width: 200,
        cell: (k) => (
          <span>
            {k.name || '(không tên)'}{' '}
            <span className={cn('text-xs text-muted-foreground', k.kind !== KEY_KIND.oauth && 'font-mono')}>
              {k.kind === KEY_KIND.oauth ? k.kind_label || 'Kết nối OAuth' : k.hint}
            </span>
          </span>
        ),
      },
      { key: 'scope', header: 'Mức', width: 100, cell: (k) => upperFirst(k.scope_label) },
      { key: 'expires_at', header: 'Hết hạn', width: 150, cell: (k) => <span className="whitespace-nowrap">{formatDateTime(k.expires_at)}</span> },
      {
        key: 'last_used_at',
        header: 'Dùng lần cuối',
        width: 150,
        cell: (k) => (
          <span className="whitespace-nowrap text-muted-foreground">{k.last_used_at ? formatDateTime(k.last_used_at) : 'Chưa dùng'}</span>
        ),
      },
      { key: 'state', header: 'Trạng thái', width: 120, cell: (k) => <KeyStateBadge state={k.state} label={k.state_label} /> },
      { key: 'issued_by', header: 'Người phát', width: 160, defaultHidden: true, cell: (k) => k.issued_by_label || 'Tự tạo' },
    ]
    if (!canDelete) return base
    return [
      createSelectionColumn<AdminMcpKey>({
        getRowId: (k) => k.id,
        selectedIds,
        onToggleRow: toggleRow,
        onToggleAllOnPage: () => toggleAllOnPage(idsOnPage),
        allOnPageSelected: allOnPage,
        someOnPageSelected: someOnPage && !allOnPage,
        getRowLabel: (k) => `khóa ${k.name || k.hint} của ${k.owner_label}`,
      }),
      ...base,
    ]
  }, [canDelete, idsOnPage, selectedIds, toggleRow, toggleAllOnPage])

  async function handleRevoke() {
    if (selectedLive.length === 0) return
    const ok = await confirm({
      title: 'Thu hồi khóa',
      message: `Thu hồi ${selectedLive.length} khóa đang hiệu lực? Ứng dụng AI đang dùng các khóa này sẽ không tra được ERP nữa.`,
      confirmLabel: `Thu hồi ${selectedLive.length} khóa`,
    })
    if (!ok) return
    try {
      await revoke.mutateAsync({ key_ids: selectedLive.map((k) => k.id) })
      selection.clear()
    } catch {
      //  Toast lỗi tự động (chủ khóa ngoài phạm vi → không thu hồi lẻ một phần).
    }
  }

  if (meta.data && !canRead) {
    return (
      <PageContainer>
        <ErrorState title="Không có quyền" description="Bạn chưa được giao quản lý khóa kết nối AI của nhân sự." />
      </PageContainer>
    )
  }

  const filtering = departmentId !== ALL || state !== ALL

  return (
    <PageContainer fill>
      <PageHeader
        title="Kết nối"
        description="Khóa để AI riêng của nhân viên (Claude, ChatGPT…) tra cứu ERP đúng quyền của họ. Phát hộ cho cả phòng, thu hồi khi nghỉ việc."
        actions={
          <>
            {canDelete && selectedLive.length > 0 && (
              <Button variant="outline" onClick={() => void handleRevoke()} disabled={revoke.isPending}>
                <ShieldOff className="size-4" />
                Thu hồi ({selectedLive.length})
              </Button>
            )}
            <Button variant="outline" className="xl:hidden" onClick={() => setGuideOpen(true)}>
              <BookOpen className="size-4" />
              Hướng dẫn kết nối
            </Button>
            {canCreate && meta.data && (
              <Button onClick={() => setIssueOpen(true)}>
                <Plus className="size-4" />
                Phát khóa
              </Button>
            )}
          </>
        }
      />
      <div className="flex min-h-0 flex-1 flex-col gap-4 xl:flex-row">
        <Card className="flex min-h-0 min-w-0 flex-1 flex-col p-4">
          <DataTable
            fillHeight
            columns={columns}
            rows={rows}
            getRowId={(k) => k.id}
            isLoading={isLoading || meta.isLoading}
            isError={isError}
            emptyMessage={
              filtering ? 'Không có khóa nào khớp bộ lọc.' : 'Chưa có khóa nào. Bấm Phát khóa để cấp cho một phòng.'
            }
            storageKey="ai-skill.keys"
            pagination={{
              page,
              pageSize,
              total: data?.total ?? 0,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
              unitLabel: 'khóa',
            }}
            toolbar={
              <>
                <KeyRound className="hidden size-4 text-muted-foreground md:block" />
                <Select value={departmentId} onValueChange={setDepartmentId}>
                  <SelectTrigger className="w-48" aria-label="Lọc phòng ban">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Tất cả phòng ban</SelectItem>
                    {(departments?.items ?? []).map((d) => (
                      <SelectItem key={d.id} value={String(d.id)}>
                        {d.name}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <Select value={state} onValueChange={setState}>
                  <SelectTrigger className="w-44" aria-label="Lọc trạng thái">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value={ALL}>Tất cả trạng thái</SelectItem>
                    {(meta.data?.states ?? []).map((s) => (
                      <SelectItem key={s.value} value={String(s.value)}>
                        {s.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </>
            }
          />
        </Card>
        {/*  bao-CR-638: hướng dẫn nối dùng chung với AI của tôi, nhưng KHÔNG có khóa — khóa mỗi người tự lấy. Màn hẹp thì
            cột này chiếm hết chỗ của bảng (bảng co về 0), nên dưới xl chỉ mở bằng nút ở đầu trang. */}
        <Card className="hidden min-h-0 p-4 xl:block xl:w-96 xl:shrink-0 xl:overflow-y-auto">
          <GuidePanel />
        </Card>
      </div>
      <Dialog open={guideOpen} onOpenChange={setGuideOpen}>
        <DialogContent className="max-h-[92dvh] overflow-y-auto sm:max-w-2xl">
          <DialogHeader>
            <DialogTitle>Hướng dẫn kết nối</DialogTitle>
            <DialogDescription>Cùng nội dung trang công khai gửi cho nhân viên — không có khóa.</DialogDescription>
          </DialogHeader>
          {guideOpen && <GuidePanel />}
        </DialogContent>
      </Dialog>
      {meta.data && <KeyIssueDialog open={issueOpen} onOpenChange={setIssueOpen} meta={meta.data} />}
    </PageContainer>
  )
}

function GuidePanel() {
  return (
    <div className="space-y-3">
      <SectionHeading>Hướng dẫn kết nối</SectionHeading>
      <p className="text-sm text-muted-foreground">
        Gửi nhân viên link hướng dẫn (không cần đăng nhập). Khóa mỗi người tự lấy ở Trang cá nhân → AI của tôi, hoặc
        nhận khóa bạn phát hộ.
      </p>
      <ConnectGuide source="private" footer={<CopyGuideLinkButton />} />
    </div>
  )
}

/** Link trang công khai /connect-ai — gửi cho nhân viên; trang đó không bao giờ có khóa. */
function CopyGuideLinkButton() {
  async function copy() {
    try {
      if (!navigator.clipboard) throw new Error('clipboard unavailable')
      await navigator.clipboard.writeText(`${window.location.origin}${appRoutes.connectAi}`)
      toast.success('Đã chép link hướng dẫn.')
    } catch {
      toast.error('Không chép được link — mở trang Hướng dẫn kết nối rồi chép địa chỉ trên trình duyệt.')
    }
  }
  return (
    <Button type="button" variant="outline" size="sm" onClick={() => void copy()}>
      <Link2 className="size-4" />
      Sao chép link hướng dẫn
    </Button>
  )
}
