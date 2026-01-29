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

interface PapersState {
  papers: Paper[]
  currentPaper: Paper | null
  agentProgress: AgentProgress[]
  loading: boolean
  generating: boolean
  error: string | null
}

const initialState: PapersState = {
  papers: [],
  currentPaper: null,
  agentProgress: [],
  loading: false,
  generating: false,
  error: null,
}

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

const papersSlice = createSlice({
  name: 'papers',
  initialState,
  reducers: {
    updateAgentProgress: (state, action: PayloadAction<AgentProgress>) => {
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
        state.generating = false
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
  },
})

export const { updateAgentProgress, resetAgentProgress, setCurrentPaper } = papersSlice.actions
export default papersSlice.reducer
