import { describe, expect, it } from 'vitest'

import {
  FOLDER_DRAG_MIME,
  hasFolderDragPayload,
  readFolderDragPayload,
  writeFolderDragPayload,
  type FolderDragPayload,
} from './folder-drag-payload'

/**
 * jsdom KHÔNG dựng `DataTransfer` thật (bản mô phỏng thiếu hẳn) — dùng một
 * bản giả tối thiểu đủ cho `setData`/`getData`/`types`, đúng hành vi native:
 * `types` là mảng MIME đã từng `setData`, `getData` đọc theo đúng MIME đó.
 */
class FakeDataTransfer implements Pick<DataTransfer, 'setData' | 'getData' | 'types'> {
  private store = new Map<string, string>()

  setData(format: string, data: string): void {
    this.store.set(format, data)
  }

  getData(format: string): string {
    return this.store.get(format) ?? ''
  }

  get types(): readonly string[] {
    return Array.from(this.store.keys())
  }
}

function fakeDataTransfer() {
  return new FakeDataTransfer() as unknown as DataTransfer
}

describe('writeFolderDragPayload / readFolderDragPayload', () => {
  it('ghi rồi đọc lại đúng nguyên payload', () => {
    const dt = fakeDataTransfer()
    const payload: FolderDragPayload = { documentIds: [1, 2, 3], folderIds: [9], sourceFolderId: 5 }
    writeFolderDragPayload(dt, payload)
    expect(readFolderDragPayload(dt)).toEqual(payload)
  })

  it('sourceFolderId null (không gắn thư mục nguồn) đọc lại đúng null', () => {
    const dt = fakeDataTransfer()
    const payload: FolderDragPayload = { documentIds: [1], folderIds: [], sourceFolderId: null }
    writeFolderDragPayload(dt, payload)
    expect(readFolderDragPayload(dt)).toEqual(payload)
  })

  it('chưa từng ghi gì → đọc ra null, không ném lỗi', () => {
    expect(readFolderDragPayload(fakeDataTransfer())).toBeNull()
  })

  it('JSON hỏng (dữ liệu từ nguồn khác gắn cùng MIME) → null, không ném lỗi', () => {
    const dt = fakeDataTransfer()
    dt.setData(FOLDER_DRAG_MIME, '{khong phai json')
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('thiếu khóa bắt buộc → null', () => {
    const dt = fakeDataTransfer()
    dt.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: [1] }))
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('mảng chứa số THỰC (không phải số nguyên) → null', () => {
    const dt = fakeDataTransfer()
    dt.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: [1.5], folderIds: [], sourceFolderId: null }))
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('mảng chứa số ÂM hoặc 0 → null (id thật luôn dương)', () => {
    const dt = fakeDataTransfer()
    expect(
      readFolderDragPayload(
        (() => {
          const d = fakeDataTransfer()
          d.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: [-1], folderIds: [], sourceFolderId: null }))
          return d
        })(),
      ),
    ).toBeNull()
    dt.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: [0], folderIds: [], sourceFolderId: null }))
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('mảng chứa chuỗi thay vì số → null', () => {
    const dt = fakeDataTransfer()
    dt.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: ['1'], folderIds: [], sourceFolderId: null }))
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('sourceFolderId = 0 → null (0 không phải id thật, đừng lẫn với null)', () => {
    const dt = fakeDataTransfer()
    dt.setData(FOLDER_DRAG_MIME, JSON.stringify({ documentIds: [1], folderIds: [], sourceFolderId: 0 }))
    expect(readFolderDragPayload(dt)).toBeNull()
  })

  it('cả hai mảng RỖNG cùng lúc vẫn hợp lệ (kéo thứ khác ngoài văn bản/thư mục là việc của nơi gọi tự chặn)', () => {
    const dt = fakeDataTransfer()
    const payload: FolderDragPayload = { documentIds: [], folderIds: [], sourceFolderId: null }
    writeFolderDragPayload(dt, payload)
    expect(readFolderDragPayload(dt)).toEqual(payload)
  })

  it('khóa THỪA trong JSON vẫn đọc được (chỉ soát khóa BẮT BUỘC, không xóa khóa lạ)', () => {
    const dt = fakeDataTransfer()
    dt.setData(
      FOLDER_DRAG_MIME,
      JSON.stringify({ documentIds: [1], folderIds: [], sourceFolderId: null, extra: 'lạ' }),
    )
    const result = readFolderDragPayload(dt)
    expect(result).not.toBeNull()
    expect(result).toMatchObject({ documentIds: [1], folderIds: [], sourceFolderId: null })
  })
})

describe('hasFolderDragPayload', () => {
  it('đã setData đúng MIME → true, kể cả lúc dragover (chưa gọi getData thật)', () => {
    const dt = fakeDataTransfer()
    writeFolderDragPayload(dt, { documentIds: [1], folderIds: [], sourceFolderId: null })
    expect(hasFolderDragPayload(dt)).toBe(true)
  })

  it('không có MIME này (kéo tệp từ ngoài trình duyệt vào) → false', () => {
    const dt = fakeDataTransfer()
    ;(dt as unknown as FakeDataTransfer).setData('Files', 'x')
    expect(hasFolderDragPayload(dt)).toBe(false)
  })

  it('dataTransfer trống hoàn toàn → false, không ném lỗi', () => {
    expect(hasFolderDragPayload(fakeDataTransfer())).toBe(false)
  })
})
