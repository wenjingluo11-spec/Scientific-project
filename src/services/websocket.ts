import { store } from '@/store/store'
import { updateAgentProgress, fetchPaperById } from '@/store/slices/papersSlice'

class WebSocketService {
  private sockets: Map<number, WebSocket> = new Map()
  private reconnectAttempts: Map<number, number> = new Map()
  private maxReconnectAttempts = 5

  connect(paperId: number) {
    if (this.sockets.has(paperId)) return // Already connected

    const wsUrl = `ws://localhost:8001/api/v1/papers/ws/paper/${paperId}`
    const ws = new WebSocket(wsUrl)
    this.sockets.set(paperId, ws)

    ws.onopen = () => {
      console.log(`WebSocket connected for paper ${paperId}`)
      this.reconnectAttempts.set(paperId, 0)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      // Pass paperId to ensure the reducer knows which paper this belongs to
      store.dispatch(updateAgentProgress({ ...data, paperId }))

      // If generation is complete, fetch the final paper content
      if (data.agent === 'completed') {
        store.dispatch(fetchPaperById(paperId))
        this.disconnect(paperId)
      }
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error for paper ${paperId}:`, error)
    }

    ws.onclose = () => {
      console.log(`WebSocket disconnected for paper ${paperId}`)
      const attempts = this.reconnectAttempts.get(paperId) || 0
      if (attempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts.set(paperId, attempts + 1)
          this.connect(paperId)
        }, 3000)
      } else {
        this.sockets.delete(paperId)
      }
    }
  }

  disconnect(paperId?: number) {
    if (paperId) {
      const ws = this.sockets.get(paperId)
      if (ws) {
        ws.close()
        this.sockets.delete(paperId)
      }
    } else {
      // Disconnect all
      this.sockets.forEach((ws) => ws.close())
      this.sockets.clear()
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const websocketService = new WebSocketService()
