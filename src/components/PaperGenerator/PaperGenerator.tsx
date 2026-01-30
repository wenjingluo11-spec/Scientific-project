import React, { useEffect, useState } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, Steps, Button, Progress, Space, Typography, Divider, message, Select, Tabs, Switch, Tag, Badge } from 'antd'
import { RobotOutlined, FileTextOutlined, DownloadOutlined, HistoryOutlined, PlusOutlined, PlayCircleOutlined, RocketOutlined, DownOutlined, UpOutlined } from '@ant-design/icons'
import ReactMarkdown from 'react-markdown'
import type { RootState, AppDispatch } from '@/store/store'
import { generatePaper, resetAgentProgress, fetchPapers, addActivePaperId, updateAgentProgress } from '@/store/slices/papersSlice'
import { fetchTopics } from '@/store/slices/topicsSlice'
import { websocketService } from '@/services/websocket'
import PaperHistory from './PaperHistory'
import PaperTrace from './PaperTrace'

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
  const { currentPaper, agentProgress, generating, papers: allPapers } = useSelector((state: RootState) => state.papers)

  const [selectedTheme, setSelectedTheme] = useState<string | null>(null)
  const [selectedTopicIds, setSelectedTopicIds] = useState<number[]>([])
  const [activeTab, setActiveTab] = useState('generate')

  // Extract unique themes from topics
  const themes = Array.from(new Set(topics.map(t => t.specific_topic).filter(Boolean))) as string[]

  // Filter topics based on selected theme
  const filteredTopics = selectedTheme
    ? topics.filter(t => t.specific_topic === selectedTheme)
    : []

  const { multiAgentProgress, activePaperIds } = useSelector((state: RootState) => state.papers)
  const [expandedPaperIds, setExpandedPaperIds] = useState<number[]>([]) // Track expanded states

  useEffect(() => {
    dispatch(fetchTopics())
    dispatch(fetchPapers())
  }, [dispatch])

  // Auto-select all topics under the theme when theme changes
  useEffect(() => {
    if (selectedTheme) {
      const themeTopics = topics.filter(t => t.specific_topic === selectedTheme)
      setSelectedTopicIds(themeTopics.map(t => t.id))
    } else {
      setSelectedTopicIds([])
    }
  }, [selectedTheme, topics])

  const toggleExpand = (paperId: number) => {
    setExpandedPaperIds(prev =>
      prev.includes(paperId)
        ? prev.filter(id => id !== paperId)
        : [...prev, paperId]
    )
  }

  const handleGenerate = async () => {
    if (selectedTopicIds.length === 0) {
      message.warning('请至少选择一个选题')
      return
    }

    try {
      message.info(`正在并行启动 ${selectedTopicIds.length} 个生成任务...`)

      // Parallel Batch Mode - Loop and trigger each independently
      for (const topicId of selectedTopicIds) {
        // We pass the single ID in a list to the backend API but it will treat it as a single-topic paper task
        const result = await dispatch(generatePaper([topicId])).unwrap()
        dispatch(addActivePaperId(result.id))
        websocketService.connect(result.id)
      }

      message.success('所有生成任务已成功启动！')
    } catch (error) {
      message.error('生成启动失败，请重试')
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
                    <div style={{ display: 'flex', gap: 24, alignItems: 'flex-start', flexWrap: 'wrap' }}>
                      <div style={{ flex: 1, minWidth: 200 }}>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>选择主题/细分方向：</Text>
                        <Select
                          style={{ width: '100%' }}
                          placeholder="请选择研究主题"
                          onChange={(value) => setSelectedTheme(value)}
                          value={selectedTheme}
                          size="large"
                        >
                          {themes.map((theme) => (
                            <Option key={theme} value={theme}>
                              {theme}
                            </Option>
                          ))}
                        </Select>
                      </div>

                      <div style={{ flex: 2, minWidth: 300 }}>
                        <Text strong style={{ display: 'block', marginBottom: 8 }}>选择选题 (可多选)：</Text>
                        <Select
                          mode="multiple"
                          style={{ width: '100%' }}
                          placeholder={selectedTheme ? "已默认选中全部选题，可在此取消不想要的任务" : "请先选择左侧主题"}
                          onChange={(values) => setSelectedTopicIds(values)}
                          value={selectedTopicIds}
                          disabled={!selectedTheme}
                          size="large"
                          optionFilterProp="children"
                        >
                          {filteredTopics.map((topic) => (
                            <Option key={topic.id} value={topic.id}>
                              {topic.title}
                            </Option>
                          ))}
                        </Select>
                      </div>

                      <div style={{ paddingTop: 32 }}>
                        <Button
                          type="primary"
                          icon={<RocketOutlined />}
                          onClick={handleGenerate}
                          disabled={selectedTopicIds.length === 0}
                          size="large"
                          danger
                        >
                          批量启动并行生成
                        </Button>
                      </div>
                    </div>

                    {(generating || activePaperIds.length > 0) && (
                      <>
                        <Divider />
                        <Title level={5}>实施生成任务队列</Title>

                        {/* Vertical list of active tasks */}
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                          {activePaperIds.map(paperId => {
                            const progress = multiAgentProgress[paperId] || [];
                            const lastProgress = progress[progress.length - 1];
                            const currentStep = lastProgress ? Object.keys(agentNames).indexOf(lastProgress.agent) : 0;
                            const isExpanded = expandedPaperIds.includes(paperId);
                            // Find topic info: first check if we have the paper in our history which is more reliable
                            const paperRecord = allPapers.find(p => p.id === paperId);
                            // If paper record exists, try to find topic from topic list by topic_id
                            let topicTitle = '正在加载选题信息...';

                            if (paperRecord) {
                              // If we have the paper record, we can use its title (which might be "Research on...")
                              // Or better, find the original topic
                              const t = topics.find(t => t.id === paperRecord.topic_id);
                              if (t) topicTitle = t.title;
                              else topicTitle = paperRecord.title; // Fallback to paper title
                            } else {
                              // If paper record not yet loaded (race condition), try to find by reverse lookup?
                              // Actually, lastProgress might not contain topicId. 
                              // We rely on the topic list having the ID we selected.
                              // But `selectedTopicIds` are TOPIC IDs not PAPER IDs.
                              // We need a map. For now, let's use the Paper title if available.
                              topicTitle = `生成任务 #${paperId}`;
                            }

                            return (
                              <Card
                                key={paperId}
                                size="small"
                                style={{
                                  borderRadius: 8,
                                  border: '1px solid #e6f7ff',
                                  transition: 'all 0.3s'
                                }}
                                headStyle={{
                                  backgroundColor: '#fafafa',
                                  borderBottom: isExpanded ? '1px solid #f0f0f0' : 'none'
                                }}
                                title={
                                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', cursor: 'pointer' }} onClick={() => toggleExpand(paperId)}>
                                    <Space>
                                      <Badge status={lastProgress?.status === 'completed' ? 'success' : 'processing'} />
                                      <Text strong>任务 #{paperId}:</Text>
                                      <Text type="secondary" style={{ maxWidth: 300 }} ellipsis>{topicTitle}</Text>
                                    </Space>
                                    <Space>
                                      <Tag color={lastProgress?.status === 'completed' ? 'green' : 'blue'}>
                                        {lastProgress ? agentNames[lastProgress.agent] : '准备中...'}
                                      </Tag>
                                      <Button type="text" size="small" icon={isExpanded ? <UpOutlined /> : <DownOutlined />}>
                                        {isExpanded ? '收起详情' : '展开进度'}
                                      </Button>
                                    </Space>
                                  </div>
                                }
                              >
                                <div style={{ padding: '8px 12px' }}>
                                  {/* Percentage Progress Bar (Always visible) */}
                                  <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                                    <div style={{ flex: 1 }}>
                                      <Progress
                                        percent={lastProgress?.progress || 0}
                                        size="default"
                                        status={lastProgress?.status === 'completed' ? 'success' : 'active'}
                                        strokeWidth={10}
                                        showInfo={false}
                                      />
                                    </div>
                                    <Text type="secondary" style={{ minWidth: 40, textAlign: 'right' }}>{lastProgress?.progress || 0}%</Text>
                                  </div>

                                  {/* Detailed Content (Shown ONLY when expanded) */}
                                  {isExpanded && (
                                    <div style={{ marginTop: 24, padding: '0 8px' }}>
                                      <Divider style={{ margin: '16px 0' }} />
                                      <Steps
                                        size="small"
                                        current={currentStep}
                                        items={Object.entries(agentNames).map(([key, name]) => ({
                                          title: <span style={{ fontSize: '12px' }}>{name}</span>,
                                        }))}
                                        style={{ marginBottom: 20 }}
                                      />
                                      {lastProgress && (
                                        <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
                                          <Card size="small" style={{ backgroundColor: '#f9f9f9', border: 'none' }}>
                                            <Space align="start">
                                              <RobotOutlined style={{ marginTop: 4, color: '#1890ff' }} />
                                              <div>
                                                <Text strong style={{ fontSize: '13px' }}>{agentNames[lastProgress.agent]} 状态反馈：</Text>
                                                <Paragraph style={{ margin: 0, color: '#555', fontSize: '13px' }}>
                                                  {lastProgress.message}
                                                </Paragraph>
                                              </div>
                                            </Space>
                                          </Card>

                                          {/* Multi-dimensional Scores */}
                                          {lastProgress.detailedScores && (
                                            <Card
                                              size="small"
                                              title={<Text strong style={{ fontSize: '13px' }}><HistoryOutlined /> ICLR/NeurIPS 维度评分详情 (1-10)</Text>}
                                              style={{ background: '#fff', border: '1px solid #f0f0f0' }}
                                            >
                                              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 12 }}>
                                                {[
                                                  { label: '创新性', key: 'novelty', color: '#722ed1' },
                                                  { label: '技术质量', key: 'quality', color: '#2f54eb' },
                                                  { label: '清晰度', key: 'clarity', color: '#13c2c2' },
                                                  { label: '综合总分', key: 'total', color: '#faad14', isBold: true }
                                                ].map(item => (
                                                  <div key={item.key} style={{ textAlign: 'center' }}>
                                                    <div style={{ fontSize: '12px', color: '#8c8c8c', marginBottom: 4 }}>{item.label}</div>
                                                    <div style={{
                                                      fontSize: item.isBold ? '20px' : '16px',
                                                      fontWeight: 'bold',
                                                      color: item.color
                                                    }}>
                                                      {(lastProgress.detailedScores as any)[item.key]?.toFixed(1) || '0.0'}
                                                    </div>
                                                    <Progress
                                                      percent={(lastProgress.detailedScores as any)[item.key] * 10}
                                                      size="small"
                                                      showInfo={false}
                                                      strokeColor={item.color}
                                                      style={{ marginTop: 4 }}
                                                    />
                                                  </div>
                                                ))}
                                              </div>
                                            </Card>
                                          )}
                                        </div>
                                      )}
                                    </div>
                                  )}
                                </div>
                              </Card>
                            );
                          })}
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
                    <div style={{ marginBottom: 24, padding: '16px', background: '#fafafa', borderRadius: 8, display: 'flex', alignItems: 'center', gap: 24 }}>
                      <div>
                        <Text type="secondary" style={{ fontSize: 12, display: 'block', marginBottom: 4 }}>最终评审均分 (1-10)</Text>
                        <Title level={2} style={{ margin: 0, color: currentPaper.quality_score >= 8.5 ? '#722ed1' : currentPaper.quality_score >= 6.5 ? '#52c41a' : '#faad14' }}>
                          {currentPaper.quality_score.toFixed(1)}
                        </Title>
                      </div>
                      <div style={{ flex: 1 }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 8 }}>
                          <Text strong>论文综合质量</Text>
                          <Tag color={currentPaper.quality_score >= 8.5 ? 'purple' : currentPaper.quality_score >= 6.5 ? 'green' : 'orange'}>
                            {currentPaper.quality_score >= 8.5 ? 'Strong Accept (顶会级)' : currentPaper.quality_score >= 6.5 ? 'Accept (推荐录用)' : 'Borderline (待改进)'}
                          </Tag>
                        </div>
                        <Progress
                          percent={currentPaper.quality_score * 10}
                          strokeColor={{
                            '0%': '#ff4d4f',
                            '50%': '#faad14',
                            '100%': '#52c41a',
                          }}
                          status="active"
                          showInfo={false}
                        />
                      </div>
                    </div>

                    {/* Detailed Dimension Scores */}
                    {currentPaper.detailed_scores && (
                      <Card
                        size="small"
                        title={<Text strong style={{ fontSize: '13px' }}><HistoryOutlined /> 维度考核详情 (ICLR / NeurIPS 标准)</Text>}
                        style={{ marginBottom: 24, border: '1px solid #f0f0f0' }}
                        bodyStyle={{ padding: '16px 24px' }}
                      >
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: 24 }}>
                          {[
                            { label: '技术创新性 (Novelty)', key: 'novelty', color: '#722ed1', desc: '方法原创性与贡献度' },
                            { label: '实证质量 (Quality)', key: 'quality', color: '#2f54eb', desc: '实验严谨性与SOTA对比' },
                            { label: '行文清晰度 (Clarity)', key: 'clarity', color: '#13c2c2', desc: '逻辑严密性与数学表达' },
                            { label: '综合影响力 (Impact)', key: 'total', color: '#faad14', desc: '领域贡献与长远影响' }
                          ].map(item => (
                            <div key={item.key}>
                              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 4 }}>
                                <Text style={{ fontSize: '12px', color: '#8c8c8c' }}>{item.label}</Text>
                                <Text strong style={{ color: item.color, fontSize: '16px' }}>
                                  {(currentPaper.detailed_scores as any)[item.key]?.toFixed(1) || '0.0'}
                                </Text>
                              </div>
                              <Progress
                                percent={(currentPaper.detailed_scores as any)[item.key] * 10}
                                size="small"
                                showInfo={false}
                                strokeColor={item.color}
                              />
                              <Text type="secondary" style={{ fontSize: '10px', display: 'block', marginTop: 4 }}>{item.desc}</Text>
                            </div>
                          ))}
                        </div>
                      </Card>
                    )}

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
            key: 'trace',
            label: (
              <span>
                <PlayCircleOutlined />
                生成过程回放
              </span>
            ),
            children: (
              <Card>
                <PaperTrace paperId={currentPaper?.id || null} />
              </Card>
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
