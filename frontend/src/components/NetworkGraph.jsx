import { useEffect, useRef } from 'react'
import * as d3 from 'd3'

export default function NetworkGraph({ graphData }) {
  const containerRef = useRef(null)

  useEffect(() => {
    if (!graphData || !graphData.nodes || graphData.nodes.length === 0 || !containerRef.current) {
      return
    }

    const width = containerRef.current.clientWidth
    const height = 380

    // Clear previous SVG
    d3.select(containerRef.current).selectAll('svg').remove()

    const svg = d3.select(containerRef.current)
      .append('svg')
      .attr('width', width)
      .attr('height', height)
      .attr('viewBox', [0, 0, width, height])
      .style('cursor', 'grab')

    const g = svg.append('g')

    const zoom = d3.zoom()
      .scaleExtent([0.2, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
      })

    svg.call(zoom)

    const nodes = graphData.nodes.map(d => ({ ...d }))
    const links = graphData.edges.map(d => ({ ...d }))

    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id(d => d.id).distance(120))
      .force('charge', d3.forceManyBody().strength(-400))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(40))

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
      .attr('fill', '#9CA3AF')

    const link = g.append('g')
      .attr('stroke', '#9CA3AF')
      .attr('stroke-opacity', 0.6)
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke-width', d => d.severity === 'severe' ? 3 : d.severity === 'moderate' ? 2 : 1)
      .attr('stroke', d => d.severity === 'severe' ? '#DC2626' : d.severity === 'moderate' ? '#D97706' : '#16A34A')
      .attr('marker-end', 'url(#arrow)')
      .attr('class', 'network-link')

    const node = g.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 14)
      .attr('fill', '#2185C5')
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .attr('class', 'network-node')
      .style('cursor', 'pointer')
      .call(d3.drag()
        .on('start', (event, d) => {
          if (!event.active) simulation.alphaTarget(0.3).restart()
          d.fx = d.x
          d.fy = d.y
          svg.style('cursor', 'grabbing')
        })
        .on('drag', (event, d) => {
          d.fx = event.x
          d.fy = event.y
        })
        .on('end', (event, d) => {
          if (!event.active) simulation.alphaTarget(0)
          d.fx = null
          d.fy = null
          svg.style('cursor', 'grab')
        }))

    const labels = g.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .attr('class', 'node-label')
      .attr('dy', -22)
      .attr('text-anchor', 'middle')
      .text(d => d.label)
      .style('pointer-events', 'none')

    // Hover interactions
    node.on('mouseover', (event, d) => {
      const connectedNodeIds = new Set()
      connectedNodeIds.add(d.id)
      
      link.each(l => {
        if (l.source.id === d.id) connectedNodeIds.add(l.target.id)
        if (l.target.id === d.id) connectedNodeIds.add(l.source.id)
      })

      node.transition().duration(200)
        .style('opacity', n => connectedNodeIds.has(n.id) ? 1 : 0.15)
      
      link.transition().duration(200)
        .style('opacity', l => (l.source.id === d.id || l.target.id === d.id) ? 1 : 0.1)
      
      labels.transition().duration(200)
        .style('opacity', n => connectedNodeIds.has(n.id) ? 1 : 0.15)
    }).on('mouseout', () => {
      node.transition().duration(200).style('opacity', 1)
      link.transition().duration(200).style('opacity', 1)
      labels.transition().duration(200).style('opacity', 1)
    })

    simulation.on('tick', () => {
      link
        .attr('x1', d => d.source.x)
        .attr('y1', d => d.source.y)
        .attr('x2', d => d.target.x)
        .attr('y2', d => d.target.y)
      node
        .attr('cx', d => d.x)
        .attr('cy', d => d.y)
      labels
        .attr('x', d => d.x)
        .attr('y', d => d.y)
    })

    return () => {
      simulation.stop()
    }
  }, [graphData])

  return (
    <section className="card">
      <div className="card-header">
        <h2>Interaction Network</h2>
      </div>
      <div className="card-body">
        <div className="network-container" ref={containerRef}>
          {(!graphData || !graphData.nodes || graphData.nodes.length === 0) && (
            <div className="empty-state">
              <p>Network graph will appear here</p>
            </div>
          )}
        </div>
      </div>
    </section>
  )
}
