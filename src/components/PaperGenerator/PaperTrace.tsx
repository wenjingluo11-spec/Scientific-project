import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Timeline, Tag, Typography, Spin, Empty, Space, Select, Descriptions } from 'antd'
import { ClockCircleOutlined, RobotOutlined, UserOutlined, HistoryOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchPaperTrace, PaperTraceItem, fetchPapers } from '@/store/slices/papersSlice'

const { Title, Text } = Typography
const { Option } = Select

interface PaperTraceProps {
  paperId: number | null
}

const agentRoleColors: Record<string, string> = {
  research_director: 'purple',
  literature_researcher: 'blue',
  methodology_expert: 'cyan',
  data_analyst: 'green',
  paper_writer: 'orange',
  peer_reviewer: 'red',
  paper_revisor: 'geekblue'
}

const agentRoleNames: Record<string, string> = {
  research_director: '研究主管',
  literature_researcher: '文献调研员',
  methodology_expert: '方法论专家',
  data_analyst: '数据分析师',
  paper_writer: '论文撰写员',
  peer_reviewer: '同行评审员',
  paper_revisor: '论文修改员'
}

const PaperTrace: React.FC<PaperTraceProps> = ({ paperId: initialPaperId }) => {
  const dispatch = useDispatch<AppDispatch>()
  const { paperTrace, traceLoading, papers } = useSelector((state: RootState) => state.papers)
  const [selectedPaperId, setSelectedPaperId] = useState<number | null>(initialPaperId)
  const [selectedItem, setSelectedItem] = useState<PaperTraceItem | null>(null)

  // Ensure papers are loaded
  useEffect(() => {
    if (papers.length === 0) {
      dispatch(fetchPapers())
    }
  }, [dispatch, papers.length])

  // Fetch trace when internal selectedPaperId changes
  useEffect(() => {
    if (selectedPaperId) {
      dispatch(fetchPaperTrace(selectedPaperId))
      setSelectedItem(null) // 切换论文时清空选中
    }
  }, [selectedPaperId, dispatch])

  // Sync with prop changes (e.g. from PaperGenerator tabs or external selection)
  useEffect(() => {
    if (initialPaperId) {
      setSelectedPaperId(initialPaperId)
    }
  }, [initialPaperId])

  const handlePaperChange = (id: number) => {
    setSelectedPaperId(id)
  }

  const handleSelectItem = (item: PaperTraceItem) => {
    setSelectedItem(item)
  }

  return (
    <div style={{ padding: '12px 24px', height: '100%', display: 'flex', flexDirection: 'column' }}>
      <div style={{ marginBottom: 16, padding: '12px 16px', background: '#fafafa', borderRadius: 6, border: '1px solid #f0f0f0' }}>
        <Space size="large" align="center">
          <Text strong><HistoryOutlined /> 选择回放题目：</Text>
          <Select
            placeholder="请选择要回放生成过程的选题"
            style={{ width: 400 }}
            value={selectedPaperId || undefined}
            onChange={handlePaperChange}
            showSearch
            optionFilterProp="children"
            size="small"
          >
            {papers.map(p => (
              <Option key={p.id} value={p.id}>
                <Space>
                  <Tag color={p.status === 'completed' ? 'success' : 'processing'} style={{ margin: 0 }}>ID:{p.id}</Tag>
                  <span>{p.title}</span>
                </Space>
              </Option>
            ))}
          </Select>
          {selectedPaperId && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              共 {paperTrace.length} 条记录
            </Text>
          )}
        </Space>
      </div>

      <Spin spinning={traceLoading} style={{ flex: 1 }}>
        {!selectedPaperId ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="请先选择一个生成任务"
          />
        ) : paperTrace.length === 0 && !traceLoading ? (
          <Empty description="暂无交互记录" />
        ) : (
          <div style={{ display: 'flex', flex: 1, overflow: 'hidden', gap: 16 }}>
            {/* 左侧时间轴 - 简化版 */}
            <div style={{ width: 280, flexShrink: 0, overflow: 'auto', paddingRight: 8 }}>
              <Title level={5} style={{ marginBottom: 12, color: '#666' }}>
                <ClockCircleOutlined /> 工作流时间轴
              </Title>
              <Timeline
                items={paperTrace.map((item) => ({
                  key: item.id,
                  color: agentRoleColors[item.agent_role] || 'blue',
                  children: (
                    <div
                      onClick={() => handleSelectItem(item)}
                      style={{
                        cursor: 'pointer',
                        padding: '8px 12px',
                        borderRadius: 4,
                        background: selectedItem?.id === item.id ? '#e6f7ff' : '#fafafa',
                        border: selectedItem?.id === item.id ? '1px solid #1890ff' : '1px solid #f0f0f0',
                        transition: 'all 0.2s',
                        marginBottom: 4
                      }}
                    >
                      <div style={{ fontWeight: 500, fontSize: 13, marginBottom: 4 }}>
                        {item.step_name || 'Processing'}
                      </div>
                      <Space size={4}>
                        <Tag color={agentRoleColors[item.agent_role]} style={{ margin: 0, fontSize: 11 }}>
                          {agentRoleNames[item.agent_role] || item.agent_role}
                        </Tag>
                        <Text type="secondary" style={{ fontSize: 11 }}>
                          {new Date(item.created_at).toLocaleTimeString()}
                        </Text>
                      </Space>
                    </div>
                  )
                }))}
              />
            </div>

            {/* 右侧详情面板 */}
            <div style={{ flex: 1, overflow: 'auto', background: '#fff', borderRadius: 6, border: '1px solid #f0f0f0' }}>
              {selectedItem ? (
                <div style={{ padding: 16 }}>
                  {/* 头部信息 */}
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, paddingBottom: 12, borderBottom: '1px solid #f0f0f0' }}>
                    <Space>
                      <RobotOutlined style={{ fontSize: 18, color: agentRoleColors[selectedItem.agent_role] }} />
                      <Text strong style={{ fontSize: 16 }}>{selectedItem.step_name}</Text>
                      <Tag color={agentRoleColors[selectedItem.agent_role]}>
                        {agentRoleNames[selectedItem.agent_role] || selectedItem.agent_role}
                      </Tag>
                    </Space>
                    {selectedItem.model_signature && (
                      <Tag icon={<UserOutlined />} color="gold" style={{ margin: 0 }}>
                        {selectedItem.model_signature.replace(/-- | --/g, '')}
                      </Tag>
                    )}
                  </div>

                  {/* 基本信息 */}
                  <Descriptions column={2} size="small" style={{ marginBottom: 16 }}>
                    <Descriptions.Item label="执行时间">
                      {new Date(selectedItem.created_at).toLocaleString()}
                    </Descriptions.Item>
                    <Descriptions.Item label="迭代轮次">
                      Round {selectedItem.iteration}
                    </Descriptions.Item>
                  </Descriptions>

                  {/* 输入上下文 */}
                  <div style={{ marginBottom: 16 }}>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>📥 输入上下文</Text>
                    <div style={{
                      background: '#f6f6f6',
                      padding: 12,
                      borderRadius: 4,
                      maxHeight: 150,
                      overflow: 'auto',
                      fontSize: 12,
                      fontFamily: 'monospace',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      {selectedItem.input_context || "无输入上下文"}
                    </div>
                  </div>

                  {/* 输出结果 */}
                  <div>
                    <Text strong style={{ display: 'block', marginBottom: 8 }}>📤 输出结果</Text>
                    <div style={{
                      border: '1px solid #e8e8e8',
                      borderRadius: 4,
                      padding: 16,
                      overflow: 'auto',
                      maxHeight: 400
                    }}>
                      <ReactMarkdown>{selectedItem.output_content}</ReactMarkdown>
                    </div>
                  </div>
                </div>
              ) : (
                <div style={{ height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Empty description="点击左侧时间轴查看详情" image={Empty.PRESENTED_IMAGE_SIMPLE} />
                </div>
              )}
            </div>
          </div>
        )}
      </Spin>
    </div>
  )
}

export default PaperTrace

