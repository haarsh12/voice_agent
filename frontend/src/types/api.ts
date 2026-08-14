export type HealthResponse = {
  status: 'ok'
  agent_name: string
  configured: boolean
}

export type TokenResponse = {
  server_url: string
  participant_token: string
}
