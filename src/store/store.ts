import { configureStore } from '@reduxjs/toolkit'
import topicsReducer from './slices/topicsSlice'
import papersReducer from './slices/papersSlice'
import industryReducer from './slices/industrySlice'
import competitorsReducer from './slices/competitorsSlice'
import llmConfigReducer from './slices/llmConfigSlice'

export const store = configureStore({
  reducer: {
    topics: topicsReducer,
    papers: papersReducer,
    industry: industryReducer,
    competitors: competitorsReducer,
    llmConfig: llmConfigReducer,
  },
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch

