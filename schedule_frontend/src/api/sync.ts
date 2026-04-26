import { get, post } from '@/api/client'
import type {
  SyncConfigPayload,
  SyncConfigResponse,
  SyncConflict,
  SyncConflictListData,
  SyncConflictResolvePayload,
  SyncLoginPayload,
  SyncRegisterPayload,
  SyncRunResult,
  SyncStatus,
} from '@/types/sync'

export function fetchSyncStatus(): Promise<SyncStatus> {
  return get<SyncStatus>('/api/sync/status')
}

export async function saveSyncConfig(payload: SyncConfigPayload): Promise<SyncStatus> {
  const data = await post<SyncConfigResponse>('/api/sync/config', { body: payload })
  return data.status
}

export async function loginSync(payload: SyncLoginPayload): Promise<SyncStatus> {
  const data = await post<SyncConfigResponse>('/api/sync/login', { body: payload })
  return data.status
}

export async function registerSync(payload: SyncRegisterPayload): Promise<SyncStatus> {
  const data = await post<SyncConfigResponse>('/api/sync/register', { body: payload })
  return data.status
}

export async function logoutSync(): Promise<SyncStatus> {
  const data = await post<SyncConfigResponse>('/api/sync/logout')
  return data.status
}

export function runSync(): Promise<SyncRunResult> {
  return post<SyncRunResult>('/api/sync/run')
}

export function pushSync(): Promise<SyncRunResult> {
  return post<SyncRunResult>('/api/sync/push')
}

export function pullSync(): Promise<SyncRunResult> {
  return post<SyncRunResult>('/api/sync/pull')
}

export async function fetchSyncConflicts(): Promise<SyncConflict[]> {
  const data = await get<SyncConflictListData>('/api/sync/conflicts')
  return data.items
}

export function resolveSyncConflict(conflictId: number, payload: SyncConflictResolvePayload): Promise<SyncConflict> {
  return post<SyncConflict>(`/api/sync/conflicts/${conflictId}/resolve`, { body: payload })
}
