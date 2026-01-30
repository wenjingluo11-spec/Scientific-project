import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '@/services/api'

export interface Paper {
  id: number
  topic_id: number
  title: string
  abstract: string
  content: string
  version: number
  status: 'draft' | 'reviewing' | 'completed'
  quality_score: number
  detailed_scores?: {
    novelty: number
    quality: number
    clarity: number
    total: number
  }
  created_at: string
}

export interface AgentProgress {
  paperId?: number
  agent: string
  status: 'waiting' | 'working' | 'completed' | 'reviewing_revision'
  message: string
  progress: number
  detailedScores?: {
    novelty: number
    quality: number
    clarity: number
    total: number
  }
}

export interface PaperTraceItem {
  id: number
  step_name: string
  agent_role: string
  model_signature: string
  input_context: string
  output_content: string
  iteration: number
  created_at: string
}

interface PapersState {
  papers: Paper[]
  currentPaper: Paper | null
  multiAgentProgress: Record<number, AgentProgress[]> // For concurrent tasks
  agentProgress: AgentProgress[] // Legacy/Focused progress
  activePaperIds: number[]
  paperTrace: PaperTraceItem[]
  loading: boolean
  generating: boolean
  traceLoading: boolean
  error: string | null
}

const initialState: PapersState = {
  papers: [],
  currentPaper: null,
  multiAgentProgress: {},
  agentProgress: [],
  activePaperIds: [],
  paperTrace: [],
  loading: false,
  generating: false,
  traceLoading: false,
  error: null,
}

export const fetchPaperTrace = createAsyncThunk(
  'papers/fetchPaperTrace',
  async (paperId: number) => {
    const response = await api.get(`/api/v1/papers/${paperId}/trace`)
    return response.data
  }
)

export const generatePaper = createAsyncThunk(
  'papers/generatePaper',
  async (topicIds: number[]) => {
    const response = await api.post(`/api/v1/papers/generate`, { topic_ids: topicIds })
    return response.data
  }
)

export const fetchPapers = createAsyncThunk('papers/fetchPapers', async () => {
  const response = await api.get('/api/v1/papers')
  return response.data
})

export const fetchPaperById = createAsyncThunk(
  'papers/fetchPaperById',
  async (paperId: number) => {
    const response = await api.get(`/api/v1/papers/${paperId}`)
    return response.data
  }
)

export const deletePaper = createAsyncThunk(
  'papers/deletePaper',
  async (paperId: number) => {
    await api.delete(`/api/v1/papers/${paperId}`)
    return paperId
  }
)

const papersSlice = createSlice({
  name: 'papers',
  initialState,
  reducers: {
    updateAgentProgress: (state, action: PayloadAction<AgentProgress>) => {
      const { paperId, agent } = action.payload

      // Handle completion globally if no paperId (legacy)
      if (agent === 'completed' && !paperId) {
        state.generating = false
        return
      }

      // If we have a paperId, update multi-progress
      if (paperId) {
        if (!state.multiAgentProgress[paperId]) {
          state.multiAgentProgress[paperId] = []
        }

        const index = state.multiAgentProgress[paperId].findIndex(p => p.agent === agent)
        if (index >= 0) {
          state.multiAgentProgress[paperId][index] = action.payload
        } else {
          state.multiAgentProgress[paperId].push(action.payload)
        }

        // Remove from active list if completed
        if (agent === 'completed') {
          state.activePaperIds = state.activePaperIds.filter(id => id !== paperId)
          if (state.activePaperIds.length === 0) {
            state.generating = false
          }

          // Sync completion data to current paper if matches
          if (state.currentPaper?.id === paperId) {
            state.currentPaper.status = 'completed'
            if (action.payload.detailedScores) {
              state.currentPaper.detailed_scores = action.payload.detailedScores
              state.currentPaper.quality_score = action.payload.detailedScores.total
            }
          }
        }
      }

      // Always sync to focused progress for the current paper being viewed
      if (!paperId || state.currentPaper?.id === paperId) {
        const index = state.agentProgress.findIndex((p) => p.agent === agent)
        if (index >= 0) {
          state.agentProgress[index] = action.payload
        } else {
          state.agentProgress.push(action.payload)
        }
      }
    },
    resetAgentProgress: (state, action: PayloadAction<number | undefined>) => {
      if (action.payload) {
        delete state.multiAgentProgress[action.payload]
        state.activePaperIds = state.activePaperIds.filter(id => id !== action.payload)
      } else {
        state.multiAgentProgress = {}
        state.agentProgress = []
        state.activePaperIds = []
      }
    },
    addActivePaperId: (state, action: PayloadAction<number>) => {
      if (!state.activePaperIds.includes(action.payload)) {
        state.activePaperIds.push(action.payload)
        state.generating = true
      }
    },
    setCurrentPaper: (state, action: PayloadAction<Paper | null>) => {
      state.currentPaper = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(generatePaper.pending, (state) => {
        state.generating = true
        state.error = null
        state.agentProgress = []
      })
      .addCase(generatePaper.fulfilled, (state, action) => {
        // We do NOT set generating = false here because it should stay true 
        // until the multi-agent workflow finishes (handled by updateAgentProgress)
        state.currentPaper = action.payload
        state.papers.unshift(action.payload)
      })
      .addCase(generatePaper.rejected, (state, action) => {
        state.generating = false
        state.error = action.error.message || 'Failed to generate paper'
      })
      .addCase(fetchPapers.fulfilled, (state, action) => {
        state.papers = action.payload
      })
      .addCase(fetchPaperById.fulfilled, (state, action) => {
        state.currentPaper = action.payload
        // Update the item in the papers list as well
        const index = state.papers.findIndex((p) => p.id === action.payload.id)
        if (index >= 0) {
          state.papers[index] = action.payload
        }
      })
      .addCase(deletePaper.fulfilled, (state, action) => {
        state.papers = state.papers.filter((p) => p.id !== action.payload)
        if (state.currentPaper?.id === action.payload) {
          state.currentPaper = null
        }
      })
      .addCase(fetchPaperTrace.pending, (state) => {
        state.traceLoading = true
      })
      .addCase(fetchPaperTrace.fulfilled, (state, action) => {
        state.paperTrace = action.payload
        state.traceLoading = false
      })
      .addCase(fetchPaperTrace.rejected, (state) => {
        state.traceLoading = false
      })
  },
})

export const { updateAgentProgress, resetAgentProgress, setCurrentPaper, addActivePaperId } = papersSlice.actions
export default papersSlice.reducer
