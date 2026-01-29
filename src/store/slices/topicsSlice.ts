import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '@/services/api'

export interface Topic {
  id: number
  title: string
  description: string
  field: string
  keywords: string[]
  status: 'pending' | 'processing' | 'completed'
  created_at: string
  updated_at: string
}

export interface TopicSuggestion {
  title: string
  description: string
  field: string
  keywords: string[]
  novelty_score: number
  feasibility_score: number
  reasoning: string
  model_signature?: string // Added
}

export interface RecommendationHistory {
  id: number
  research_field: string
  keywords: string[]
  description: string | null
  suggestions: TopicSuggestion[]
  created_at: string
}

export interface DiscoveryResponse {
  suggestions: TopicSuggestion[]
  recommendation_id?: number
  model_signature?: string // Added
}

interface TopicsState {
  topics: Topic[]
  loading: boolean
  error: string | null
  selectedTopic: Topic | null
  suggestions: TopicSuggestion[]
  discovering: boolean
  recommendationHistory: RecommendationHistory[]
  historyLoading: boolean
}

const initialState: TopicsState = {
  topics: [],
  loading: false,
  error: null,
  selectedTopic: null,
  suggestions: [],
  discovering: false,
  recommendationHistory: [],
  historyLoading: false,
}

export const fetchTopics = createAsyncThunk('topics/fetchTopics', async () => {
  const response = await api.get('/api/v1/topics')
  return response.data
})

export const createTopic = createAsyncThunk('topics/createTopic', async (topic: Partial<Topic>) => {
  const response = await api.post('/api/v1/topics', topic)
  return response.data
})

export const searchTopics = createAsyncThunk('topics/searchTopics', async (query: string) => {
  const response = await api.get(`/api/v1/topics/search?q=${query}`)
  return response.data
})

export const discoverTopics = createAsyncThunk(
  'topics/discoverTopics',
  async (params: {
    research_field: string
    keywords: string[]
    description?: string
    num_suggestions?: number
  }) => {
    const response = await api.post('/api/v1/topics/ai-discover', params)
    return response.data
  }
)

export const batchCreateTopics = createAsyncThunk(
  'topics/batchCreateTopics',
  async (topics: Partial<Topic>[]) => {
    const response = await api.post('/api/v1/topics/batch-create', { topics })
    return response.data
  }
)

export const fetchRecommendationHistory = createAsyncThunk(
  'topics/fetchRecommendationHistory',
  async (params?: { limit?: number; offset?: number }) => {
    const limit = params?.limit || 10
    const offset = params?.offset || 0
    const response = await api.get(`/api/v1/topics/recommendations?limit=${limit}&offset=${offset}`)
    return response.data
  }
)

export const loadHistoricalRecommendation = createAsyncThunk(
  'topics/loadHistoricalRecommendation',
  async (recommendationId: number) => {
    const response = await api.get(`/api/v1/topics/recommendations/${recommendationId}`)
    return response.data
  }
)

const topicsSlice = createSlice({
  name: 'topics',
  initialState,
  reducers: {
    setSelectedTopic: (state, action: PayloadAction<Topic | null>) => {
      state.selectedTopic = action.payload
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchTopics.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchTopics.fulfilled, (state, action) => {
        state.loading = false
        state.topics = action.payload
      })
      .addCase(fetchTopics.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || 'Failed to fetch topics'
      })
      .addCase(createTopic.fulfilled, (state, action) => {
        state.topics.unshift(action.payload)
      })
      .addCase(searchTopics.fulfilled, (state, action) => {
        state.topics = action.payload
      })
      .addCase(discoverTopics.pending, (state) => {
        state.discovering = true
        state.error = null
      })
      .addCase(discoverTopics.fulfilled, (state, action) => {
        state.discovering = false
        // Inject model_signature into suggestions if present in payload
        const signature = (action.payload as any).model_signature
        if (signature) {
            state.suggestions = action.payload.suggestions.map((s: TopicSuggestion) => ({
                ...s,
                model_signature: signature
            }))
        } else {
            state.suggestions = action.payload.suggestions
        }
      })
      .addCase(discoverTopics.rejected, (state, action) => {
        state.discovering = false
        state.error = action.error.message || 'Failed to discover topics'
      })
      .addCase(batchCreateTopics.fulfilled, (state, action) => {
        state.topics = [...action.payload.created, ...state.topics]
      })
      .addCase(fetchRecommendationHistory.pending, (state) => {
        state.historyLoading = true
      })
      .addCase(fetchRecommendationHistory.fulfilled, (state, action) => {
        state.historyLoading = false
        state.recommendationHistory = action.payload
      })
      .addCase(fetchRecommendationHistory.rejected, (state) => {
        state.historyLoading = false
      })
      .addCase(loadHistoricalRecommendation.fulfilled, (state, action) => {
        state.suggestions = action.payload.suggestions
      })
  },
})

export const { setSelectedTopic, clearError } = topicsSlice.actions
export default topicsSlice.reducer
