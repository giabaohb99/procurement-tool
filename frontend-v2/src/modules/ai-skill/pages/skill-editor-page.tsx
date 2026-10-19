import { Bold, Heading2, List, ListOrdered, Rocket, Save, Table2 } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useBlocker, useNavigate, useParams } from 'react-router-dom'

import { usePermission } from '@/core/authorization/use-permission'
import { MarkdownMessage } from '@/modules/assistant/components/markdown-message'
import { AuditTimeline } from '@/shared/audit'
import { appRoutes } from '@/shared/constants/app-routes'
import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader } from '@/shared/ui/card'
import { confirm } from '@/shared/ui/confirm-dialog'
import { DetailPageHeader } from '@/shared/ui/detail-page-header'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/shared/ui/dialog'
import { ErrorState } from '@/shared/ui/error-state'
import { Input } from '@/shared/ui/input'
import { Label } from '@/shared/ui/label'
import { PageContainer } from '@/shared/ui/page-container'
import { RequiredMark } from '@/shared/ui/required-mark'
import { ScrollableTabsList } from '@/shared/ui/scrollable-tabs-list'
import { SectionHeading } from '@/shared/ui/section-heading'
import { Skeleton } from '@/shared/ui/skeleton'
import { TAB_TRIGGER_UNDERLINE } from '@/shared/ui/tab-underline'
import { Tabs, TabsContent, TabsTrigger } from '@/shared/ui/tabs'
import { Textarea } from '@/shared/ui/textarea'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'
import { ACCESS_TARGET, BODY_MAX_CHARS, NOTE_MAX, SUMMARY_MAX, TITLE_MAX } from '../config/ai-skill-constants'
import { SkillStatusBadge } from '../config/ai-skill-meta'
import { SkillAccessTab } from '../components/skill-access-tab'
import { SkillFilesCard } from '../components/skill-files-card'
import { SkillVersionsPanel } from '../components/skill-versions-panel'
import { usePublishSkill, useSkill, useUpdateSkill } from '../hooks/use-ai-skill'
import type { SkillDetail } from '../types/ai-skill'

interface Draft {
  title: string
  summary: string
  body: string
}

function draftOf(skill: SkillDetail): Draft {
  return { title: skill.title, summary: skill.summary, body: skill.draft_body_md }
}

/** Mẫu chèn của thanh công cụ gọn — chèn ở con trỏ, không cần thư viện soạn thảo. */
const SNIPPETS = {
  heading: '\n## Tiêu đề mục\n',
  bold: '**chữ đậm**',
  list: '\n- Ý thứ nhất\n- Ý thứ hai\n',
  ordered: '\n1. Bước một\n2. Bước hai\n',
  table: '\n| Cột A | Cột B |\n| --- | --- |\n| ... | ... |\n',
} as const

/**
 * G4 — soạn một skill (doc 21 §6.2). Hai cột: trái soạn Markdown, phải «Xem như AI đọc». Lưu là lưu NHÁP (Ctrl+S);
 * AI chỉ đọc bản đã XUẤT BẢN, nên nháp sửa thoải mái không ảnh hưởng ai. Xuất bản cần quyền duyệt và tóm tắt cho AI.
 */
export function SkillEditorPage() {
  const { id: rawId } = useParams()
  const skillId = Number(rawId)
  const validId = Number.isInteger(skillId) && skillId > 0
  const navigate = useNavigate()
  const { can } = usePermission()
  const canWrite = can('ai_skill', 'write')
  const canPublish = can('ai_skill', 'approve')
  const { data: skill, isLoading, isError } = useSkill(validId ? skillId : 0)

  if (!validId || isError) {
    return (
      <PageContainer>
        <ErrorState title="Không mở được skill" description="Skill này không tồn tại hoặc bạn không có quyền xem.">
          <Button variant="outline" onClick={() => navigate(appRoutes.aiSkill.root)}>
            Về danh sách bộ skill
          </Button>
        </ErrorState>
      </PageContainer>
    )
  }
  if (isLoading || !skill) {
    return (
      <PageContainer>
        <Skeleton className="h-96 w-full" />
      </PageContainer>
    )
  }
  //  `key` theo id: đổi sang skill khác thì dựng lại bộ soạn, không mang nháp của skill trước sang.
  return <SkillEditor key={skill.id} skill={skill} canWrite={canWrite} canPublish={canPublish} />
}

function SkillEditor({ skill, canWrite, canPublish }: { skill: SkillDetail; canWrite: boolean; canPublish: boolean }) {
  const update = useUpdateSkill(skill.id)
  const publish = usePublishSkill(skill.id)
  const [saved, setSaved] = useState<Draft>(() => draftOf(skill))
  const [draft, setDraft] = useState<Draft>(() => draftOf(skill))
  const [tab, setTab] = useState('content')
  const [publishOpen, setPublishOpen] = useState(false)
  const bodyRef = useRef<HTMLTextAreaElement>(null)
  const saving = useRef(false)

  const dirty = draft.title !== saved.title || draft.summary !== saved.summary || draft.body !== saved.body
  const summaryMissing = draft.summary.trim() === ''

  async function save(silent = false): Promise<boolean> {
    if (!canWrite) return false
    if (!dirty) return true
    if (saving.current) return false
    saving.current = true
    const snapshot = draft
    try {
      await update.mutateAsync({ body: { title: snapshot.title, summary: snapshot.summary, body_md: snapshot.body }, silent })
      setSaved(snapshot)
      return true
    } catch {
      return false
    } finally {
      saving.current = false
    }
  }

  //  Ctrl+S / Cmd+S lưu nháp thay vì mở hộp «Lưu trang» của trình duyệt.
  const saveRef = useRef(save)
  useEffect(() => {
    saveRef.current = save
  })
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === 's') {
        event.preventDefault()
        void saveRef.current()
      }
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  //  Cảnh báo rời trang khi còn sửa chưa lưu: đóng tab / tải lại (beforeunload) và bấm sang màn khác (useBlocker).
  useEffect(() => {
    if (!dirty) return
    const onBeforeUnload = (event: BeforeUnloadEvent) => event.preventDefault()
    window.addEventListener('beforeunload', onBeforeUnload)
    return () => window.removeEventListener('beforeunload', onBeforeUnload)
  }, [dirty])
  const blocker = useBlocker(({ currentLocation, nextLocation }) => dirty && currentLocation.pathname !== nextLocation.pathname)
  useEffect(() => {
    if (blocker.state !== 'blocked') return
    void confirm({
      title: 'Rời trang khi chưa lưu?',
      message: 'Nội dung đã sửa chưa được lưu nháp sẽ mất.',
      confirmLabel: 'Rời trang',
    }).then((ok) => (ok ? blocker.proceed() : blocker.reset()))
  }, [blocker])

  function insert(snippet: string) {
    const el = bodyRef.current
    if (!el) return
    const start = el.selectionStart ?? draft.body.length
    const end = el.selectionEnd ?? start
    const next = draft.body.slice(0, start) + snippet + draft.body.slice(end)
    if (next.length > BODY_MAX_CHARS) return
    setDraft({ ...draft, body: next })
    requestAnimationFrame(() => {
      el.focus()
      el.setSelectionRange(start + snippet.length, start + snippet.length)
    })
  }

  async function handlePublish(note: string) {
    //  Xuất bản đọc bản NHÁP đã lưu ở máy chủ — lưu trước, kẻo xuất bản ra bản cũ hơn cái đang thấy trên màn.
    if (!(await save(true))) return
    try {
      await publish.mutateAsync(note.trim())
      setPublishOpen(false)
    } catch {
      //  Toast lỗi tự động: in nguyên câu backend (thiếu tóm tắt, nội dung rỗng…).
    }
  }

  return (
    <PageContainer>
      <DetailPageHeader
        backTo={appRoutes.aiSkill.setDetail(skill.skill_set_id)}
        backLabel="Về bộ skill"
        title={draft.title || skill.slug}
        badges={
          <>
            <SkillStatusBadge status={skill.status} label={skill.status_label} />
            {skill.version_no > 0 && (
              <span className="text-xs text-muted-foreground">
                AI đang đọc v{skill.version_no} · {formatDateTime(skill.published_at)}
              </span>
            )}
            {dirty ? (
              <span className="text-xs text-warning">Có sửa chưa lưu</span>
            ) : (
              skill.has_unpublished_changes && <span className="text-xs text-warning">Nháp mới hơn bản AI đang đọc</span>
            )}
          </>
        }
        primaryActions={
          canWrite && (
            <>
              <Button type="button" variant="outline" onClick={() => void save()} disabled={!dirty || update.isPending}>
                <Save className="size-4" />
                Lưu nháp
              </Button>
              {canPublish && (
                <Button type="button" onClick={() => setPublishOpen(true)} disabled={publish.isPending}>
                  <Rocket className="size-4" />
                  Xuất bản
                </Button>
              )}
            </>
          )
        }
      />

      <Tabs value={tab} onValueChange={setTab} className="space-y-4">
        <ScrollableTabsList value={tab}>
          <TabsTrigger value="content" className={TAB_TRIGGER_UNDERLINE}>
            Nội dung
          </TabsTrigger>
          <TabsTrigger value="files" className={TAB_TRIGGER_UNDERLINE}>
            Tệp đi kèm ({skill.files.length})
          </TabsTrigger>
          <TabsTrigger value="versions" className={TAB_TRIGGER_UNDERLINE}>
            Phiên bản
          </TabsTrigger>
          <TabsTrigger value="access" className={TAB_TRIGGER_UNDERLINE}>
            Ai được đọc
          </TabsTrigger>
          <TabsTrigger value="history" className={TAB_TRIGGER_UNDERLINE}>
            Lịch sử
          </TabsTrigger>
        </ScrollableTabsList>

        <TabsContent value="content" className="space-y-4">
          <Card>
            <CardContent className="grid gap-4 pt-6 md:grid-cols-[minmax(0,1fr)_minmax(0,2fr)]">
              <div className="space-y-1.5">
                <Label htmlFor="skill-editor-title">Tiêu đề</Label>
                <Input
                  id="skill-editor-title"
                  value={draft.title}
                  maxLength={TITLE_MAX}
                  readOnly={!canWrite}
                  onChange={(e) => setDraft({ ...draft, title: e.target.value })}
                />
                <p className="font-mono text-xs text-muted-foreground">Tên AI gọi: {skill.slug}</p>
              </div>
              <div className="space-y-1.5">
                <Label htmlFor="skill-editor-summary">
                  Tóm tắt cho AI <RequiredMark hint="Bắt buộc trước khi xuất bản" />
                </Label>
                <Textarea
                  id="skill-editor-summary"
                  rows={2}
                  value={draft.summary}
                  readOnly={!canWrite}
                  aria-invalid={summaryMissing}
                  onChange={(e) => setDraft({ ...draft, summary: e.target.value.slice(0, SUMMARY_MAX) })}
                  placeholder="Một câu nói KHI NÀO dùng skill này, ví dụ: Dùng khi người dùng hỏi cách lập yêu cầu mua hàng."
                />
                <p className="flex justify-between gap-2 text-xs text-muted-foreground">
                  <span>AI đọc câu này để quyết định có mở skill hay không — nói rõ khi nào dùng.</span>
                  <span className={cn('shrink-0 tabular-nums', draft.summary.length >= SUMMARY_MAX && 'text-warning')}>
                    {draft.summary.length}/{SUMMARY_MAX}
                  </span>
                </p>
              </div>
            </CardContent>
          </Card>

          <div className="grid gap-4 lg:grid-cols-2">
            <Card className="min-w-0">
              <CardHeader className="flex flex-row flex-wrap items-center justify-between gap-2">
                <SectionHeading>Nội dung (Markdown)</SectionHeading>
                {canWrite && (
                  <div className="flex gap-1" role="toolbar" aria-label="Chèn định dạng">
                    <ToolbarButton label="Chèn tiêu đề" onClick={() => insert(SNIPPETS.heading)} icon={Heading2} />
                    <ToolbarButton label="Chèn chữ đậm" onClick={() => insert(SNIPPETS.bold)} icon={Bold} />
                    <ToolbarButton label="Chèn danh sách" onClick={() => insert(SNIPPETS.list)} icon={List} />
                    <ToolbarButton label="Chèn danh sách đánh số" onClick={() => insert(SNIPPETS.ordered)} icon={ListOrdered} />
                    <ToolbarButton label="Chèn bảng" onClick={() => insert(SNIPPETS.table)} icon={Table2} />
                  </div>
                )}
              </CardHeader>
              <CardContent className="space-y-1">
                <Textarea
                  ref={bodyRef}
                  aria-label="Nội dung skill"
                  className="min-h-[28rem] font-mono text-xs leading-5"
                  value={draft.body}
                  readOnly={!canWrite}
                  onChange={(e) => setDraft({ ...draft, body: e.target.value.slice(0, BODY_MAX_CHARS) })}
                  placeholder={'# Tên quy trình\n\nViết như hướng dẫn một nhân viên mới: các bước, mẫu, lưu ý.'}
                />
                <p className="text-right text-xs text-muted-foreground tabular-nums">
                  {draft.body.length.toLocaleString('vi-VN')}/{BODY_MAX_CHARS.toLocaleString('vi-VN')} ký tự · Ctrl+S lưu nháp
                </p>
              </CardContent>
            </Card>

            <Card className="min-w-0">
              <CardHeader>
                <SectionHeading>Xem như AI đọc</SectionHeading>
              </CardHeader>
              <CardContent className="max-h-[32rem] overflow-y-auto text-sm">
                {draft.body.trim() ? (
                  <MarkdownMessage content={draft.body} />
                ) : (
                  <p className="text-muted-foreground">Chưa có nội dung.</p>
                )}
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="files">
          <SkillFilesCard skillId={skill.id} files={skill.files} canWrite={canWrite} />
        </TabsContent>
        <TabsContent value="versions">
          <SkillVersionsPanel skillId={skill.id} draftBody={draft.body} />
        </TabsContent>
        <TabsContent value="access" className="space-y-3">
          <p className="text-sm text-muted-foreground">
            Mặc định skill theo quyền của bộ. Gán riêng ở đây là THU HẸP: có dòng riêng thì chỉ những đối tượng này đọc
            được skill, quyền của bộ không áp nữa.
          </p>
          <SkillAccessTab targetKind={ACCESS_TARGET.skill} targetId={skill.id} canWrite={canWrite} />
        </TabsContent>
        <TabsContent value="history">
          <AuditTimeline entity="ai_skill" entityId={skill.id} />
        </TabsContent>
      </Tabs>

      <PublishDialog
        open={publishOpen}
        onOpenChange={setPublishOpen}
        summaryMissing={summaryMissing}
        dirty={dirty}
        pending={publish.isPending || update.isPending}
        nextVersion={skill.version_no + 1}
        onPublish={(note) => void handlePublish(note)}
      />
    </PageContainer>
  )
}

function ToolbarButton({ label, onClick, icon: Icon }: { label: string; onClick: () => void; icon: typeof Bold }) {
  return (
    <Button type="button" variant="ghost" size="sm" className="size-8 p-0" title={label} aria-label={label} onClick={onClick}>
      <Icon className="size-4" />
    </Button>
  )
}

function PublishDialog({
  open,
  onOpenChange,
  summaryMissing,
  dirty,
  pending,
  nextVersion,
  onPublish,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  summaryMissing: boolean
  dirty: boolean
  pending: boolean
  nextVersion: number
  onPublish: (note: string) => void
}) {
  const [note, setNote] = useState('')
  return (
    <Dialog
      open={open}
      onOpenChange={(next) => {
        if (!next) setNote('')
        onOpenChange(next)
      }}
    >
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Xuất bản phiên bản {nextVersion}</DialogTitle>
          <DialogDescription>
            AI của người được gán sẽ đọc bản này từ lượt hỏi kế tiếp. Bản cũ vẫn giữ trong tab Phiên bản.
          </DialogDescription>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          {summaryMissing && (
            <p className="rounded-md border border-warning/40 bg-warning/10 p-2 text-xs">
              Chưa có Tóm tắt cho AI — máy chủ sẽ từ chối xuất bản. Viết một câu nói khi nào dùng skill này trước.
            </p>
          )}
          {dirty && <p className="text-xs text-muted-foreground">Phần sửa chưa lưu sẽ được lưu nháp trước khi xuất bản.</p>}
          <div className="space-y-1">
            <Label htmlFor="skill-publish-note">Ghi chú thay đổi</Label>
            <Textarea
              id="skill-publish-note"
              rows={3}
              value={note}
              onChange={(e) => setNote(e.target.value.slice(0, NOTE_MAX))}
              placeholder="Ví dụ: Thêm bước kiểm tra công nợ trước khi lập phiếu"
            />
          </div>
        </div>
        <DialogFooter>
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Hủy
          </Button>
          <Button type="button" onClick={() => onPublish(note)} disabled={pending}>
            Xuất bản
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}
