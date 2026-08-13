/**
 * Kho dữ liệu TẠM phía trình duyệt cho phân hệ Văn bản.
 *
 * ⚠️ Phân hệ này chưa có backend. Mỗi danh mục / bảng dữ liệu tạo một "collection"
 * từ đây: giữ bản ghi + lịch sử thao tác trong bộ nhớ, ghi kèm localStorage cho
 * F5 không mất, và phát tín hiệu cho React qua `useSyncExternalStore`.
 *
 * Gom về một factory vì cả bốn danh mục lẫn bảng văn bản đều cần đúng một bộ:
 * đọc / lưu / xóa / nhật ký. Khi có API thật thì bỏ file này và thay các hook
 * bằng react-query — kiểu dữ liệu đã đặt theo lối backend nên trang không đổi.
 */

/** Một dòng lịch sử — đặt tên trường theo `AuditLogEntry` của backend. */
export interface HistoryEntry {
  recordId: number
  action: 'create' | 'write' | 'delete'
  action_label: string
  /** Diễn giải ngắn: đổi cái gì. */
  message?: string
  by: string
  /** ISO string. */
  at: string
}

export interface CollectionState<T> {
  items: T[]
  history: HistoryEntry[]
}

export interface SaveOptions {
  /**
   * Lưu mà KHÔNG ghi vào lịch sử thao tác.
   *
   * Dành cho tự động lưu: gõ vài chữ đã ghi một dòng nhật ký thì sổ lịch sử
   * dài hàng trăm dòng "Cập nhật" giống hệt nhau, không còn tra được gì.
   */
  silent?: boolean
}

export interface LocalCollection<T extends { id: number }> {
  subscribe: (listener: () => void) => () => void
  getState: () => CollectionState<T>
  /** Thêm mới (không truyền `id`) hoặc sửa; trả id của bản ghi vừa lưu. */
  save: (values: Omit<T, 'id'>, actor: string, id?: number, options?: SaveOptions) => number
  remove: (id: number, actor: string) => void
}

interface CreateOptions<T> {
  /** Khóa localStorage, vd `erp.document-types`. */
  storageKey: string
  /** Dữ liệu khởi tạo khi máy chưa có gì. */
  seed: T[]
  /** Nhãn tiếng Việt của từng trường — dùng để ghi "đổi tên, tiền tố". */
  labels: Partial<Record<keyof T, string>>
}

export function createLocalCollection<T extends { id: number }>({
  storageKey,
  seed,
  labels,
}: CreateOptions<T>): LocalCollection<T> {
  let state = read()
  const listeners = new Set<() => void>()

  function read(): CollectionState<T> {
    try {
      const raw = localStorage.getItem(storageKey)
      if (!raw) return { items: seed, history: [] }
      const parsed = JSON.parse(raw) as Partial<CollectionState<T>>
      return {
        items: Array.isArray(parsed.items) ? parsed.items : seed,
        history: Array.isArray(parsed.history) ? parsed.history : [],
      }
    } catch {
      // Dữ liệu cũ hỏng định dạng -> dùng bản khởi tạo.
      return { items: seed, history: [] }
    }
  }

  function commit(next: CollectionState<T>) {
    state = next
    try {
      localStorage.setItem(storageKey, JSON.stringify(next))
    } catch {
      // Hết quota hoặc trình duyệt chặn storage: vẫn dùng được trong phiên này.
    }
    listeners.forEach((listener) => listener())
  }

  function entry(
    recordId: number,
    action: HistoryEntry['action'],
    action_label: string,
    by: string,
    message?: string,
  ): HistoryEntry {
    return { recordId, action, action_label, by, message, at: new Date().toISOString() }
  }

  /** "đổi tên, tiền tố" — liệt kê trường vừa đổi; `undefined` nếu không đổi gì. */
  function changeSummary(before: T | undefined, after: Omit<T, 'id'>): string | undefined {
    if (!before) return undefined
    const changed = (Object.keys(labels) as (keyof T)[]).filter(
      (field) =>
        JSON.stringify(before[field]) !== JSON.stringify((after as T)[field]),
    )
    if (changed.length === 0) return undefined
    return `đổi ${changed.map((field) => labels[field]).join(', ')}`
  }

  return {
    subscribe(listener) {
      listeners.add(listener)
      return () => listeners.delete(listener)
    },

    getState: () => state,

    save(values, actor, id, options) {
      if (id) {
        const before = state.items.find((item) => item.id === id)
        commit({
          items: state.items.map((item) =>
            item.id === id ? ({ ...item, ...values } as T) : item,
          ),
          history: options?.silent
            ? state.history
            : [
                entry(id, 'write', 'Cập nhật', actor, changeSummary(before, values)),
                ...state.history,
              ],
        })
        return id
      }

      // Id tăng theo id lớn nhất đang có, không dùng `length` — xóa ở giữa rồi
      // thêm mới sẽ đụng id cũ.
      const nextId = state.items.reduce((max, item) => Math.max(max, item.id), 0) + 1
      commit({
        items: [...state.items, { ...values, id: nextId } as T],
        history: [entry(nextId, 'create', 'Tạo mới', actor), ...state.history],
      })
      return nextId
    },

    remove(id, actor) {
      commit({
        items: state.items.filter((item) => item.id !== id),
        // Giữ lịch sử của bản ghi đã xóa: sổ nhật ký mà xóa theo thì hỏi ai xóa
        // lúc nào cũng chịu.
        history: [entry(id, 'delete', 'Xóa', actor), ...state.history],
      })
    },
  }
}
