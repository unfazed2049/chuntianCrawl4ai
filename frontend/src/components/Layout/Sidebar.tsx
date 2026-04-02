import { BookOpen, CalendarRange, Users2 } from "lucide-react";
import { useNavigate, useLocation } from "react-router-dom";
import { cn } from "../../lib/utils";

export default function Sidebar() {
  const navigate = useNavigate();
  const location = useLocation();

  const menuItems = [
    {
      key: "/competitors",
      icon: Users2,
      label: "竞争对手",
      description: "跟踪公司产品、案例、解决方案",
    },
    {
      key: "/industry-news",
      icon: BookOpen,
      label: "行业新闻",
      description: "阅读高价值资讯、趋势与事件",
    },
    {
      key: "/trade-shows",
      icon: CalendarRange,
      label: "展会信息",
      description: "按时间整理会展节点与市场曝光",
    },
  ];

  return (
    <aside className="border-r border-white/60 bg-slate-950 text-slate-100 lg:sticky lg:top-[97px] lg:h-[calc(100vh-97px)]">
      <div className="flex h-full flex-col px-4 py-6">
        <div className="mb-6 rounded-3xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs font-semibold uppercase tracking-[0.24em] text-sky-300/80">
            Navigation
          </p>
        </div>

        <nav aria-label="主导航" className="space-y-2">
          {menuItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.key;

            return (
              <button
                key={item.key}
                type="button"
                onClick={() => navigate(item.key)}
                className={cn(
                  "group flex w-full items-start gap-3 rounded-2xl px-4 py-3 text-left transition-[background-color,border-color,color] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-950",
                  isActive
                    ? "bg-sky-500 text-white shadow-lg shadow-sky-950/20"
                    : "bg-white/0 text-slate-300 hover:bg-white/8 hover:text-white",
                )}
                aria-current={isActive ? "page" : undefined}
              >
                <span
                  className={cn(
                    "mt-0.5 rounded-xl p-2 transition-colors",
                    isActive
                      ? "bg-white/15"
                      : "bg-white/6 group-hover:bg-white/12",
                  )}
                >
                  <Icon className="h-4 w-4" aria-hidden="true" />
                </span>
                <span className="min-w-0">
                  <span className="block text-sm font-semibold">
                    {item.label}
                  </span>
                  <span className="mt-1 block text-xs leading-5 text-inherit/75">
                    {item.description}
                  </span>
                </span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
