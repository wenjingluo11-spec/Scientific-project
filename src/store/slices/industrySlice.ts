import { createSlice, createAsyncThunk } from '@reduxjs/toolkit'
import { api } from '@/services/api'

export interface IndustryNews {
  id: number
  title: string
  source: string
  url: string
  content: string
  keywords: string[]
  relevance_score: number
  published_at: string
  created_at: string
}

interface IndustryState {
  news: IndustryNews[]
  loading: boolean
  error: string | null
}

const initialState: IndustryState = {
  news: [],
  loading: false,
  error: null,
}

export const fetchIndustryNews = createAsyncThunk(
  'industry/fetchNews',
  async (topicId?: number) => {
    const url = topicId ? `/api/v1/industry/news?topic_id=${topicId}` : '/api/v1/industry/news'
    const response = await api.get(url)
    return response.data
  }
)

export const refreshIndustryNews = createAsyncThunk(
  'industry/refresh',
  async (topicId: number) => {
    const response = await api.post(`/api/v1/industry/refresh?topic_id=${topicId}`)
    return response.data
  }
)

const industrySlice = createSlice({
  name: 'industry',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchIndustryNews.pending, (state) => {
        state.loading = true
      })
      .addCase(fetchIndustryNews.fulfilled, (state, action) => {
        state.loading = false
        state.news = action.payload
      })
      .addCase(fetchIndustryNews.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch news'
      })
      .addCase(refreshIndustryNews.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(refreshIndustryNews.fulfilled, (state, action) => {
        state.loading = false
        state.news = action.payload
      })
      .addCase(refreshIndustryNews.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to refresh news'
      })
  },
})

export default industrySlice.reducer
