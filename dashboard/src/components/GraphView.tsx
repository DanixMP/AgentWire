/**
 * D3 force-directed graph view
 */

import { useEffect, useRef, useState } from 'react';
import * as d3 from 'd3';
import type { GraphData, D3Node, D3Edge, MessageType } from '../types';
import { GRAPH_COLORS } from '../types';

interface GraphViewProps {
  graphData: GraphData;
  onFilterAgent: (agent: string) => void;
  onFilterPair: (source: string, target: string) => void;
  isReplaying?: boolean;
  replayIndex?: number;
  messages?: any[]; // For replay mode
}

export function GraphView({ graphData, onFilterAgent, onFilterPair, isReplaying = false, replayIndex = 0, messages = [] }: GraphViewProps) {
  const svgRef = useRef<SVGSVGElement>(null);
  const simulationRef = useRef<d3.Simulation<D3Node, D3Edge> | null>(null);
  const [hoveredNode, setHoveredNode] = useState<string | null>(null);
  const [hoveredEdge, setHoveredEdge] = useState<string | null>(null);

  // In replay mode, filter graph data to only show nodes/edges up to replayIndex
  const displayGraphData = isReplaying && messages.length > 0
    ? (() => {
        const replayMessages = messages.slice(0, replayIndex + 1);
        const seenAgents = new Set<string>();
        const seenEdges = new Set<string>();

        replayMessages.forEach(msg => {
          seenAgents.add(msg.sender);
          if (msg.receiver !== 'system' && msg.receiver !== 'broadcast' && msg.receiver !== 'unknown') {
            seenAgents.add(msg.receiver);
            seenEdges.add(`${msg.sender}→${msg.receiver}`);
          }
        });

        return {
          nodes: graphData.nodes.filter(n => seenAgents.has(n.id)),
          edges: graphData.edges.filter(e => seenEdges.has(`${e.source}→${e.target}`)),
        };
      })()
    : graphData;

  useEffect(() => {
    if (!svgRef.current || !displayGraphData.nodes.length) return;

    const svg = d3.select(svgRef.current);
    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    // Clear previous content
    svg.selectAll('*').remove();

    // Create container group for zoom
    const g = svg.append('g');

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    svg.call(zoom);

    // Prepare data
    const nodes: D3Node[] = displayGraphData.nodes.map(n => ({ ...n }));
    const edges: D3Edge[] = displayGraphData.edges.map(e => ({ ...e }));

    // Create simulation
    const simulation = d3.forceSimulation<D3Node>(nodes)
      .force('link', d3.forceLink<D3Node, D3Edge>(edges)
        .id(d => d.id)
        .distance(150))
      .force('charge', d3.forceManyBody().strength(-500))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(60));

    simulationRef.current = simulation;

    // Create arrow markers for edges
    const defs = svg.append('defs');
    
    Object.entries(GRAPH_COLORS).forEach(([type, color]) => {
      defs.append('marker')
        .attr('id', `arrow-${type}`)
        .attr('viewBox', '0 -5 10 10')
        .attr('refX', 35)
        .attr('refY', 0)
        .attr('markerWidth', 6)
        .attr('markerHeight', 6)
        .attr('orient', 'auto')
        .append('path')
        .attr('d', 'M0,-5L10,0L0,5')
        .attr('fill', color);
    });

    // Draw edges
    const link = g.append('g')
      .selectAll('line')
      .data(edges)
      .join('line')
      .attr('stroke', d => GRAPH_COLORS[d.dominant_type as MessageType])
      .attr('stroke-width', d => Math.max(1, Math.min(6, d.count)))
      .attr('stroke-opacity', 0.6)
      .attr('marker-end', d => `url(#arrow-${d.dominant_type})`)
      .style('cursor', 'pointer')
      .on('mouseenter', function(_event, d: D3Edge) {
        const edgeKey = `${d.source}-${d.target}`;
        setHoveredEdge(edgeKey);
        d3.select(this).attr('stroke-opacity', 1).attr('stroke-width', Math.max(2, Math.min(8, d.count + 2)));
      })
      .on('mouseleave', function(_event, d: D3Edge) {
        setHoveredEdge(null);
        d3.select(this).attr('stroke-opacity', 0.6).attr('stroke-width', Math.max(1, Math.min(6, d.count)));
      })
      .on('click', (event, d) => {
        event.stopPropagation();
        const source = typeof d.source === 'string' ? d.source : d.source.id;
        const target = typeof d.target === 'string' ? d.target : d.target.id;
        onFilterPair(source, target);
      });

    // Add edge tooltips
    link.append('title')
      .text(d => {
        const source = typeof d.source === 'string' ? d.source : d.source.id;
        const target = typeof d.target === 'string' ? d.target : d.target.id;
        return `${source} → ${target}\n${d.count} messages\nType: ${d.dominant_type}\nTokens: ${d.total_tokens}\nAvg latency: ${d.avg_latency_ms}ms`;
      });

    // Draw nodes
    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', d => Math.max(20, Math.min(50, 10 + d.message_count * 3)))
      .attr('fill', d => GRAPH_COLORS[d.dominant_type as MessageType])
      .attr('stroke', '#1e293b')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .on('mouseenter', function(_event, d: D3Node) {
        setHoveredNode(d.id);
        d3.select(this).attr('stroke-width', 4).attr('stroke', '#60a5fa');
      })
      .on('mouseleave', function(_event, _d: D3Node) {
        setHoveredNode(null);
        d3.select(this).attr('stroke-width', 2).attr('stroke', '#1e293b');
      })
      .on('click', (event, d) => {
        event.stopPropagation();
        onFilterAgent(d.id);
      })
      .call(d3.drag<any, D3Node>()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
        })
        .on('drag', (event, d) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
        }) as any);

    // Add node tooltips
    node.append('title')
      .text(d => `${d.id}\n${d.message_count} messages\n${d.total_tokens} tokens\nType: ${d.dominant_type}`);

    // Draw labels
    const label = g.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text(d => d.id)
      .attr('font-size', 12)
      .attr('font-weight', 'bold')
      .attr('fill', '#e2e8f0')
      .attr('text-anchor', 'middle')
      .attr('dy', d => Math.max(20, Math.min(50, 10 + d.message_count * 3)) + 15)
      .style('pointer-events', 'none')
      .style('user-select', 'none');

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as D3Node).x!)
        .attr('y1', d => (d.source as D3Node).y!)
        .attr('x2', d => (d.target as D3Node).x!)
        .attr('y2', d => (d.target as D3Node).y!);

      node
        .attr('cx', d => d.x!)
        .attr('cy', d => d.y!);

      label
        .attr('x', d => d.x!)
        .attr('y', d => d.y!);
    });

    // Cleanup
    return () => {
      simulation.stop();
    };
  }, [displayGraphData, onFilterAgent, onFilterPair]);

  if (!displayGraphData.nodes.length) {
    return (
      <div className="flex-1 flex items-center justify-center text-slate-500">
        <div className="text-center">
          <div className="text-4xl mb-2">🕸️</div>
          <p>No graph data yet</p>
          <p className="text-sm mt-1">
            Agent interactions will appear here
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex-1 relative">
      <svg
        ref={svgRef}
        className="w-full h-full bg-slate-900"
      />
      
      {/* Legend */}
      <div className="absolute top-4 right-4 bg-slate-800 rounded-lg p-4 text-sm">
        <div className="font-semibold text-slate-200 mb-2">Legend</div>
        <div className="space-y-1 text-slate-300">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: GRAPH_COLORS.TASK }}></div>
            <span>TASK</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: GRAPH_COLORS.RESULT }}></div>
            <span>RESULT</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: GRAPH_COLORS.ERROR }}></div>
            <span>ERROR</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded-full" style={{ backgroundColor: GRAPH_COLORS.TOOL_CALL }}></div>
            <span>TOOL_CALL</span>
          </div>
        </div>
        <div className="mt-3 pt-3 border-t border-slate-700 text-xs text-slate-400">
          <div>• Node size = message count</div>
          <div>• Edge width = message count</div>
          <div>• Click node to filter</div>
          <div>• Click edge to filter pair</div>
          <div>• Drag nodes to reposition</div>
          <div>• Scroll to zoom</div>
        </div>
      </div>

      {/* Hover info */}
      {(hoveredNode || hoveredEdge) && (
        <div className="absolute bottom-4 left-4 bg-slate-800 rounded-lg p-3 text-sm text-slate-200">
          {hoveredNode && <div>Hovering: <span className="font-semibold">{hoveredNode}</span></div>}
          {hoveredEdge && <div>Hovering edge: <span className="font-semibold">{hoveredEdge}</span></div>}
        </div>
      )}
    </div>
  );
}
