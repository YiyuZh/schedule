import { API_BASE_URL, REQUEST_TIMEOUT } from '@/config/app'
import { notifyError } from '@/utils/message'

type HttpMethod = 'GET' | 'POST' | 'PUT' | 'PATCH' | 'DELETE'

type QueryValue = string | number | boolean | null | undefined

export interface RequestOptions {
  query?: Record<string, QueryValue>
  body?: unknown
  timeout?: number
  headers?: HeadersInit
  showErrorMessage?: boolean
}

interface ApiEnvelope<T> {
  code: number
  message: string
  data: T
}

export class ApiClientError extends Error {
  code: number
  status: number

  constructor(message: string, code = -1, status = 500) {
    super(message)
    this.name = 'ApiClientError'
    this.code = code
    this.status = status
  }
}

function buildUrl(path: string, query?: Record<string, QueryValue>): string {
  const url = new URL(path, API_BASE_URL)
  if (!query) {
    return url.toString()
  }

  Object.entries(query).forEach(([key, value]) => {
    if (value === null || value === undefined || value === '') {
      return
    }
    url.searchParams.set(key, String(value))
  })

  return url.toString()
}

async function parseJsonSafely(response: Response): Promise<unknown> {
  try {
    return await response.json()
  } catch {
    return null
  }
}

async function request<T>(method: HttpMethod, path: string, options: RequestOptions = {}): Promise<T> {
  const controller = new AbortController()
  const timeoutId = window.setTimeout(() => controller.abort(), options.timeout ?? REQUEST_TIMEOUT)

  try {
    const response = await fetch(buildUrl(path, options.query), {
      method,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      body: options.body !== undefined ? JSON.stringify(options.body) : undefined,
      signal: controller.signal,
    })

    const payload = (await parseJsonSafely(response)) as ApiEnvelope<T> | null

    if (!response.ok) {
      const errorMessage = payload?.message || `请求失败：${response.status}`
      throw new ApiClientError(errorMessage, payload?.code ?? response.status, response.status)
    }

    if (!payload) {
      throw new ApiClientError('接口返回为空', -1, response.status)
    }

    if (payload.code !== 0) {
      throw new ApiClientError(payload.message || '请求失败', payload.code, response.status)
    }

    return payload.data
  } catch (error) {
    let message = '网络请求失败'
    let clientError: ApiClientError

    if (error instanceof ApiClientError) {
      clientError = error
      message = error.message
    } else if (error instanceof DOMException && error.name === 'AbortError') {
      clientError = new ApiClientError('请求超时，请稍后重试', -1, 408)
      message = clientError.message
    } else {
      clientError = new ApiClientError(error instanceof Error ? error.message : message, -1, 500)
      message = clientError.message
    }

    if (options.showErrorMessage !== false) {
      notifyError(message)
    }

    throw clientError
  } finally {
    window.clearTimeout(timeoutId)
  }
}

export function get<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>('GET', path, options)
}

export function post<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>('POST', path, options)
}

export function put<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>('PUT', path, options)
}

export function patch<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>('PATCH', path, options)
}

export function del<T>(path: string, options?: RequestOptions): Promise<T> {
  return request<T>('DELETE', path, options)
}
