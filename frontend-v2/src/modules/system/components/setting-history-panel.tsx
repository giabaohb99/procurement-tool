import { ArrowRight, History, RefreshCw } from 'lucide-react'

import { Button } from '@/shared/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/shared/ui/card'
import { Skeleton } from '@/shared/ui/skeleton'
import { cn } from '@/shared/utils/cn'
import { formatDateTime } from '@/shared/utils/format-date'

import { SETTING_HISTORY_LIMIT, useSettingHistory } from '../hooks/use-settings'
import { parseSettingChangeLine, splitSettingLogMessage } from '../utils/setting-log-format'

/**
 * LỊCH SỬ THAY ĐỔI của màn Cấu hình hệ thống (bao-CR-462).
 *
 * Bày dạng dòng thời gian chứ không dùng `DataTable`: nội dung chính của một lần
 * cập nhật là DANH SÁCH ô đã đổi, dài ngắn tùy lần — nhét vào một ô bảng thì hoặc
 * cụt đuôi, hoặc kéo dòng cao gấp mấy lần các dòng khác.
 *
 * ⚠️ Nguồn là `tab_audit_log` (`entity=setting`), KHÔNG phải `tab_change_log`.
 * Quyển sổ trước/sau ở mức cột kia chưa có đường API nào đọc được; nó dành cho
 * người đi tra sự cố, còn dòng ở đây là câu backend viết sẵn cho người vừa bấm Lưu.
 */
export function SettingHistoryPanel() {
  const { data, isPending, isError, isFetching, refetch } = useSettingHistory()
  const logs = data ?? []

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-3">
        <CardTitle className="flex items-center gap-2 text-base">
          <History className="size-4 text-muted-foreground" />
          Lịch sử thay đổi
        </CardTitle>
        <Button variant="outline" size="sm" onClick={() => void refetch()} disabled={isFetching}>
          <RefreshCw className={cn('size-4', isFetching && 'animate-spin')} />
          Tải lại
        </Button>
      </CardHeader>

      <CardContent className="flex flex-col gap-3">
        <p className="text-xs text-muted-foreground">
          {SETTING_HISTORY_LIMIT} lần cập nhật gần nhất, kèm giá trị trước và sau của từng
          ô. Giá trị của khóa bí mật <b>không</b> được ghi vào nhật ký — chỉ ghi nhận là đã
          đặt lại.
        </p>

        {isPending && <Skeleton className="h-24 w-full" />}

        {/*
          Lỗi phải nói thành lời: thẻ rỗng vì thiếu quyền trông y hệt thẻ rỗng vì
          chưa ai đổi gì, mà hai thứ đó dẫn tới hai việc phải làm khác hẳn nhau.
        */}
        {isError && (
          <p className="text-sm text-destructive">
            Không đọc được nhật ký thay đổi. Bấm <b>Tải lại</b> để thử lần nữa.
          </p>
        )}

        {!isPending && !isError && logs.length === 0 && (
          <p className="text-sm text-muted-foreground">Chưa có lần cập nhật nào được ghi nhận.</p>
        )}

        {logs.length > 0 && (
          <ol className="flex flex-col gap-2">
            {logs.map((log) => {
              const { title, details } = splitSettingLogMessage(log.message)
              return (
                <li key={log.id} className="rounded-lg border px-3 py-2.5">
                  <div className="flex flex-wrap items-baseline gap-x-2">
                    <span className="text-sm font-medium">{log.by}</span>
                    <span className="text-xs text-muted-foreground">
                      {formatDateTime(log.at)}
                    </span>
                  </div>
                  {/*
                    Bản ghi ghi TRƯỚC bao-CR-461 chỉ có câu tóm tắt, không có dòng
                    chi tiết nào — đó là dữ liệu thật, không phải thiếu sót.
                  */}
                  <p className="text-sm">{title || log.action_label}</p>

                  {details.length > 0 && (
                    <ul className="mt-2 flex flex-col gap-1">
                      {details.map((line, index) => {
                        const change = parseSettingChangeLine(line)
                        return (
                          <li
                            key={`${log.id}-${index}`}
                            className="flex flex-wrap items-center gap-x-1.5 gap-y-0.5 text-xs"
                          >
                            {change ? (
                              <>
                                <span className="text-muted-foreground">{change.label}</span>
                                <span className="rounded bg-muted px-1.5 py-0.5 break-all text-muted-foreground">
                                  {change.before}
                                </span>
                                <ArrowRight className="size-3 shrink-0 text-muted-foreground" />
                                <span className="rounded bg-muted px-1.5 py-0.5 font-medium break-all">
                                  {change.after}
                                </span>
                              </>
                            ) : (
                              //  Dòng của khóa bí mật («… đã đặt giá trị mới») không
                              //  có cặp trước/sau — hiện nguyên văn, đừng bỏ qua.
                              <span className="text-muted-foreground">{line}</span>
                            )}
                          </li>
                        )
                      })}
                    </ul>
                  )}
                </li>
              )
            })}
          </ol>
        )}
      </CardContent>
    </Card>
  )
}
