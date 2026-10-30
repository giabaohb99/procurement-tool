import { describe, expect, it } from 'vitest'

import type { AdminMcpKey, McpCall, OAuthClient } from '../types/ai-skill'
import { filterOAuthClients, readCallDocument, redirectHost, toConnectionRow } from './ai-row-mappers'

/**
 * bao-CR-696 — hợp đồng màn Kết nối / cột Chứng từ còn là BẢN ĐỀ NGHỊ. Các hàm map phải chịu được: máy chủ cũ thiếu
 * hẳn trường mới, trường null, chuỗi toàn khoảng trắng, giá trị lạ, và link chứng từ dẫn ra ngoài.
 */

function oldServerKey(over: Partial<AdminMcpKey> = {}): AdminMcpKey {
  return {
    id: 1, name: 'Claude máy nhà', hint: '…ab12', scope: 0, scope_label: 'chỉ đọc', expires_at: null,
    last_used_at: '2026-10-29T08:00:00', created_at: null, state: 2, state_label: 'Đang dùng', issued_by: 0,
    claimed_at: null, batch_id: '', user_id: 42, owner_label: 'Nguyễn Văn An', department_id: 3, department: 'Thu mua',
    issued_by_label: '', ...over,
  }
}

describe('toConnectionRow', () => {
  it('reads the proposed fields when the server sends them', () => {
    const row = toConnectionRow(
      oldServerKey({
        person_name: 'Trần Thị Bình', employee_code: 'NSU001', email: 'binh@dego.vn', dept_name: 'Kế toán',
        connection_type: 'oauth', app_name: 'ChatGPT', app_redirect_uri: 'https://chatgpt.com/connector/oauth/abc',
      }),
    )
    expect(row).toMatchObject({
      person: 'Trần Thị Bình', employeeCode: 'NSU001', email: 'binh@dego.vn', department: 'Kế toán',
      connectionType: 'oauth', appName: 'ChatGPT', appRedirectUri: 'https://chatgpt.com/connector/oauth/abc',
    })
  })

  it('falls back to the fields an older server already has, without printing undefined', () => {
    const row = toConnectionRow(oldServerKey())
    expect(row).toMatchObject({
      person: 'Nguyễn Văn An', employeeCode: '', email: '', department: 'Thu mua', connectionType: 'key',
      appName: '', appRedirectUri: '', keyName: 'Claude máy nhà', lastUsedAt: '2026-10-29T08:00:00',
    })
    //  Mọi ô chữ phải là chuỗi thật — `undefined` / `null` lọt vào JSX là ô in chữ "undefined" hoặc trống không lý do.
    for (const field of ['person', 'employeeCode', 'email', 'department', 'appName', 'appRedirectUri', 'keyName', 'hint', 'stateLabel'] as const) {
      expect(typeof row[field], field).toBe('string')
    }
  })

  it('treats null and whitespace-only new fields as missing and keeps the old value', () => {
    const row = toConnectionRow(oldServerKey({ person_name: '   ', dept_name: null, email: null, employee_code: ' ' }))
    expect(row.person).toBe('Nguyễn Văn An')
    expect(row.department).toBe('Thu mua')
    expect(row.email).toBe('')
    expect(row.employeeCode).toBe('')
  })

  it('takes OAuth from the old kind field and pulls the app name out of the "Qua <app>" key name', () => {
    const row = toConnectionRow(oldServerKey({ kind: 2, name: 'Qua claude.ai' }))
    expect(row.connectionType).toBe('oauth')
    expect(row.appName).toBe('claude.ai')
  })

  it('does not invent an app name for a hand-pasted key whose name happens to start like an OAuth one', () => {
    expect(toConnectionRow(oldServerKey({ kind: 1, name: 'Qua máy công ty' })).appName).toBe('')
  })

  it('prefers app_name over the key-name trick, and an explicit connection_type over kind', () => {
    const row = toConnectionRow(oldServerKey({ kind: 2, name: 'Qua X', app_name: 'Tên thật', connection_type: 'key' }))
    expect(row.connectionType).toBe('key')
    expect(row.appName).toBe('Tên thật')
  })

  it('accepts the connection type in any case and ignores an unknown value', () => {
    expect(toConnectionRow(oldServerKey({ connection_type: 'OAUTH' })).connectionType).toBe('oauth')
    expect(toConnectionRow(oldServerKey({ connection_type: 'saml', kind: 2 })).connectionType).toBe('oauth')
    expect(toConnectionRow(oldServerKey({ connection_type: '', kind: undefined })).connectionType).toBe('key')
  })

  it('shows the user id when the server has no name at all, and nothing for user 0 (broken key)', () => {
    expect(toConnectionRow(oldServerKey({ owner_label: '' })).person).toBe('#42')
    expect(toConnectionRow(oldServerKey({ owner_label: '', user_id: 0 })).person).toBe('')
  })
})

describe('redirectHost', () => {
  it('shortens a normal URL to its host, keeping the port', () => {
    expect(redirectHost('https://chatgpt.com/connector/oauth/x?y=1')).toBe('chatgpt.com')
    expect(redirectHost('http://localhost:6274/callback')).toBe('localhost:6274')
  })

  it('keeps the raw string when it is not a standard URL, so a strange app is still recognisable', () => {
    expect(redirectHost('cursor://anysphere.cursor-retrieval/oauth')).toBe('anysphere.cursor-retrieval')
    expect(redirectHost('khong phai url')).toBe('khong phai url')
    expect(redirectHost('vscode:/callback')).toBe('vscode:/callback')
  })

  it('returns empty for empty or blank input', () => {
    expect(redirectHost('')).toBe('')
    expect(redirectHost('   ')).toBe('')
  })
})

function call(over: Partial<McpCall> = {}): McpCall {
  return {
    id: 1, created_at: null, key_id: 1, user_id: 7, employee_id: 7, department_id: 0, company_id: 0, client_name: '',
    method: 'tools/call', tool: 'propose_approval', skill_id: 0, status: 1, status_label: 'Thành công', deny_reason: '',
    duration_ms: 1, ip: '', user_label: 'An', ...over,
  }
}

describe('readCallDocument', () => {
  it('is null for a read-only call, a legacy row, or an older server without the field', () => {
    expect(readCallDocument(call())).toBeNull()
    expect(readCallDocument(call({ doc_code: null, doc_url: null, doc_id: null }))).toBeNull()
    expect(readCallDocument(call({ doc_code: '   ' }))).toBeNull()
    expect(readCallDocument(call({ doc_id: 0 }))).toBeNull()
    expect(readCallDocument(call({ doc_id: -5 }))).toBeNull()
  })

  it('needs a code to show anything: a link without a code is dropped', () => {
    expect(readCallDocument(call({ doc_url: '/procurement/purchase-requests/9' }))).toBeNull()
  })

  it('falls back to the document id when the code is missing', () => {
    expect(readCallDocument(call({ doc_id: 9 }))).toEqual({ code: '#9', href: null })
  })

  it('links only to an internal path', () => {
    expect(readCallDocument(call({ doc_code: 'YCMH-0001', doc_url: '/procurement/purchase-requests/9' }))).toEqual({
      code: 'YCMH-0001',
      href: '/procurement/purchase-requests/9',
    })
    for (const unsafe of ['//evil.com/x', '/\\evil.com', 'https://evil.com', 'javascript:alert(1)', ' javascript:x', '']) {
      expect(readCallDocument(call({ doc_code: 'YCMH-0001', doc_url: unsafe }))?.href, unsafe).toBeNull()
    }
  })
})

function app(id: number, over: Partial<OAuthClient> = {}): OAuthClient {
  return {
    id, client_id: `dego_oc_${id}`, client_name: `App ${id}`, redirect_hosts: ['chatgpt.com'], trusted: true,
    auth_method: 'none', ip: '', created_at: null, last_used_at: null, live_grants: 0, ...over,
  }
}

describe('filterOAuthClients', () => {
  const items = [
    app(1, { client_name: 'ChatGPT', live_grants: 3 }),
    app(2, { client_name: 'Trình kết nối lạ', trusted: false, redirect_hosts: ['evil.example'] }),
    app(3, { client_name: 'claude.ai', redirect_hosts: ['claude.ai'], live_grants: 1, trusted: false }),
  ]

  it('returns everything for "all", an unknown status and an empty keyword', () => {
    expect(filterOAuthClients(items, '', 'all')).toHaveLength(3)
    expect(filterOAuthClients(items, '  ', 'khong-ro')).toHaveLength(3)
  })

  it('splits by live connections and flags untrusted hosts', () => {
    expect(filterOAuthClients(items, '', 'live').map((c) => c.id)).toEqual([1, 3])
    expect(filterOAuthClients(items, '', 'idle').map((c) => c.id)).toEqual([2])
    expect(filterOAuthClients(items, '', 'untrusted').map((c) => c.id)).toEqual([2, 3])
  })

  it('searches name, client id and redirect host without caring about Vietnamese accents', () => {
    expect(filterOAuthClients(items, 'ket noi', 'all').map((c) => c.id)).toEqual([2])
    expect(filterOAuthClients(items, 'EVIL.example', 'all').map((c) => c.id)).toEqual([2])
    expect(filterOAuthClients(items, 'dego_oc_3', 'all').map((c) => c.id)).toEqual([3])
    expect(filterOAuthClients(items, 'claude', 'untrusted').map((c) => c.id)).toEqual([3])
    expect(filterOAuthClients(items, 'không có', 'all')).toEqual([])
  })

  it('survives an empty list and a client with no redirect hosts', () => {
    expect(filterOAuthClients([], 'x', 'live')).toEqual([])
    expect(filterOAuthClients([app(9, { redirect_hosts: [] })], 'chatgpt', 'all')).toEqual([])
  })
})
