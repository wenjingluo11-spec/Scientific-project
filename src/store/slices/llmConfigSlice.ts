import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit'
import { api } from '@/services/api'

export interface LLMConfig {
  id: number
  name: string
  provider: string
  base_url: string
  api_key: string  // 脱敏后的
  default_model: string
  max_tokens: number
  timeout: number
  is_primary: boolean
  created_at: string | null
  updated_at: string | null
}

export interface LLMConfigCreate {
  name: string
  provider?: string
  base_url: string
  api_key: string
  default_model: string
  max_tokens?: number
  timeout?: number
}

export interface LLMConfigUpdate {
  name?: string
  provider?: string
  base_url?: string
  api_key?: string
  default_model?: string
  max_tokens?: number
  timeout?: number
}

export interface TestConnectionRequest {
  base_url: string
  api_key: string
  model?: string
}

export interface TestConnectionResponse {
  success: boolean
  message: string
  response_time_ms?: number
}

interface LLMConfigState {
  configs: LLMConfig[]
  primaryConfig: LLMConfig | null
  loading: boolean
  error: string | null
  testResult: TestConnectionResponse | null
  testing: boolean
}

const initialState: LLMConfigState = {
  configs: [],
  primaryConfig: null,
  loading: false,
  error: null,
  testResult: null,
  testing: false,
}

// Async thunks
export const fetchConfigs = createAsyncThunk(
  'llmConfig/fetchConfigs',
  async () => {
    const response = await api.get('/api/v1/llm-configs')
    return response.data
  }
)

export const fetchPrimaryConfig = createAsyncThunk(
  'llmConfig/fetchPrimaryConfig',
  async () => {
    const response = await api.get('/api/v1/llm-configs/primary')
    return response.data
  }
)

export const createConfig = createAsyncThunk(
  'llmConfig/createConfig',
  async (config: LLMConfigCreate) => {
    const response = await api.post('/api/v1/llm-configs', config)
    return response.data
  }
)

export const updateConfig = createAsyncThunk(
  'llmConfig/updateConfig',
  async ({ id, data }: { id: number; data: LLMConfigUpdate }) => {
    const response = await api.put(`/api/v1/llm-configs/${id}`, data)
    return response.data
  }
)

export const deleteConfig = createAsyncThunk(
  'llmConfig/deleteConfig',
  async (id: number) => {
    await api.delete(`/api/v1/llm-configs/${id}`)
    return id
  }
)

export const setPrimaryConfig = createAsyncThunk(
  'llmConfig/setPrimaryConfig',
  async (id: number) => {
    const response = await api.post(`/api/v1/llm-configs/${id}/set-primary`)
    return response.data
  }
)

export const testConnection = createAsyncThunk(
  'llmConfig/testConnection',
  async (request: TestConnectionRequest) => {
    const response = await api.post('/api/v1/llm-configs/test', request)
    return response.data
  }
)

const llmConfigSlice = createSlice({
  name: 'llmConfig',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    clearTestResult: (state) => {
      state.testResult = null
    },
  },
  extraReducers: (builder) => {
    builder
      // fetchConfigs
      .addCase(fetchConfigs.pending, (state) => {
        state.loading = true
        state.error = null
      })
      .addCase(fetchConfigs.fulfilled, (state, action) => {
        state.loading = false
        state.configs = action.payload
      })
      .addCase(fetchConfigs.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '获取配置列表失败'
      })
      // fetchPrimaryConfig
      .addCase(fetchPrimaryConfig.fulfilled, (state, action) => {
        state.primaryConfig = action.payload
      })
      // createConfig
      .addCase(createConfig.pending, (state) => {
        state.loading = true
      })
      .addCase(createConfig.fulfilled, (state, action) => {
        state.loading = false
        state.configs.unshift(action.payload)
        // 如果是第一个配置，自动成为主配置
        if (action.payload.is_primary) {
          state.primaryConfig = action.payload
        }
      })
      .addCase(createConfig.rejected, (state, action) => {
        state.loading = false
        state.error = action.error.message || '创建配置失败'
      })
      // updateConfig
      .addCase(updateConfig.fulfilled, (state, action) => {
        const index = state.configs.findIndex(c => c.id === action.payload.id)
        if (index !== -1) {
          state.configs[index] = action.payload
        }
        if (action.payload.is_primary) {
          state.primaryConfig = action.payload
        }
      })
      // deleteConfig
      .addCase(deleteConfig.fulfilled, (state, action) => {
        state.configs = state.configs.filter(c => c.id !== action.payload)
        // 如果删除的是主配置，清除主配置状态
        if (state.primaryConfig?.id === action.payload) {
          state.primaryConfig = state.configs.find(c => c.is_primary) || null
        }
      })
      // setPrimaryConfig
      .addCase(setPrimaryConfig.fulfilled, (state, action) => {
        // 更新所有配置的 is_primary 状态
        state.configs = state.configs.map(c => ({
          ...c,
          is_primary: c.id === action.payload.id
        }))
        state.primaryConfig = action.payload
      })
      // testConnection
      .addCase(testConnection.pending, (state) => {
        state.testing = true
        state.testResult = null
      })
      .addCase(testConnection.fulfilled, (state, action) => {
        state.testing = false
        state.testResult = action.payload
      })
      .addCase(testConnection.rejected, (state, action) => {
        state.testing = false
        state.testResult = {
          success: false,
          message: action.error.message || '测试失败'
        }
      })
  },
})

export const { clearError, clearTestResult } = llmConfigSlice.actions
export default llmConfigSlice.reducer
