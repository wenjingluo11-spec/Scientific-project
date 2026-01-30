import React, { useState } from 'react'
import { Tabs } from 'antd'
import AITopicDiscovery from './AITopicDiscovery'
import TopicManagement from './TopicManagement'

const TopicSearch: React.FC = () => {
  const [activeKey, setActiveKey] = useState('discovery')

  const items = [
    {
      key: 'discovery',
      label: '选题搜索',
      children: <AITopicDiscovery onSwitchToManagement={() => setActiveKey('management')} />
    },
    {
      key: 'management',
      label: '选题管理',
      children: <TopicManagement />
    }
  ]

  return (
    <div>
      <Tabs
        activeKey={activeKey}
        onChange={setActiveKey}
        items={items}
        size="large"
      />
    </div>
  )
}

export default TopicSearch
