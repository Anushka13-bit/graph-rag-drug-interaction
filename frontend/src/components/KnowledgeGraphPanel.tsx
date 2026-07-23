import React, { useEffect, useRef } from 'react';
import { ZoomIn, ZoomOut, Info } from 'lucide-react';
import * as d3 from 'd3';
import { type InteractionGraphData } from '../services/apiClient';

interface KnowledgeGraphPanelProps {
  patientId?: string;
  graphData?: InteractionGraphData;
}

export const KnowledgeGraphPanel: React.FC<KnowledgeGraphPanelProps> = ({
  patientId = '#8492-B',
  graphData,
}) => {
  const containerRef = useRef<HTMLDivElement>(null);
  const svgRef = useRef<SVGSVGElement | null>(null);
  const zoomBehavior = useRef<d3.ZoomBehavior<Element, unknown> | null>(null);

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0 || !containerRef.current) {
      // Clean up SVG if empty
      d3.select(containerRef.current).selectAll('svg').remove();
      return;
    }

    const width = containerRef.current.clientWidth;
    const height = containerRef.current.clientHeight;

    d3.select(containerRef.current).selectAll('svg').remove();

    const svg = d3.select(containerRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height])
      .style('cursor', 'grab');

    svgRef.current = svg.node();

    const g = svg.append('g');

    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform);
      });

    zoomBehavior.current = zoom;
    svg.call(zoom);

    const nodes = graphData.nodes.map(d => ({ ...d }));
    const links = graphData.edges.map(d => ({ ...d }));

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40));

    // Arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrow')
      .attr('viewBox', '0 -5 10 10')
      .attr('refX', 22)
      .attr('refY', 0)
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .attr('orient', 'auto')
      .append('path')
      .attr('d', 'M0,-5L10,0L0,5')
      .attr('fill', '#9CA3AF');

    const link = g.append('g')
      .attr('stroke', '#9CA3AF')
      .attr('stroke-opacity', 0.6)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', (d: any) => d.severity === 'severe' ? 3 : d.severity === 'moderate' ? 2 : 1)
      .attr('stroke', (d: any) => d.severity === 'severe' ? '#DC2626' : d.severity === 'moderate' ? '#D97706' : '#16A34A')
      .attr('marker-end', 'url(#arrow)');

    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 14)
      .attr('fill', '#2185C5')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0.3).restart();
          d.fx = d.x;
          d.fy = d.y;
          svg.style('cursor', 'grabbing');
        })
        .on('drag', (event: any, d: any) => {
          d.fx = event.x;
          d.fy = event.y;
        })
        .on('end', (event: any, d: any) => {
          if (!event.active) simulation.alphaTarget(0);
          d.fx = null;
          d.fy = null;
          svg.style('cursor', 'grab');
        }) as any);

    const labels = g.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .attr('dy', -22)
      .attr('text-anchor', 'middle')
      .style('font-size', '11px')
      .style('font-weight', 'bold')
      .style('fill', '#374151')
      .text((d: any) => d.label)
      .style('pointer-events', 'none');

    // Hover interactions
    node.on('mouseover', (_event: any, d: any) => {
      const connectedNodeIds = new Set();
      connectedNodeIds.add(d.id);
      
      link.each((l: any) => {
        if (l.source.id === d.id) connectedNodeIds.add(l.target.id);
        if (l.target.id === d.id) connectedNodeIds.add(l.source.id);
      });

      node.transition().duration(200)
        .style('opacity', (n: any) => connectedNodeIds.has(n.id) ? 1 : 0.15);
      
      link.transition().duration(200)
        .style('opacity', (l: any) => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1);
      
      labels.transition().duration(200)
        .style('opacity', (n: any) => connectedNodeIds.has(n.id) ? 1 : 0.15);
    }).on('mouseout', () => {
      node.transition().duration(200).style('opacity', 1);
      link.transition().duration(200).style('opacity', 1);
      labels.transition().duration(200).style('opacity', 1);
    });

    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);
      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);
      labels
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    return () => {
      simulation.stop();
    };
  }, [graphData]);

  const handleZoomIn = () => {
    if (svgRef.current && zoomBehavior.current) {
      d3.select(svgRef.current).transition().call(zoomBehavior.current.scaleBy as any, 1.2);
    }
  };

  const handleZoomOut = () => {
    if (svgRef.current && zoomBehavior.current) {
      d3.select(svgRef.current).transition().call(zoomBehavior.current.scaleBy as any, 0.8);
    }
  };

  return (
    <aside className="w-[340px] shrink-0 pl-6 border-l border-gray-200 flex flex-col gap-3 select-none">
      {/* Heading Row with Zoom Buttons */}
      <div className="flex items-start justify-between">
        <div>
          <h2 className="text-base font-bold text-gray-900 leading-tight">
            Interaction Knowledge Graph
          </h2>
          <p className="text-xs text-gray-400 font-normal mt-0.5">
            Active Patient Profile: {patientId}
          </p>
        </div>

        {/* Zoom Controls */}
        <div className="flex items-center gap-1">
          <button
            type="button"
            onClick={handleZoomIn}
            className="p-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-600 transition-colors shadow-2xs"
            aria-label="Zoom in"
          >
            <ZoomIn className="w-4 h-4" />
          </button>
          <button
            type="button"
            onClick={handleZoomOut}
            className="p-1.5 border border-gray-300 rounded-md bg-white hover:bg-gray-50 text-gray-600 transition-colors shadow-2xs"
            aria-label="Zoom out"
          >
            <ZoomOut className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Main Canvas Area */}
      <div className="border border-gray-200 rounded-xl bg-white relative h-[440px] flex flex-col justify-between overflow-hidden shadow-2xs">
        
        {(!graphData || !graphData.nodes || graphData.nodes.length === 0) ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400 gap-2">
            <Info className="w-8 h-8 opacity-50" />
            <span className="text-sm">No graph data available</span>
          </div>
        ) : (
          <div ref={containerRef} className="absolute inset-0 w-full h-full" />
        )}

        {/* Legend Row at Bottom of Canvas */}
        <div className="absolute bottom-3 left-3 flex items-center gap-4 text-xs font-normal text-gray-600 bg-white/90 backdrop-blur-xs px-2 py-1 rounded-md border border-gray-100 shadow-2xs z-10">
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#DC2626]" />
            <span>Major</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#D97706]" />
            <span>Moderate</span>
          </div>
          <div className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full bg-[#16A34A]" />
            <span>Minor</span>
          </div>
        </div>
      </div>
    </aside>
  );
};
