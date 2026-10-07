import { beforeEach, describe, expect, it, vi } from 'vitest'

const apiGet = vi.fn()
const apiPost = vi.fn()
const apiPatch = vi.fn()
const apiPut = vi.fn()
const apiDelete = vi.fn()
const downloadFile = vi.fn()
vi.mock('@/core/api', () => ({
  apiGet: (...a: unknown[]) => apiGet(...a),
  apiPost: (...a: unknown[]) => apiPost(...a),
  apiPatch: (...a: unknown[]) => apiPatch(...a),
  apiPut: (...a: unknown[]) => apiPut(...a),
  apiDelete: (...a: unknown[]) => apiDelete(...a),
  downloadFile: (...a: unknown[]) => downloadFile(...a),
}))

import { laborContractApi } from './labor-contract-api'

beforeEach(() => vi.clearAllMocks())

describe('laborContractApi', () => {
  it('danh sách mẫu của nhân sự: bỏ trống loại thì KHÔNG gửi contract_type=0', async () => {
    apiGet.mockResolvedValue([])
    await laborContractApi.listTemplateOptions(7)
    await laborContractApi.listTemplateOptions(7, 0)
    await laborContractApi.listTemplateOptions(7, 2)
    expect(apiGet.mock.calls.map((c) => c[1])).toEqual([
      { params: undefined },
      { params: undefined },
      { params: { contract_type: 2 } },
    ])
    expect(apiGet.mock.calls[0][0]).toBe('/api/employees/7/labor-contract-templates')
  })

  it('tạo và sửa trả {item, warnings} nguyên dạng (không bóc mất cảnh báo)', async () => {
    const saved = { item: { id: 1 }, warnings: ['quá 36 tháng'] }
    apiPost.mockResolvedValue(saved)
    apiPatch.mockResolvedValue(saved)
    await expect(laborContractApi.create(7, {} as never)).resolves.toBe(saved)
    await expect(laborContractApi.update(1, { end_date: null })).resolves.toBe(saved)
    expect(apiPost).toHaveBeenCalledWith('/api/employees/7/labor-contracts', {})
    expect(apiPatch).toHaveBeenCalledWith('/api/labor-contracts/1', { end_date: null })
  })

  it('sinh tệp gửi {template_id}; chuyển trạng thái gửi {to_status,date,reason}', async () => {
    await laborContractApi.generate(3, { template_id: 9 })
    await laborContractApi.transition(3, { to_status: 4, date: '2026-05-01', reason: 'nghỉ' })
    expect(apiPost).toHaveBeenNthCalledWith(1, '/api/labor-contracts/3/generate', { template_id: 9 })
    expect(apiPost).toHaveBeenNthCalledWith(2, '/api/labor-contracts/3/transition', { to_status: 4, date: '2026-05-01', reason: 'nghỉ' })
  })

  it('tải bản ký lên bằng multipart field "file"', async () => {
    const f = new File([new Uint8Array(3)], 'ky.pdf')
    await laborContractApi.uploadSignedFile(3, f)
    const [url, form] = apiPut.mock.calls[0]
    expect(url).toBe('/api/labor-contracts/3/signed-file')
    expect((form as FormData).get('file')).toBeInstanceOf(File)
  })

  it('tải .docx và bản ký đi qua downloadFile (có token), không dùng url trần', async () => {
    await laborContractApi.downloadDocument(3, 'a.docx')
    await laborContractApi.downloadSignedFile(3, 'b.pdf')
    expect(downloadFile).toHaveBeenNthCalledWith(1, '/api/labor-contracts/3/document', 'a.docx')
    expect(downloadFile).toHaveBeenNthCalledWith(2, '/api/labor-contracts/3/signed-file', 'b.pdf')
  })
})
