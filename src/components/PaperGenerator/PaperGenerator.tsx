import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, Steps, Button, Progress, Space, Typography, Divider, message, Select, Tabs } from 'antd'
import { RobotOutlined, FileTextOutlined, DownloadOutlined, HistoryOutlined, PlusOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { RootState, AppDispatch } from '@/store/store'
import { generatePaper, resetAgentProgress, fetchPapers } from '@/store/slices/papersSlice'
import { fetchTopics } from '@/store/slices/topicsSlice'
import { websocketService } from '@/services/websocket'
import PaperHistory from './PaperHistory'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

const agentNames: Record<string, string> = {
  research_director: '研究主管',
  literature_researcher: '文献调研员',
  methodology_expert: '方法论专家',
  data_analyst: '数据分析师',
  paper_writer: '论文撰写员',
  peer_reviewer: '同行评审员',
  completed: '审核完成',
}

const PaperGenerator: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { topics } = useSelector((state: RootState) => state.topics)
  const { currentPaper, agentProgress, generating } = useSelector((state: RootState) => state.papers)
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState('generate')

  useEffect(() => {
    dispatch(fetchTopics())
    dispatch(fetchPapers())
  }, [dispatch])

  const handleGenerate = async () => {
    if (!selectedTopicId) {
      message.warning('请先选择一个选题')
      return
    }

    try {
      dispatch(resetAgentProgress())
      const result = await dispatch(generatePaper(selectedTopicId)).unwrap()
      websocketService.connect(result.id)
      message.success('论文生成已启动！')
    } catch (error) {
      message.error('生成失败，请重试')
    }
  }

  const handleExport = async () => {
    if (!currentPaper) return

    if (window.electronAPI) {
      const result = await window.electronAPI.saveFile(
        `${currentPaper.title}.md`,
        currentPaper.content
      )
      if (result.success) {
        message.success('导出成功！')
      }
    } else {
      // Web fallback
      const blob = new Blob([currentPaper.content], { type: 'text/markdown' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${currentPaper.title}.md`
      a.click()
      URL.revokeObjectURL(url)
      message.success('导出成功！')
    }
  }

  const getCurrentStep = () => {
    if (agentProgress.length === 0) return 0
    const lastProgress = agentProgress[agentProgress.length - 1]
    const agents = Object.keys(agentNames)
    const index = agents.findIndex((agent) => agent === lastProgress.agent)
    return index >= 0 ? index : 0
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>多智能体论文生成</Title>
      </div>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'generate',
            label: (
              <span>
                <PlusOutlined />
                生成论文
              </span>
            ),
            children: (
              <>
                <Paragraph>
                  选择一个研究选题，AI 智能体团队将协作为您生成高质量的学术论文初稿。
                </Paragraph>

                <Card style={{ marginBottom: 24 }}>
                  <Space direction="vertical" style={{ width: '100%' }} size="large">
                    <div>
                      <Text strong style={{ marginRight: 16 }}>选择选题：</Text>
                      <Select
                        style={{ width: 400 }}
                        placeholder="请选择一个研究选题"
                        onChange={(value) => setSelectedTopicId(value)}
                        value={selectedTopicId}
                      >
                        {topics.map((topic) => (
                          <Option key={topic.id} value={topic.id}>
                            {topic.title}
                          </Option>
                        ))}
                      </Select>
                      <Button
                        type="primary"
                        icon={<RobotOutlined />}
                        onClick={handleGenerate}
                        loading={generating}
                        disabled={!selectedTopicId}
                        style={{ marginLeft: 16 }}
                      >
                        开始生成
                      </Button>
                    </div>

                    {generating && (
                      <>
                        <Divider />
                        <div>
                          <Title level={5}>智能体工作流程</Title>
                          <Steps
                            current={getCurrentStep()}
                            items={Object.entries(agentNames).map(([key, name]) => ({
                              title: name,
                              icon: <RobotOutlined />,
                            }))}
                          />
                        </div>

                        <Divider />
                        <div>
                          <Title level={5}>实时进度</Title>
                          {agentProgress.filter(p => p.agent !== 'completed').map((progress, index) => (
                            <Card
                              key={index}
                              size="small"
                              style={{ marginBottom: 12 }}
                              title={
                                <Space>
                                  <RobotOutlined />
                                  <Text strong>{agentNames[progress.agent] || progress.agent}</Text>
                                </Space>
                              }
                            >
                              <Paragraph>{progress.message}</Paragraph>
                              <Progress percent={progress.progress} status={progress.status === 'completed' ? 'success' : 'active'} />
                            </Card>
                          ))}
                        </div>
                      </>
                    )}
                  </Space>
                </Card>

                {currentPaper && (
                  <Card
                    title={
                      <Space>
                        <FileTextOutlined />
                        <Text strong>生成的论文</Text>
                      </Space>
                    }
                    extra={
                      <Button icon={<DownloadOutlined />} onClick={handleExport}>
                        导出论文
                      </Button>
                    }
                  >
                    <div style={{ marginBottom: 16 }}>
                      <Text strong>质量评分：</Text>
                      <Progress
                        percent={currentPaper.quality_score}
                        strokeColor={{
                          '0%': '#108ee9',
                          '100%': '#87d068',
                        }}
                        style={{ width: 200, marginLeft: 16 }}
                      />
                    </div>
                    <Divider />
                    <div style={{ maxHeight: 600, overflow: 'auto', padding: '0 16px' }}>
                      <ReactMarkdown>{currentPaper.content}</ReactMarkdown>
                    </div>
                  </Card>
                )}
              </>
            ),
          },
          {
            key: 'history',
            label: (
              <span>
                <HistoryOutlined />
                论文历史记录
              </span>
            ),
            children: (
              <Card>
                <PaperHistory onView={() => setActiveTab('generate')} />
              </Card>
            ),
          },
        ]}
      />
    </div>
  )
}

export default PaperGenerator
