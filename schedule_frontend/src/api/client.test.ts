import { afterEach, describe, expect, it, vi } from 'vitest'

vi.mock('@/utils/message', () => ({
  notifyError: vi.fn(),
}))

import { ApiClientError, get } from '@/api/client'
import { notifyError } from '@/utils/message'

describe('api client', () => {
  afterEach(() => {
    vi.restoreAllMocks()
    vi.mocked(notifyError).mockReset()
  })

  it('returns envelope data when code is 0', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          code: 0,
          message: 'success',
          data: { status: 'ok' },
        }),
      }),
    )

    await expect(get<{ status: string }>('/api/health')).resolves.toEqual({ status: 'ok' })
  })

  it('throws ApiClientError and notifies when business code is not 0', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: async () => ({
          code: 4060,
          message: 'AI is disabled',
          data: null,
        }),
      }),
    )

    await expect(get('/api/ai/test-connection')).rejects.toBeInstanceOf(ApiClientError)
    expect(vi.mocked(notifyError)).toHaveBeenCalledWith('AI is disabled')
  })
})
