import { Layout, Menu } from '@arco-design/web-react';
import { IconUser, IconBook, IconCalendar } from '@arco-design/web-react/icon';
import { useNavigate, useLocation } from 'react-router-dom';
import './Sidebar.css';

const { Sider } = Layout;
const MenuItem = Menu.Item;

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: '/competitors',
      icon: <IconUser />,
      label: '竞争对手',
    },
    {
      key: '/industry-news',
      icon: <IconBook />,
      label: '行业新闻',
    },
    {
      key: '/trade-shows',
      icon: <IconCalendar />,
      label: '展会信息',
    },
  ];

  return (
    <Sider className="app-sidebar" width={200}>
      <Menu
        selectedKeys={[location.pathname]}
        onClickMenuItem={(key) => navigate(key)}
      >
        {menuItems.map((item) => (
          <MenuItem key={item.key}>
            {item.icon}
            {item.label}
          </MenuItem>
        ))}
      </Menu>
    </Sider>
  );
}
