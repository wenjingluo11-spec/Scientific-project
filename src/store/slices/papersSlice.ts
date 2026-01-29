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
  created_at: string
}

export interface AgentProgress {
  agent: string
  status: 'waiting' | 'working' | 'completed'
  message: string
  progress: number
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
  agentProgress: AgentProgress[]
  paperTrace: PaperTraceItem[] // Added
  loading: boolean
  generating: boolean
  traceLoading: boolean // Added
  error: string | null
}

const initialState: PapersState = {
  papers: [],
  currentPaper: null,
  agentProgress: [],
  paperTrace: [], // Added
  loading: false,
  generating: false,
  traceLoading: false, // Added
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
  async (topicId: number) => {
    const response = await api.post(`/api/v1/papers/generate`, { topic_id: topicId })
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
      // Check for final completion message from backend (agent: "completed")
      if (action.payload.agent === 'completed') {
        state.generating = false
        return
      }

      const index = state.agentProgress.findIndex((p) => p.agent === action.payload.agent)
      if (index >= 0) {
        state.agentProgress[index] = action.payload
      } else {
        state.agentProgress.push(action.payload)
      }
    },
    resetAgentProgress: (state) => {
      state.agentProgress = []
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

export const { updateAgentProgress, resetAgentProgress, setCurrentPaper } = papersSlice.actions
export default papersSlice.reducer
