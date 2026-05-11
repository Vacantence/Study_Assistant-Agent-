import { useEffect, useRef, useState } from 'react';
import { useGraphStore } from '../stores/graphStore';

export default function GraphPage() {
  const { nodes, edges, loading, fetchGraph, clearGraph } = useGraphStore();
  const containerRef = useRef<HTMLDivElement>(null);
  const [showList, setShowList] = useState(false);

  useEffect(() => {
    fetchGraph();
  }, []);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;
    let vis: any;
    import('vis-network').then((mod) => {
      const Network = mod.Network;
      const dataset: any = {
        nodes: nodes.map((n, i) => ({
          id: i,
          label: n.name,
          title: n.description,
        })),
        edges: edges.map((e) => ({
          from: nodes.findIndex((n) => n.name === e.source),
          to: nodes.findIndex((n) => n.name === e.target),
          label: e.relation,
          arrows: 'to',
          font: { size: 12 },
        })),
      };
      vis = new Network(containerRef.current!, dataset, {
        physics: { solver: 'barnesHut' },
        edges: { smooth: true },
        nodes: {
          shape: 'ellipse',
          font: { size: 14, face: 'PingFang SC, Microsoft YaHei, sans-serif' },
        },
      });
    });
    return () => { vis?.destroy(); };
  }, [nodes, edges]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full">
        <p style={{ color: 'var(--color-text-muted)' }}>加载中...</p>
      </div>
    );
  }

  if (nodes.length === 0) {
    return (
      <div className="flex items-center justify-center h-full">
        <div className="text-center">
          <h2 className="text-lg font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>知识图谱为空</h2>
          <p className="text-sm" style={{ color: 'var(--color-text-muted)' }}>继续学习来构建你的知识图谱</p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-2 border-b shrink-0" style={{ borderColor: 'var(--color-border)' }}>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {nodes.length} 个知识点 · {edges.length} 条关系
          </span>
          <button onClick={() => setShowList(!showList)} className="text-xs cursor-pointer" style={{ color: 'var(--color-accent)' }}>
            {showList ? '收起列表' : '全部知识点'}
          </button>
        </div>
        <button
          onClick={() => { if (confirm('确定清空知识图谱？')) clearGraph(); }}
          className="text-xs cursor-pointer"
          style={{ color: 'var(--color-danger)' }}
        >
          清空图谱
        </button>
      </div>

      <div className="flex-1 flex min-h-0">
        <div ref={containerRef} className="flex-1" />
        {showList && (
          <div
            className="w-64 overflow-y-auto border-l p-3"
            style={{ borderColor: 'var(--color-border)', backgroundColor: 'var(--color-surface-alt)' }}
          >
            <h3 className="text-xs font-medium mb-2" style={{ color: 'var(--color-text-secondary)' }}>全部知识点</h3>
            {nodes.map((n) => (
              <div key={n.name} className="mb-2">
                <div className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>{n.name}</div>
                <div className="text-xs" style={{ color: 'var(--color-text-muted)' }}>{n.description}</div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
