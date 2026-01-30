import React, { useState, useEffect } from 'react'
import { useDispatch, useSelector } from 'react-redux'
import {
  Form, Input, Select, Button, Card, Tag, Progress,
  Space, Checkbox, message, Spin, Empty, Row, Col, Modal, List, Badge, Switch
} from 'antd'
import { PlusOutlined, BulbOutlined, HistoryOutlined, ReloadOutlined } from '@ant-design/icons'
import type { RootState, AppDispatch } from '@/store/store'
import {
  discoverTopics,
  batchCreateTopics,
  fetchRecommendationHistory,
  loadHistoricalRecommendation,
  TopicSuggestion,
  RecommendationHistory
} from '@/store/slices/topicsSlice'

const { TextArea } = Input
const { Option } = Select

interface AITopicDiscoveryProps {
  onSwitchToManagement: () => void
}

const AITopicDiscovery: React.FC<AITopicDiscoveryProps> = ({ onSwitchToManagement }) => {
  const dispatch = useDispatch<AppDispatch>()
  const { suggestions, discovering, recommendationHistory, historyLoading } = useSelector((state: RootState) => state.topics)
  const [form] = Form.useForm()
  const [selectedSuggestions, setSelectedSuggestions] = useState<number[]>([])
  const [historyModalVisible, setHistoryModalVisible] = useState(false)
  const [currentSearchTopic, setCurrentSearchTopic] = useState<string | undefined>()

  const handleDiscover = async (values: any) => {
    try {
      await dispatch(discoverTopics({
        research_field: values.field,
        topic: values.topic,
        keywords: values.keywords.split(',').map((k: string) => k.trim()),
        description: values.description,
        num_suggestions: values.num_suggestions || 5,
        use_deep_research: values.use_deep_research
      })).unwrap()

      setCurrentSearchTopic(values.topic) // 记录当前搜索的主题
      message.success('AI 推荐完成！')
      setSelectedSuggestions([]) // 清空选择
    } catch (error) {
      message.error('推荐失败，请重试')
    }
  }

  const handleBatchAdd = async () => {
    if (selectedSuggestions.length === 0) {
      message.warning('请至少选择一个推荐选题')
      return
    }

    const topicsToAdd = selectedSuggestions.map(index => ({
      title: suggestions[index].title,
      description: suggestions[index].description,
      field: suggestions[index].field,
      specific_topic: currentSearchTopic, // 使用记录的主题
      keywords: suggestions[index].keywords
    }))

    try {
      await dispatch(batchCreateTopics(topicsToAdd)).unwrap()
      message.success(`已添加 ${selectedSuggestions.length} 个选题到管理列表`)
      setSelectedSuggestions([])

      // 跳转到选题管理 Tab
      setTimeout(() => {
        onSwitchToManagement()
      }, 500)
    } catch (error) {
      message.error('添加失败，请重试')
    }
  }

  const handleShowHistory = async () => {
    setHistoryModalVisible(true)
    await dispatch(fetchRecommendationHistory({ limit: 10 }))
  }

  const handleLoadHistory = async (record: RecommendationHistory) => {
    try {
      await dispatch(loadHistoricalRecommendation(record.id)).unwrap()
      setHistoryModalVisible(false)
      message.success('已加载历史推荐')
      setSelectedSuggestions([])

      // 同步当前搜索的主题状态，以便后续添加到管理列表
      setCurrentSearchTopic(record.specific_topic)

      // 更新表单显示
      form.setFieldsValue({
        field: record.research_field,
        topic: record.specific_topic,
        keywords: record.keywords.join(', '),
        description: record.description
      })
    } catch (error) {
      message.error('加载失败，请重试')
    }
  }

  return (
    <div>
      {/* 输入表单 */}
      <Card title="AI 智能推荐" style={{ marginBottom: 24 }}>
        <Form form={form} layout="vertical" onFinish={handleDiscover}>
          <Row gutter={16}>
            <Col span={8}>
              <Form.Item
                name="field"
                label="研究领域"
                rules={[{ required: true, message: '请选择研究领域' }]}
              >
                <Select placeholder="选择研究领域" size="large">
                  <Option value="计算机科学">计算机科学</Option>
                  <Option value="人工智能">人工智能</Option>
                  <Option value="生物医学">生物医学</Option>
                  <Option value="物理学">物理学</Option>
                  <Option value="化学">化学</Option>
                  <Option value="材料科学">材料科学</Option>
                  <Option value="经济学">经济学</Option>
                  <Option value="其他">其他</Option>
                </Select>
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="topic"
                label="具体细分方向/主题"
                rules={[{ required: true, message: '请输入您的具体研究方向' }]}
              >
                <Input
                  placeholder="例如：基于Transformer的目标检测"
                  size="large"
                />
              </Form.Item>
            </Col>

            <Col span={8}>
              <Form.Item
                name="keywords"
                label="关键词"
                rules={[{ required: true, message: '请输入关键词' }]}
              >
                <Input
                  placeholder="多个词用逗号分隔"
                  size="large"
                />
              </Form.Item>
            </Col>
          </Row>

          <Form.Item name="description" label="研究方向描述（可选）">
            <TextArea
              rows={3}
              placeholder="简要描述您的研究方向和兴趣，AI 将据此提供更精准的推荐..."
            />
          </Form.Item>

          <Form.Item name="use_deep_research" valuePropName="checked">
            <div style={{ display: 'flex', alignItems: 'center', gap: 8, background: '#f0f5ff', padding: '12px', borderRadius: 8, border: '1px solid #adc6ff' }}>
              <Switch />
              <div style={{ display: 'flex', flexDirection: 'column' }}>
                <span style={{ fontWeight: 'bold', color: '#1d39c4' }}>启用 Gemini Deep Research 深度调研</span>
                <span style={{ fontSize: 12, color: '#666' }}>
                  智能体将自主进行长达数分钟的广泛文献搜索与深度阅读，生成更具前瞻性的选题。
                  (耗时较长，请耐心等待)
                </span>
              </div>
            </div>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button
                type="primary"
                htmlType="submit"
                icon={<BulbOutlined />}
                size="large"
                loading={discovering}
              >
                AI 智能推荐
              </Button>
              <Button
                icon={<HistoryOutlined />}
                size="large"
                onClick={handleShowHistory}
              >
                查看历史
              </Button>
            </Space>
            <span style={{ marginLeft: 16, color: '#888' }}>
              {discovering ? '正在分析，预计需要 10-15 秒...' : ''}
            </span>
          </Form.Item>
        </Form>
      </Card>

      {/* 推荐结果 */}
      <Spin spinning={discovering} tip="AI 正在深度分析您的研究方向...">
        {suggestions.length > 0 ? (
          <>
            <div style={{ marginBottom: 16 }}>
              <Space>
                <Button
                  type="primary"
                  icon={<PlusOutlined />}
                  onClick={handleBatchAdd}
                  disabled={selectedSuggestions.length === 0}
                >
                  添加 {selectedSuggestions.length > 0 ? selectedSuggestions.length : ''} 个选题到管理
                </Button>
                <span style={{ color: '#888' }}>
                  共推荐 {suggestions.length} 个选题，请选择感兴趣的添加
                </span>
              </Space>
            </div>

            <Space direction="vertical" size="middle" style={{ width: '100%' }}>
              {suggestions.map((suggestion, index) => (
                <Card
                  key={index}
                  hoverable
                  extra={
                    <Checkbox
                      checked={selectedSuggestions.includes(index)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedSuggestions([...selectedSuggestions, index])
                        } else {
                          setSelectedSuggestions(selectedSuggestions.filter(i => i !== index))
                        }
                      }}
                    >
                      选择
                    </Checkbox>
                  }
                >
                  <h3 style={{ marginBottom: 12, fontSize: 18 }}>
                    {index + 1}. {suggestion.title}
                  </h3>

                  <p style={{ color: '#666', marginBottom: 12 }}>
                    {suggestion.description}
                  </p>

                  <div style={{ marginBottom: 12 }}>
                    <strong>研究领域：</strong>
                    <Tag color="purple" style={{ marginLeft: 8 }}>
                      {suggestion.field}
                    </Tag>
                  </div>

                  <div style={{ marginBottom: 12 }}>
                    <strong>关键词：</strong>
                    {suggestion.keywords.map(keyword => (
                      <Tag color="blue" key={keyword} style={{ marginLeft: 4 }}>
                        {keyword}
                      </Tag>
                    ))}
                  </div>

                  <Row gutter={16} style={{ marginBottom: 12 }}>
                    <Col span={12}>
                      <div>新颖性评分：</div>
                      <Progress
                        percent={suggestion.novelty_score}
                        strokeColor="#52c41a"
                        format={(percent) => `${percent}分`}
                      />
                    </Col>
                    <Col span={12}>
                      <div>可行性评分：</div>
                      <Progress
                        percent={suggestion.feasibility_score}
                        strokeColor="#1890ff"
                        format={(percent) => `${percent}分`}
                      />
                    </Col>
                  </Row>

                  <div style={{
                    padding: 12,
                    background: '#f5f5f5',
                    borderRadius: 4
                  }}>
                    <strong>推荐理由：</strong>
                    <div style={{ marginTop: 8, color: '#666' }}>
                      {suggestion.reasoning}
                    </div>
                  </div>

                  {/* Display Model Signature */}
                  {suggestion.model_signature && (
                    <div style={{ marginTop: 12, textAlign: 'right' }}>
                      <Tag color="default" style={{ color: '#999', fontSize: 12, border: 'none', background: 'transparent' }}>
                        {suggestion.model_signature}
                      </Tag>
                    </div>
                  )}
                </Card>
              ))}
            </Space>
          </>
        ) : !discovering && (
          <Empty
            description="输入研究方向后，AI 将为您推荐创新且可行的选题"
            image={Empty.PRESENTED_IMAGE_SIMPLE}
          />
        )}
      </Spin>

      {/* 历史记录 Modal */}
      <Modal
        title="推荐历史记录"
        open={historyModalVisible}
        onCancel={() => setHistoryModalVisible(false)}
        footer={null}
        width={800}
        styles={{
          body: {
            height: 'calc(65vh - 55px)',
            overflow: 'auto',
          }
        }}
      >
        <Spin spinning={historyLoading}>
          {recommendationHistory.length > 0 ? (
            <List
              dataSource={recommendationHistory}
              renderItem={(record) => (
                <List.Item
                  key={record.id}
                  actions={[
                    <Button
                      key="load"
                      type="link"
                      icon={<ReloadOutlined />}
                      onClick={() => handleLoadHistory(record)}
                    >
                      加载此推荐
                    </Button>
                  ]}
                >
                  <List.Item.Meta
                    title={
                      <Space>
                        <Badge status="success" />
                        <span>{record.research_field}</span>
                        {record.specific_topic && (
                          <Tag color="cyan">{record.specific_topic}</Tag>
                        )}
                        <Tag color="blue">{record.suggestions.length} 个推荐</Tag>
                      </Space>
                    }
                    description={
                      <div>
                        <div style={{ marginBottom: 8 }}>
                          <strong>关键词：</strong>
                          {record.keywords.map(kw => (
                            <Tag key={kw} color="geekblue" style={{ marginLeft: 4 }}>
                              {kw}
                            </Tag>
                          ))}
                        </div>
                        {record.description && (
                          <div style={{ color: '#666' }}>
                            <strong>描述：</strong>{record.description}
                          </div>
                        )}
                        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
                          推荐时间：{new Date(record.created_at).toLocaleString('zh-CN')}
                        </div>
                      </div>
                    }
                  />
                </List.Item>
              )}
            />
          ) : (
            <Empty description="暂无历史记录" />
          )}
        </Spin>
      </Modal>
    </div>
  )
}

export default AITopicDiscovery
