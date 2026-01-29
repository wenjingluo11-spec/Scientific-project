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
  searchResults: any[]
  loading: boolean
  error: string | null
}

const initialState: CompetitorsState = {
  competitors: [],
  searchResults: [],
  loading: false,
  error: null,
}

export const fetchCompetitors = createAsyncThunk(
  'competitors/fetch',
  async (topicId: number) => {
    const response = await api.get(`/api/v1/competitors/?topic_id=${topicId}`)
    return response.data
  }
)

export const searchCompetitors = createAsyncThunk(
  'competitors/search',
  async (topicId: number) => {
    const response = await api.post(`/api/v1/competitors/search?topic_id=${topicId}`)
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

export const addCompetitor = createAsyncThunk(
  'competitors/add',
  async (compData: Partial<Competitor>) => {
    const response = await api.post('/api/v1/competitors/', compData)
    return response.data
  }
)

export const updateCompetitor = createAsyncThunk(
  'competitors/update',
  async ({ id, data }: { id: number; data: Partial<Competitor> }) => {
    const response = await api.put(`/api/v1/competitors/${id}`, data)
    return response.data
  }
)

export const deleteCompetitor = createAsyncThunk(
  'competitors/delete',
  async (id: number) => {
    await api.delete(`/api/v1/competitors/${id}`)
    return id
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
      .addCase(searchCompetitors.pending, (state) => {
        state.loading = true
      })
      .addCase(searchCompetitors.fulfilled, (state, action) => {
        state.loading = false
        state.searchResults = action.payload
      })
      .addCase(searchCompetitors.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to search competitors'
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
      .addCase(addCompetitor.fulfilled, (state, action) => {
        state.competitors.unshift(action.payload)
      })
      .addCase(updateCompetitor.fulfilled, (state, action) => {
        const index = state.competitors.findIndex((c) => c.id === action.payload.id)
        if (index !== -1) {
          state.competitors[index] = action.payload
        }
      })
      .addCase(deleteCompetitor.fulfilled, (state, action) => {
        state.competitors = state.competitors.filter((c) => c.id !== action.payload)
      })
  },
})

export default competitorsSlice.reducer
