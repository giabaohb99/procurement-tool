import { AtSign, Ban, CircleAlert, CircleCheck, Pencil, Plus } from 'lucide-react'
import { useState } from 'react'

import { usePermission } from '@/core/authorization/use-permission'
import { DataTable, type DataTableColumn } from '@/shared/data-table'
import { Badge } from '@/shared/ui/badge'
import { Button } from '@/shared/ui/button'
import { ConfirmIconButton } from '@/shared/ui/confirm-icon-button'
import { PageContainer } from '@/shared/ui/page-container'
import { PageHeader } from '@/shared/ui/page-header'
import { MailboxFormDialog } from '../components/mailbox-form-dialog'
import { useMailboxActions, useMailboxes } from '../hooks/use-mailboxes'
import type { Mailbox } from '../types/mailbox'

/**
 * DANH MỤC HỘP THƯ GỬI (26/08/2026).
 *
 * Trả lời hai câu, và cột bảng bám đúng hai câu đó: **địa chỉ nào gửi được** và
 * **ai được gửi danh nghĩa nó**. Hộp thư khai thiếu SMTP vẫn nằm trong bảng
 * nhưng phải mang dấu đỏ — giấu đi thì người được cấp mở hộp thoại Ban hành
 * không thấy hộp thư của mình và không ai biết vì sao.
 */
export function MailboxListPage() {
  const { can } = usePermission()
  const canCreate = can('mailbox', 'create')
  const canWrite = can('mailbox', 'write')
  const canDelete = can('mailbox', 'delete')

  const { data: mailboxes = [], isLoading, isError, refetch } = useMailboxes()
  const { save, clearPassword, deactivate } = useMailboxActions()

  const [open, setOpen] = useState(false)
  const [editing, setEditing] = useState<Mailbox | undefined>(undefined)

  const openForm = (mailbox?: Mailbox) => {
    setEditing(mailbox)
    setOpen(true)
  }

  const columns: DataTableColumn<Mailbox>[] = [
    {
      key: 'email',
      header: 'Địa chỉ gửi',
      width: 260,
      cell: (row) => (
        <div className="flex items-center gap-2">
          <AtSign className="size-4 shrink-0 text-muted-foreground" />
          <div className="min-w-0">
            <p className="truncate font-medium">{row.email}</p>
            <p className="truncate text-xs text-muted-foreground">
              {row.display_name || row.name}
            </p>
          </div>
        </div>
      ),
    },
    { key: 'code', header: 'Mã', width: 90, cell: (row) => row.code },
    {
      key: 'ready',
      header: 'Gửi được',
      width: 150,
      cell: (row) =>
        row.ready ? (
          <Badge variant="secondary" className="gap-1">
            <CircleCheck className="size-3.5" />
            Sẵn sàng
          </Badge>
        ) : (
          //  Nói RÕ thiếu gì. "Chưa sẵn sàng" trơ trọi thì người khai phải đoán
          //  giữa máy chủ, tài khoản và mật khẩu.
          <Badge variant="destructive" className="gap-1">
            <CircleAlert className="size-3.5" />
            {row.smtp_host ? 'Thiếu mật khẩu' : 'Thiếu máy chủ'}
          </Badge>
        ),
    },
    {
      key: 'employee_ids',
      header: 'Người được dùng',
      width: 140,
      cell: (row) => (
        <span className={row.employee_ids.length === 0 ? 'text-muted-foreground' : ''}>
          {row.employee_ids.length === 0
            ? 'Chưa cấp cho ai'
            : `${row.employee_ids.length} người`}
        </span>
      ),
    },
    {
      key: 'smtp_host',
      header: 'Máy chủ SMTP',
      width: 180,
      cell: (row) => row.smtp_host || '—',
    },
    {
      key: 'is_active',
      header: 'Trạng thái',
      width: 120,
      cell: (row) => (
        <Badge variant={row.is_active ? 'outline' : 'secondary'}>
          {row.is_active ? 'Còn dùng' : 'Ngừng dùng'}
        </Badge>
      ),
    },
    {
      key: 'note',
      header: 'Ghi chú',
      width: 220,
      wrap: true,
      cell: (row) => <span className="text-muted-foreground">{row.note || '—'}</span>,
    },
    {
      key: 'actions',
      header: 'Thao tác',
      width: 110,
      hideable: false,
      cell: (row) => (
        <div className="flex items-center justify-center gap-1">
          {canWrite && (
            <Button
              variant="ghost"
              size="sm"
              className="h-8 w-8 p-0"
              title="Sửa hộp thư"
              onClick={() => openForm(row)}
            >
              <Pencil className="size-4" />
            </Button>
          )}
          {canDelete && row.is_active && (
            <ConfirmIconButton
              icon={Ban}
              title="Ngừng dùng hộp thư"
              confirmTitle="Ngừng dùng hộp thư này?"
              confirmDescription={
                'Không ai chọn được nó lúc ban hành nữa. Bản ghi vẫn giữ lại vì nhật ký ' +
                'thư cũ còn trỏ vào đây — câu "thư đó gửi danh nghĩa ai" phải trả lời được về sau.'
              }
              destructive
              disabled={deactivate.isPending}
              onConfirm={() => deactivate.mutate(row.id)}
            />
          )}
        </div>
      ),
    },
  ]

  return (
    <PageContainer fill>
      <PageHeader
        title="Hộp thư gửi"
        description="Địa chỉ đứng tên gửi thông báo thay cho địa chỉ mặc định của hệ thống."
        actions={
          canCreate && (
            <Button onClick={() => openForm(undefined)}>
              <Plus className="size-4" />
              Thêm hộp thư
            </Button>
          )
        }
      />

      <DataTable
        storageKey="system-mailboxes"
        columns={columns}
        rows={mailboxes}
        getRowId={(row) => row.id}
        isLoading={isLoading}
        isError={isError}
        onRefresh={() => refetch()}
        emptyMessage="Chưa khai hộp thư gửi nào. Thư ban hành đang đi bằng địa chỉ mặc định của hệ thống."
      />

      <MailboxFormDialog
        open={open}
        onOpenChange={setOpen}
        mailbox={editing}
        isPending={save.isPending}
        onSubmit={(input) =>
          save.mutate({ id: editing?.id, input }, { onSuccess: () => setOpen(false) })
        }
        onClearPassword={
          editing ? () => clearPassword.mutate(editing.id, { onSuccess: () => setOpen(false) }) : undefined
        }
      />
    </PageContainer>
  )
}
