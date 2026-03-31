import { Layout, Select } from '@arco-design/web-react';
import { useWorkspaceStore } from '../../stores/workspaceStore';
import './Header.css';

const { Header: ArcoHeader } = Layout;

export default function Header() {
  const { currentWorkspace, setWorkspace } = useWorkspaceStore();

  return (
    <ArcoHeader className="app-header">
      <div className="header-content">
        <h1 className="app-title">Crawl4AI 数据管理</h1>
        <div className="header-actions">
          <Select
            placeholder="选择工作空间"
            value={currentWorkspace}
            onChange={setWorkspace}
            style={{ width: 200 }}
          >
            <Select.Option value="default">默认工作空间</Select.Option>
            <Select.Option value="workspace1">工作空间 1</Select.Option>
            <Select.Option value="workspace2">工作空间 2</Select.Option>
          </Select>
        </div>
      </div>
    </ArcoHeader>
  );
}
