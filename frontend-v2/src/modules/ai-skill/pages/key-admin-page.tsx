import { BookOpen, Link2, Plus, Search, ShieldOff } from 'lucide-react'
import { useMemo, useState } from 'react'
import { toast } from 'sonner'

import { appConfig } from '@/core/config/app-config'
import { useDepartments } from '@/modules/hr/hooks/use-departments'
import { DataTable, createSelectionColumn, type DataTableColumn } from '@/shared/data-table'
import { usePageResetOnFilterChange } from '@/shared/hooks/use-page-reset-on-filter-change'
import { useRowSelection } from '@/shared/hooks/use-row-selection'
import { useUrlParamState } from '@/shared/hooks/use-url-param-state'
import { useUrlSearchParam } from '@/shared/hooks/use-url-search-param'
import { appRoutes } from '@/shared/constants/app-routes'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { Card } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/shared/ui/select'
import { formatDateTime } from '@/shared/utils/format-date'
import { LIVE_KEY_STATES, upperFirst } from '../config/ai-skill-constants'
import { KeyStateBadge } from '../config/ai-skill-meta'
import { ConnectGuide } from '../components/connect-guide'
import { KeyIssueDialog } from '../components/key-issue-dialog'
import { useKeyAdminKeys, useKeyAdminMeta, useRevokeKeys } from '../hooks/use-ai-usage'
import {
  CONNECTION_TYPE_LABEL,
  redirectHost,
  toConnectionRow,
  type ConnectionRow,
} from '../utils/ai-row-mappers'

const ALL = 'all'

/**
 * G5 — Kết nối (tên cũ: Khóa nhân sự; doc 21 §6.2, K4 ai-CR-212, nâng cấp bao-CR-696). Mỗi dòng là một kết nối AI
 * riêng của nhân sự: ai · nối bằng khóa riêng hay OAuth · ứng dụng nào (tên + nơi quay về) · dùng lần cuối · trạng
 * thái. Phát hộ khóa chỉ đọc cho người / cả phòng; tick chọn để thu hồi hàng loạt. Người phát không bao giờ thấy chuỗi
 * khóa — chỉ 4 ký tự cuối để đối chiếu.
 *
 * Trường mới đọc qua `toConnectionRow` (một chỗ, hợp đồng còn là bản đề nghị); máy chủ cũ thì lùi về trường sẵn có.
 */
export function KeyAdminPage() {
  const meta = useKeyAdminMeta()
  const { data: departments } = useDepartments({ page_size: 500 })
  const [departmentId, setDepartmentId] = useUrlParamState('department', ALL)
  const [state, setState] = useUrlParamState('state', ALL)
  //  Tìm theo tên / email / mã NV — máy chủ lọc (`q`). Đặt lại trang theo giá trị ĐÃ HOÃN, không theo từng ký tự gõ.
  const { value: keyword, setValue: setKeyword, debouncedValue: q } = useUrlSearchParam('q')
  const [pageSize, setPageSize] = useState<number>(appConfig.defaultPageSize)
  const [page, setPage] = usePageResetOnFilterChange([departmentId, state, q])
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
    q: q.trim() || undefined,
    page,
    size: pageSize,
  }
  const { data, isLoading, isError } = useKeyAdminKeys(params, canRead)
  const rows = useMemo(() => data?.items.map(toConnectionRow), [data])
  const idsOnPage = useMemo(() => (rows ?? []).map((k) => k.id), [rows])
  //  Khóa đã thu hồi / hết hạn không còn gì để thu hồi — đếm riêng số khóa CÒN HIỆU LỰC trong lượt chọn để hộp xác nhận
  //  nói đúng số sẽ đổi.
  const selectedLive = (rows ?? []).filter(
    (k) => selection.selectedIds.has(k.id) && LIVE_KEY_STATES.includes(k.state),
  )

  const { selectedIds, toggleRow, toggleAllOnPage } = selection
  const columns = useMemo<DataTableColumn<ConnectionRow>[]>(() => {
    const allOnPage = idsOnPage.length > 0 && idsOnPage.every((id) => selectedIds.has(id))
    const someOnPage = idsOnPage.some((id) => selectedIds.has(id))
    const base: DataTableColumn<ConnectionRow>[] = [
      {
        key: 'person',
        header: 'Người',
        width: 220,
        hideable: false,
        wrap: true,
        cell: (k) => {
          const sub = [k.employeeCode, k.email].filter(Boolean).join(' · ')
          return (
            <div className="min-w-0">
              <div className="font-medium text-navy dark:text-foreground">{k.person || '(không rõ)'}</div>
              {sub && (
                <div className="truncate text-xs text-muted-foreground" title={sub}>
                  {sub}
                </div>
              )}
            </div>
          )
        },
      },
      {
        key: 'department',
        header: 'Phòng',
        width: 160,
        cell: (k) => (k.department ? <span className="text-muted-foreground">{k.department}</span> : <span>—</span>),
      },
      {
        key: 'connection_type',
        header: 'Cách nối',
        width: 110,
        cell: (k) => (
          <Badge variant={k.connectionType === 'oauth' ? 'secondary' : 'outline'}>{CONNECTION_TYPE_LABEL[k.connectionType]}</Badge>
        ),
      },
      {
        key: 'app',
        header: 'Ứng dụng',
        width: 220,
        wrap: true,
        cell: (k) => {
          const host = redirectHost(k.appRedirectUri)
          //  Gạch thật bằng <span>: DataTable nuốt ô trả đúng chuỗi '—' (docs/ui/table.md §1).
          if (!k.appName && !host) return <span className="text-muted-foreground">—</span>
          return (
            <div className="min-w-0">
              <div>{k.appName || '(không tên)'}</div>
              {host && (
                <div className="truncate text-xs text-muted-foreground" title={k.appRedirectUri}>
                  {host}
                </div>
              )}
            </div>
          )
        },
      },
      {
        key: 'name',
        header: 'Tên khóa',
        width: 180,
        cell: (k) => (
          <span>
            {k.keyName || '(không tên)'}{' '}
            {k.connectionType === 'key' && <span className="font-mono text-xs text-muted-foreground">{k.hint}</span>}
          </span>
        ),
      },
      { key: 'scope', header: 'Mức', width: 100, defaultHidden: true, cell: (k) => upperFirst(k.source.scope_label) },
      {
        key: 'expires_at',
        header: 'Hết hạn',
        width: 150,
        defaultHidden: true,
        cell: (k) => <span className="whitespace-nowrap">{formatDateTime(k.source.expires_at)}</span>,
      },
      {
        key: 'last_used_at',
        header: 'Dùng lần cuối',
        width: 150,
        cell: (k) => (
          <span className="whitespace-nowrap text-muted-foreground">{k.lastUsedAt ? formatDateTime(k.lastUsedAt) : 'Chưa dùng'}</span>
        ),
      },
      { key: 'state', header: 'Trạng thái', width: 120, cell: (k) => <KeyStateBadge state={k.state} label={k.stateLabel} /> },
      { key: 'issued_by', header: 'Người phát', width: 160, defaultHidden: true, cell: (k) => k.source.issued_by_label || 'Tự tạo' },
    ]
    if (!canDelete) return base
    return [
      createSelectionColumn<ConnectionRow>({
        getRowId: (k) => k.id,
        selectedIds,
        onToggleRow: toggleRow,
        onToggleAllOnPage: () => toggleAllOnPage(idsOnPage),
        allOnPageSelected: allOnPage,
        someOnPageSelected: someOnPage && !allOnPage,
        getRowLabel: (k) => `khóa ${k.keyName || k.hint} của ${k.person}`,
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

  const filtering = departmentId !== ALL || state !== ALL || q.trim() !== ''

  return (
    <PageContainer fill>
      <PageHeader
        title="Kết nối"
        description="AI riêng của nhân viên (Claude, ChatGPT…) đang nối vào ERP: bằng khóa riêng hay OAuth, ứng dụng nào, dùng lần cuối khi nào. Phát khóa hộ cả phòng, thu hồi khi nghỉ việc."
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
              filtering ? 'Không có kết nối nào khớp bộ lọc.' : 'Chưa có kết nối nào. Bấm Phát khóa để cấp cho một phòng.'
            }
            //  Khóa lưu bố cục MỚI (bao-CR-696): bộ cột đổi hẳn, giữ khóa cũ thì bố cục đã lưu của màn Khóa nhân sự thắng
            //  và cột Cách nối / Ứng dụng không hiện cho người từng chỉnh cột (docs/ui/table.md §4).
            storageKey="ai.connections"
            pagination={{
              page,
              pageSize,
              total: data?.total ?? 0,
              onPageChange: setPage,
              onPageSizeChange: setPageSize,
              unitLabel: 'kết nối',
            }}
            toolbar={
              <>
                <div className="relative min-w-48 flex-1 md:max-w-xs">
                  <Search className="absolute top-1/2 left-3 size-4 -translate-y-1/2 text-muted-foreground" />
                  <Input
                    className="pl-9"
                    placeholder="Tìm tên, email, mã NV"
                    aria-label="Tìm theo tên, email, mã nhân viên"
                    value={keyword}
                    maxLength={80}
                    onChange={(e) => setKeyword(e.target.value)}
                  />
                </div>
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
