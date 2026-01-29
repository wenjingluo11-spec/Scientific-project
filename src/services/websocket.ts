import { store } from '@/store/store'
import { updateAgentProgress, fetchPaperById } from '@/store/slices/papersSlice'

class WebSocketService {
  private ws: WebSocket | null = null
  private reconnectAttempts = 0
  private maxReconnectAttempts = 5

  connect(paperId: number) {
    const wsUrl = `ws://localhost:8001/api/v1/papers/ws/paper/${paperId}`

    this.ws = new WebSocket(wsUrl)

    this.ws.onopen = () => {
      console.log('WebSocket connected')
      this.reconnectAttempts = 0
    }

    this.ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      store.dispatch(updateAgentProgress(data))

      // If generation is complete, fetch the final paper content
      if (data.agent === 'completed') {
        store.dispatch(fetchPaperById(paperId))
      }
    }

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error)
    }

    this.ws.onclose = () => {
      console.log('WebSocket disconnected')
      if (this.reconnectAttempts < this.maxReconnectAttempts) {
        setTimeout(() => {
          this.reconnectAttempts++
          this.connect(paperId)
        }, 3000)
      }
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }
}

export const websocketService = new WebSocketService()
