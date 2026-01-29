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
  searchResults: any[]
  loading: boolean
  error: string | null
}

const initialState: IndustryState = {
  news: [],
  searchResults: [],
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

export const searchIndustryNews = createAsyncThunk(
  'industry/search',
  async (topicId: number) => {
    const response = await api.post(`/api/v1/industry/search?topic_id=${topicId}`)
    return response.data
  }
)

export const addIndustryNews = createAsyncThunk(
  'industry/add',
  async (newsData: Partial<IndustryNews>) => {
    const response = await api.post('/api/v1/industry/', newsData)
    return response.data
  }
)

export const updateIndustryNews = createAsyncThunk(
  'industry/update',
  async ({ id, data }: { id: number; data: Partial<IndustryNews> }) => {
    const response = await api.put(`/api/v1/industry/${id}`, data)
    return response.data
  }
)

export const deleteIndustryNews = createAsyncThunk(
  'industry/delete',
  async (id: number) => {
    await api.delete(`/api/v1/industry/${id}`)
    return id
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
      .addCase(searchIndustryNews.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(searchIndustryNews.fulfilled, (state, action) => {
        state.loading = false
        state.searchResults = action.payload
      })
      .addCase(searchIndustryNews.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to search news'
      })
      .addCase(addIndustryNews.fulfilled, (state, action) => {
        state.news.unshift(action.payload)
      })
      .addCase(updateIndustryNews.fulfilled, (state, action) => {
        const index = state.news.findIndex((n) => n.id === action.payload.id)
        if (index !== -1) {
          state.news[index] = action.payload
        }
      })
      .addCase(deleteIndustryNews.fulfilled, (state, action) => {
        state.news = state.news.filter((n) => n.id !== action.payload)
      })
  },
})

export default industrySlice.reducer
