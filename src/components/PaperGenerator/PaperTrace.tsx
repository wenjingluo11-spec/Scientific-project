import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Timeline, Card, Tag, Typography, Spin, Empty, Button, Drawer, Descriptions, Badge, Space, Select } from 'antd'
import { ClockCircleOutlined, RobotOutlined, UserOutlined, FileSearchOutlined, EyeOutlined, HistoryOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchPaperTrace, PaperTraceItem, fetchPapers } from '@/store/slices/papersSlice'

const { Title, Text, Paragraph } = Typography
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
  const [drawerVisible, setDrawerVisible] = useState(false)

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

  const handleViewDetail = (item: PaperTraceItem) => {
    setSelectedItem(item)
    setDrawerVisible(true)
  }

  return (
    <div style={{ padding: '12px 24px' }}>
      <div style={{ marginBottom: 24, padding: '16px', background: '#f9f9f9', borderRadius: 8, border: '1px outset #eee' }}>
        <Space size="large" align="center">
          <Text strong><HistoryOutlined /> 选择回放题目：</Text>
          <Select
            placeholder="请选择要回放生成过程的选题"
            style={{ width: 450 }}
            value={selectedPaperId || undefined}
            onChange={handlePaperChange}
            showSearch
            optionFilterProp="children"
          >
            {papers.map(p => (
              <Option key={p.id} value={p.id}>
                <Space>
                  <Tag color={p.status === 'completed' ? 'success' : 'processing'}>ID:{p.id}</Tag>
                  <span style={{ fontWeight: 500 }}>{p.title}</span>
                </Space>
              </Option>
            ))}
          </Select>
          {selectedPaperId && (
            <Text type="secondary" style={{ fontSize: 12 }}>
              共 {paperTrace.length} 个交互记录
            </Text>
          )}
        </Space>
      </div>

      <Spin spinning={traceLoading}>
        {!selectedPaperId ? (
          <Empty
            image={Empty.PRESENTED_IMAGE_SIMPLE}
            description="请先在上方下拉框选择一个生成任务以查看回放"
          />
        ) : paperTrace.length === 0 && !traceLoading ? (
          <Empty description="该任务暂无交互回放记录" />
        ) : (
          <div style={{ display: 'flex' }}>
            {/* 左侧时间轴 */}
            <div style={{ width: '40%', paddingRight: 24, borderRight: '1px solid #f0f0f0' }}>
              <Title level={4} style={{ marginBottom: 24, display: 'flex', alignItems: 'center', gap: 8 }}>
                <ClockCircleOutlined /> 生成工作流时间轴
              </Title>
              <Timeline mode="left">
                {paperTrace.map((item) => (
                  <Timeline.Item
                    key={item.id}
                    label={new Date(item.created_at).toLocaleTimeString()}
                    dot={
                      <RobotOutlined style={{ fontSize: '16px', color: agentRoleColors[item.agent_role] || 'blue' }} />
                    }
                  >
                    <Card
                      size="small"
                      hoverable
                      onClick={() => handleViewDetail(item)}
                      style={{
                        cursor: 'pointer',
                        borderLeft: `4px solid ${item.step_name?.includes('Revision') ? '#faad14' : '#1890ff'}`
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div>
                          <Text strong>{item.step_name || 'Processing'}</Text>
                          <div style={{ marginTop: 4 }}>
                            <Tag color={agentRoleColors[item.agent_role]}>
                              {agentRoleNames[item.agent_role] || item.agent_role}
                            </Tag>
                          </div>
                        </div>
                        <Button type="link" size="small" icon={<EyeOutlined />} />
                      </div>
                      {item.model_signature && (
                        <div style={{ marginTop: 8, fontSize: 12, color: '#8c8c8c' }}>
                          {item.model_signature.replace(/-- Generated by | --/g, '')}
                        </div>
                      )}
                    </Card>
                  </Timeline.Item>
                ))}
              </Timeline>
            </div>

            {/* 右侧详情预览 (默认显示最新的或选中的) */}
            <div style={{ width: '60%', paddingLeft: 24 }}>
              <Empty description="点击左侧时间轴查看详细交互内容" image={Empty.PRESENTED_IMAGE_SIMPLE} />
            </div>
          </div>
        )}

        {/* 详情抽屉 */}
        <Drawer
          title={
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', width: '100%' }}>
              <Space>
                <RobotOutlined />
                <span>{selectedItem?.step_name}</span>
                <Tag color={selectedItem ? agentRoleColors[selectedItem.agent_role] : 'default'}>
                  {selectedItem ? (agentRoleNames[selectedItem.agent_role] || selectedItem.agent_role) : ''}
                </Tag>
              </Space>
              {selectedItem?.model_signature && (
                <Tag icon={<UserOutlined />} color="gold">
                  {selectedItem.model_signature.replace(/-- | --/g, '')}
                </Tag>
              )}
            </div>
          }
          width={720}
          onClose={() => setDrawerVisible(false)}
          open={drawerVisible}
        >
          {selectedItem && (
            <div>
              <Descriptions column={1} bordered size="small">
                <Descriptions.Item label="执行时间">
                  {new Date(selectedItem.created_at).toLocaleString()}
                </Descriptions.Item>
                <Descriptions.Item label="轮次">
                  Round {selectedItem.iteration}
                </Descriptions.Item>
              </Descriptions>

              <div style={{ marginTop: 24 }}>
                <Title level={5}>📥 输入指令 (Input Context)</Title>
                <div style={{
                  background: '#f5f5f5',
                  padding: 12,
                  borderRadius: 4,
                  border: '1px solid #d9d9d9',
                  maxHeight: 200,
                  overflow: 'auto',
                  fontFamily: 'monospace'
                }}>
                  {selectedItem.input_context || "无输入上下文"}
                </div>
              </div>

              <div style={{ marginTop: 24 }}>
                <Title level={5}>📤 输出结果 (Output Content)</Title>
                <div style={{
                  border: '1px solid #d9d9d9',
                  borderRadius: 4,
                  padding: 16,
                  minHeight: 200
                }}>
                  <ReactMarkdown>{selectedItem.output_content}</ReactMarkdown>
                </div>
              </div>
            </div>
          )}
        </Drawer>
      </Spin>
    </div>
  )
}

export default PaperTrace
