import React, { useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import { Card, List, Tag, Button, Space, Typography, Empty, Select, Tabs } from 'antd'
import { ReloadOutlined, LinkOutlined, ClockCircleOutlined, MonitorOutlined, SettingOutlined, PlusOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import { fetchIndustryNews, searchIndustryNews, addIndustryNews } from '@/store/slices/industrySlice'
import { message } from 'antd'
import IndustryManagement from './IndustryManagement'

const { Title, Text, Paragraph } = Typography

const dateToLocaleString = (dateStr: string) => {
  if (!dateStr) return '-'
  try {
    return new Date(dateStr).toLocaleDateString('zh-CN')
  } catch {
    return dateStr
  }
}

const IndustryMonitor: React.FC = () => {
  const dispatch = useDispatch<AppDispatch>()
  const { news, searchResults, loading } = useSelector((state: RootState) => state.industry)
  const { topics } = useSelector((state: RootState) => state.topics)
  const [selectedTopicId, setSelectedTopicId] = React.useState<number | null>(null)
  const [activeTab, setActiveTab] = React.useState('live')

  useEffect(() => {
    dispatch(fetchIndustryNews())
    // Fetch topics for the dropdown
    import('@/store/slices/topicsSlice').then(({ fetchTopics }) => {
      dispatch(fetchTopics())
    })
  }, [dispatch])

  const handleSearch = () => {
    if (selectedTopicId) {
      dispatch(searchIndustryNews(selectedTopicId))
    }
  }

  const handleSaveNews = async (item: any) => {
    try {
      await dispatch(addIndustryNews({
        ...item,
        topic_id: selectedTopicId
      })).unwrap()
      message.success('已添加到管理动态')
    } catch (error) {
      message.error('添加失败')
    }
  }

  const handleTopicChange = (value: number) => {
    setSelectedTopicId(value)
    // Clear transient search results when changing topic
    dispatch({ type: 'industry/search/fulfilled', payload: [] })
    // Fetch existing news for this topic when selected
    dispatch(fetchIndustryNews(value))
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 }}>
        <Title level={3} style={{ margin: 0 }}>行业动态追踪</Title>
      </div>

      <Card style={{ marginBottom: 24 }}>
        <Space>
          <Text strong>选择研究选题：</Text>
          <Select
            style={{ width: 400 }}
            placeholder="请选择一个研究选题以获取相关动态"
            onChange={handleTopicChange}
            value={selectedTopicId}
          >
            {topics.map((topic) => (
              <Select.Option key={topic.id} value={topic.id}>
                {topic.title}
              </Select.Option>
            ))}
          </Select>
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
                <MonitorOutlined />
                实时动态
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
                    手动添加动态
                  </Button>
                  <Button
                    type="primary"
                    icon={<ReloadOutlined />}
                    onClick={handleSearch}
                    loading={loading}
                    disabled={!selectedTopicId}
                  >
                    AI 实时探测动态
                  </Button>
                </div>
                {searchResults.length === 0 && !loading ? (
                  <Empty description={selectedTopicId ? "暂无搜索结果，点击搜索获取" : "请先选择一个选题"} />
                ) : (
                  <List
                    grid={{ gutter: 16, column: 1 }}
                    dataSource={searchResults}
                    loading={loading}
                    renderItem={(item) => (
                      <List.Item>
                        <Card
                          hoverable
                          title={
                            <Space>
                              <Text strong>{item.title}</Text>
                              <Tag color="blue">相关度: {(item.relevance_score * 100).toFixed(0)}%</Tag>
                            </Space>
                          }
                          extra={
                            <Space>
                              <Button
                                type="primary"
                                size="small"
                                icon={<PlusOutlined />}
                                onClick={() => handleSaveNews(item)}
                              >
                                采用动态
                              </Button>
                              {item.url && (
                                <a href={item.url} target="_blank" rel="noopener noreferrer">
                                  <Button type="link" icon={<LinkOutlined />} size="small">
                                    原文
                                  </Button>
                                </a>
                              )}
                            </Space>
                          }
                        >
                          <Paragraph ellipsis={{ rows: 2 }}>{item.content}</Paragraph>
                          <Space wrap>
                            {item.keywords?.map((keyword: string) => (
                              <Tag key={keyword} color="geekblue">
                                {keyword}
                              </Tag>
                            ))}
                          </Space>
                          <div style={{ marginTop: 8 }}>
                            <Text type="secondary" size="small">
                              <ClockCircleOutlined /> 来源: {item.source} | 发布时间:{' '}
                              {dateToLocaleString(item.published_at)}
                            </Text>
                          </div>
                        </Card>
                      </List.Item>
                    )}
                  />
                )}
              </>
            ),
          },
          {
            key: 'manage',
            label: (
              <span>
                <SettingOutlined />
                管理动态库 ({news.length})
              </span>
            ),
            children: <IndustryManagement topicId={selectedTopicId} />,
          },
        ]}
      />
    </div>
  )
}

export default IndustryMonitor
