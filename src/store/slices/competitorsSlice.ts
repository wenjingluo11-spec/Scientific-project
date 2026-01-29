import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '@/services/api'

export interface Competitor {
  id: number
  topic_id: number
  title: string
  authors: string
  source: string
  url: string
  abstract: string
  citations: number
  published_at: string
  analysis: string
  created_at: string
}

interface CompetitorsState {
  competitors: Competitor[]
  loading: boolean
  error: string | null
}

const initialState: CompetitorsState = {
  competitors: [],
  loading: false,
  error: null,
}

export const fetchCompetitors = createAsyncThunk(
  'competitors/fetch',
  async (topicId: number) => {
    const response = await api.get(`/api/v1/competitors?topic_id=${topicId}`)
    return response.data
  }
)

export const analyzeCompetitor = createAsyncThunk(
  'competitors/analyze',
  async (competitorId: number) => {
    const response = await api.post(`/api/v1/competitors/${competitorId}/analyze`)
    return response.data
  }
)

const competitorsSlice = createSlice({
  name: 'competitors',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchCompetitors.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchCompetitors.fulfilled, (state, action) => {
        state.loading = false
        state.competitors = action.payload
      })
      .addCase(fetchCompetitors.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch competitors'
      })
      .addCase(analyzeCompetitor.pending, (state) => {
        // Optional: could add specific loading state per item if needed
        // For now, global loading is fine or just optimistic
      })
      .addCase(analyzeCompetitor.fulfilled, (state, action) => {
        const index = state.competitors.findIndex((c) => c.id === action.payload.id)
        if (index !== -1) {
          state.competitors[index] = action.payload
        }
      })
  },
})

export default competitorsSlice.reducer
