import { useWorkspaceStore } from '../../stores/workspaceStore';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

export default function Header() {
  const { currentWorkspace, setWorkspace } = useWorkspaceStore();

  return (
    <header className="sticky top-0 z-20 border-b border-white/70 bg-white/85 backdrop-blur-xl">
      <div className="mx-auto flex w-full max-w-[1600px] items-center justify-between gap-6 px-5 py-4 lg:px-8">
        <div className="min-w-0">
          <div className="mb-2 flex items-center gap-3">
            <Badge>Market Intelligence</Badge>
            <span className="text-xs font-medium uppercase tracking-[0.24em] text-slate-400">
              Crawl4AI
            </span>
          </div>
          <div>
            <h1 className="text-balance text-2xl font-semibold tracking-tight text-slate-950">
              资讯洞察工作台
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              聚合竞争对手、行业新闻与展会动态，聚焦当前工作空间的关键信号。
            </p>
          </div>
        </div>

        <div className="flex min-w-[220px] flex-col gap-2 text-sm font-medium text-slate-600">
          <span>工作空间</span>
          <Select value={currentWorkspace} onValueChange={setWorkspace}>
            <SelectTrigger aria-label="选择工作空间">
              <SelectValue placeholder="选择工作空间" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="default">默认工作空间</SelectItem>
              <SelectItem value="workspace1">工作空间 1</SelectItem>
              <SelectItem value="workspace2">工作空间 2</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>
    </header>
  );
}
