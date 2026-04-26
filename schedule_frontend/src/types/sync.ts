export interface SyncStatus {
  enabled: boolean
  configured: boolean
  logged_in: boolean
  server_url: string | null
  user_email: string | null
  device_id: string
  device_name: string
  pending_count: number
  conflict_count: number
  last_push_at: string | null
  last_pull_at: string | null
  last_error: string | null
}

export interface SyncConfigPayload {
  server_url: string | null
  device_name: string | null
  enabled: boolean
}

export interface SyncConfigResponse {
  status: SyncStatus
}

export interface SyncLoginPayload {
  email: string
  password: string
  server_url?: string | null
  device_name?: string | null
}

export interface SyncRegisterPayload extends SyncLoginPayload {
  display_name?: string | null
}

export interface SyncRunResult {
  push_count: number
  pull_count: number
  conflict_count: number
  error_count: number
  message: string
}

export interface SyncConflict {
  id: number
  entity_type: string
  entity_id: string
  status: 'open' | 'resolved' | 'ignored'
  local_payload_json: string | null
  remote_payload_json: string | null
  created_at: string
  updated_at: string
}

export interface SyncConflictListData {
  items: SyncConflict[]
}

export interface SyncConflictResolvePayload {
  resolution: string
}
