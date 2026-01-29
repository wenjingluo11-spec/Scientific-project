import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, Select, List, Tag, Button, Space, Typography, Divider, Tabs } from 'antd'
import { SearchOutlined, BarChartOutlined, AreaChartOutlined, SettingOutlined, PlusOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchCompetitors, analyzeCompetitor, searchCompetitors, addCompetitor } from '@/store/slices/competitorsSlice'
import { message } from 'antd'
import CompetitorManagement from './CompetitorManagement'
import { fetchTopics } from '@/store/slices/topicsSlice'

const { Title, Text, Paragraph } = Typography
const { Option } = Select

const dateToLocaleString = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

const CompetitorAnalysis: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { topics } = useSelector((state: RootState) => state.topics)
  const { competitors, searchResults, loading } = useSelector((state: RootState) => state.competitors)
  const [selectedTopicId, setSelectedTopicId] = useState<number | null>(null)
  const [activeTab, setActiveTab] = useState('live')

  useEffect(() => {
    dispatch(fetchTopics())
    dispatch(fetchCompetitors())
  }, [dispatch])

  const handleAIsSearch = () => {
    if (selectedTopicId) {
      dispatch(searchCompetitors(selectedTopicId))
    }
  }

  const handleSaveComp = async (item: any) => {
    try {
      await dispatch(addCompetitor({
        ...item,
        topic_id: selectedTopicId
      })).unwrap()
      message.success('已添加到竞品库')
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleTopicChange = (value: number) => {
    setSelectedTopicId(value)
    dispatch({ type: 'competitors/search/fulfilled', payload: [] })
    dispatch(fetchCompetitors(value))
  }

  const handleFetchExisting = () => {
    if (selectedTopicId) {
      dispatch(fetchCompetitors(selectedTopicId))
    }
  }

  const handleAnalyze = (competitorId: number) => {
    dispatch(analyzeCompetitor(competitorId))
  }

  return (
    <div>
      <Title level={3}>竞品分析系统</Title>
      <Paragraph>
        选择研究选题，系统将自动搜索并分析同领域的相关论文。
      </Paragraph>

      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>选择选题：</Text>
          <Select
            style={{ width: 400 }}
            placeholder="请选择一个研究选题"
            onChange={handleTopicChange}

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
            icon={<SearchOutlined />}
            onClick={handleAIsSearch}
            disabled={!selectedTopicId}
            loading={loading}
          >
            AI 全网搜索竞品
          </Button>
        </Space>
      </Card>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'live',
            label: (
              <span>
                <AreaChartOutlined />
                实时检索分析
              </span>
            ),
            children: (
              <>
                <div style={{ marginBottom: 16, display: 'flex', justifyContent: 'flex-end', gap: 12 }}>
                  <Button
                    icon={<PlusOutlined />}
                    onClick={() => setActiveTab('manage')}
                    disabled={!selectedTopicId}
                  >
                    手动录入竞品
                  </Button>
                </div>
                <List
                  grid={{ gutter: 16, column: 1 }}
                  dataSource={searchResults}
                  loading={loading}
                  renderItem={(item) => (
                    <List.Item>
                      <Card
                        title={
                          <Space direction="vertical" style={{ width: '100%' }}>
                            <Text strong>{item.title}</Text>
                            <Space wrap>
                              <Tag color="orange">引用数: {item.citations}</Tag>
                              <Tag color="blue">来源: {item.source}</Tag>
                              <Text type="secondary">
                                发布日期: {item.published_at || '-'}
                              </Text>
                            </Space>
                          </Space>
                        }
                        extra={
                          <Space>
                            <Button
                              type="primary"
                              icon={<PlusOutlined />}
                              onClick={() => handleSaveComp(item)}
                            >
                              选用竞品
                            </Button>
                            {item.url && (
                              <Button type="link" href={item.url} target="_blank">
                                查看原文
                              </Button>
                            )}
                          </Space>
                        }
                      >
                        <Paragraph>
                          <Text strong>作者：</Text> {item.authors}
                        </Paragraph>
                        <Paragraph ellipsis={{ rows: 2, expandable: true }}>
                          <Text strong>摘要：</Text> {item.abstract}
                        </Paragraph>
                      </Card>
                    </List.Item>
                  )}
                />
              </>
            ),
          },
          {
            key: 'manage',
            label: (
              <span>
                <SettingOutlined />
                管理竞品库 ({competitors.length})
              </span>
            ),
            children: <CompetitorManagement topicId={selectedTopicId} />,
          },
        ]}
      />
    </div>
  )
}

export default CompetitorAnalysis
