import React, { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import { GraphNodeResponse, GraphEdgeResponse } from '../../lib/api';

export type SimNode = GraphNodeResponse & d3.SimulationNodeDatum;
export type SimLink = Omit<GraphEdgeResponse, 'source' | 'target'> & d3.SimulationLinkDatum<SimNode> & {
  source: SimNode;
  target: SimNode;
};

export interface GraphCanvasProps {
  nodes: GraphNodeResponse[];
  edges: GraphEdgeResponse[];
  selectedNodeId: string | null;
  onNodeSelect: (nodeId: string) => void;
}

export function GraphCanvas({ nodes, edges, selectedNodeId, onNodeSelect }: GraphCanvasProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  // We need to maintain simulation state
  const [simNodes, setSimNodes] = useState<SimNode[]>([]);
  const [simEdges, setSimEdges] = useState<SimLink[]>([]);

  // To allow deterministic graph, we initialize x/y uniformly
  useEffect(() => {
    const width = containerRef.current?.clientWidth || 800;
    const height = containerRef.current?.clientHeight || 580;

    const mappedNodes: SimNode[] = nodes.map((n, i) => ({
      ...n,
      x: width / 2 + Math.cos(i) * 50,
      y: height / 2 + Math.sin(i) * 50
    }));

    const mappedEdges: d3.SimulationLinkDatum<SimNode>[] = edges.map(e => ({
      ...e,
      source: e.source,
      target: e.target
    }));

    const simulation = d3.forceSimulation<SimNode>(mappedNodes)
      .force('link', d3.forceLink<SimNode, d3.SimulationLinkDatum<SimNode>>(mappedEdges).id((d) => d.id).distance(80))
      .force('charge', d3.forceManyBody().strength(-200))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collide', d3.forceCollide().radius(30));

    simulation.tick(300);
    simulation.stop();

    setSimNodes(mappedNodes);
    setSimEdges(mappedEdges as SimLink[]);
  }, [nodes, edges]);

  // Zoom setup
  const zoomRef = useRef<d3.ZoomBehavior<SVGSVGElement, unknown> | null>(null);

  useEffect(() => {
    if (!svgRef.current) return;
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 8])
      .on('zoom', (event) => {
        svg.select('g.zoom-layer').attr('transform', event.transform);
      });
    zoomRef.current = zoom;
    svg.call(zoom);
    return () => {
      svg.on('.zoom', null);
    };
  }, []);

  const handleZoomIn = () => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    svg.transition().duration(300).call(zoomRef.current.scaleBy, 1.3);
  };

  const handleZoomOut = () => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    svg.transition().duration(300).call(zoomRef.current.scaleBy, 1 / 1.3);
  };

  const handleReset = () => {
    if (!svgRef.current || !zoomRef.current) return;
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    svg.transition().duration(500).call(zoomRef.current.transform, d3.zoomIdentity);
  };

  const handleFit = () => {
    if (!svgRef.current || !zoomRef.current || simNodes.length === 0) return;
    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    
    const xExtent = d3.extent(simNodes, d => d.x as number);
    const yExtent = d3.extent(simNodes, d => d.y as number);
    if (xExtent[0] === undefined || xExtent[1] === undefined || yExtent[0] === undefined || yExtent[1] === undefined) return;

    const width = containerRef.current?.clientWidth || 800;
    const height = containerRef.current?.clientHeight || 580;
    
    const dx = xExtent[1] - xExtent[0];
    const dy = yExtent[1] - yExtent[0];
    const x = (xExtent[0] + xExtent[1]) / 2;
    const y = (yExtent[0] + yExtent[1]) / 2;

    const scale = Math.max(0.1, Math.min(2, 0.85 / Math.max(dx / width || 1, dy / height || 1)));
    const translate = [width / 2 - scale * x, height / 2 - scale * y];

    const transform = d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale);
    svg.transition().duration(750).call(zoomRef.current.transform, transform);
  };

  const handleFocus = () => {
    if (!svgRef.current || !zoomRef.current || !selectedNodeId) return;
    const node = simNodes.find(n => n.id === selectedNodeId);
    if (!node) return;

    const svg = d3.select<SVGSVGElement, unknown>(svgRef.current);
    const width = containerRef.current?.clientWidth || 800;
    const height = containerRef.current?.clientHeight || 580;

    const scale = 2; // Zoom level for focus
    const translate = [width / 2 - scale * (node.x as number), height / 2 - scale * (node.y as number)];

    const transform = d3.zoomIdentity.translate(translate[0], translate[1]).scale(scale);
    svg.transition().duration(750).call(zoomRef.current.transform, transform);
  };

  const getNodeColor = (type: string) => {
    if (type === 'Transaction') return '#F7931A'; // gold
    if (type === 'Address') return '#0D0D0D';
    if (type === 'IP') return '#5A5852';
    return '#555';
  };

  const getNodeShape = (type: string) => {
    if (type === 'Transaction') return 'square';
    if (type === 'Address') return 'circle';
    return 'diamond'; // IP
  };

  return (
    <div className="w-full h-full relative flex flex-col" ref={containerRef}>
      {/* Canvas Controls */}
      <div className="absolute top-4 right-4 z-10 flex items-center gap-1 font-mono text-[0.6875rem] font-bold">
        <button onClick={handleFit} className="px-2 py-1 bg-surface-accent border border-structural-border hover:bg-neutral text-secondary">FIT</button>
        <button onClick={handleFocus} disabled={!selectedNodeId} className={`px-2 py-1 border border-structural-border ${selectedNodeId ? 'bg-surface-accent hover:bg-neutral text-secondary' : 'bg-neutral text-muted-ink cursor-not-allowed'}`}>FOCUS</button>
        <button onClick={handleZoomIn} className="px-2 py-1 bg-surface-accent border border-structural-border hover:bg-neutral text-secondary">ZOOM IN [+]</button>
        <button onClick={handleZoomOut} className="px-2 py-1 bg-surface-accent border border-structural-border hover:bg-neutral text-secondary">[-]</button>
        <button onClick={handleReset} className="px-2 py-1 bg-surface-accent border border-structural-border hover:bg-neutral text-secondary">RESET VIEW</button>
      </div>

      <svg ref={svgRef} className="w-full h-full bg-neutral">
        <defs>
          <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="20" refY="3.5" orient="auto">
            <polygon points="0 0, 10 3.5, 0 7" fill="#5A5852" />
          </marker>
        </defs>
        <g className="zoom-layer">
          <g className="edges">
            {simEdges.map((e, idx) => (
              <line 
                key={idx}
                x1={e.source.x} 
                y1={e.source.y} 
                x2={e.target.x} 
                y2={e.target.y} 
                stroke="#5A5852"
                strokeWidth={selectedNodeId === e.source.id || selectedNodeId === e.target.id ? 2 : 1}
                opacity={selectedNodeId && selectedNodeId !== e.source.id && selectedNodeId !== e.target.id ? 0.2 : 1}
                markerEnd="url(#arrowhead)"
              />
            ))}
          </g>
          <g className="nodes">
            {simNodes.map(n => {
              const isSelected = selectedNodeId === n.id;
              const isFaded = selectedNodeId && !isSelected && !simEdges.some(e => 
                (e.source.id === n.id && e.target.id === selectedNodeId) || 
                (e.target.id === n.id && e.source.id === selectedNodeId)
              );
              
              const color = getNodeColor(n.node_type);
              const shape = getNodeShape(n.node_type);
              
              return (
                <g 
                  key={n.id} 
                  transform={`translate(${n.x},${n.y})`}
                  onClick={() => onNodeSelect(n.id)}
                  onKeyDown={(e) => {
                    if (e.key === 'Enter' || e.key === ' ') {
                      e.preventDefault();
                      onNodeSelect(n.id);
                    }
                  }}
                  tabIndex={0}
                  role="button"
                  aria-label={`${n.node_type} node: ${n.id}`}
                  style={{ cursor: 'pointer', opacity: isFaded ? 0.2 : 1 }}
                  className="focus:outline focus:outline-2 focus:outline-primary focus:outline-offset-2 outline-none"
                >
                  {shape === 'circle' && (
                    <circle r={10} fill={isSelected ? '#F9F8F3' : '#F4F1EA'} stroke={color} strokeWidth={isSelected ? 3 : 2} />
                  )}
                  {shape === 'square' && (
                    <rect x={-10} y={-10} width={20} height={20} fill={isSelected ? '#F9F8F3' : '#F4F1EA'} stroke={color} strokeWidth={isSelected ? 3 : 2} />
                  )}
                  {shape === 'diamond' && (
                    <polygon points="0,-12 12,0 0,12 -12,0" fill={isSelected ? '#F9F8F3' : '#F4F1EA'} stroke={color} strokeWidth={isSelected ? 3 : 2} />
                  )}
                  <text 
                    y={20} 
                    textAnchor="middle" 
                    fill="#0D0D0D" 
                    className="font-mono text-[0.625rem]"
                  >
                    {n.id.length > 8 ? n.id.substring(0,8) + '...' : n.id}
                  </text>
                </g>
              );
            })}
          </g>
        </g>
      </svg>
    </div>
  );
}
