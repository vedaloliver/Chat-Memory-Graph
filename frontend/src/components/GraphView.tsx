import React, { useCallback, useState } from 'react';
import ReactFlow, {
  Controls,
  Background,
  useNodesState,
  useEdgesState,
  MiniMap,
  BackgroundVariant,
  MarkerType,
  Handle,
  Position,
} from 'reactflow';
import type { Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import './GraphView.css';
import { MessageSquare, Users, FileText, ChevronDown, ChevronRight } from 'lucide-react';

// Mock data for the 3-layer hierarchy
const mockGraphData = {
  sessionSummaries: [
    {
      id: 'session-1',
      title: 'Planning Sprint Goals',
      summary: 'Discussion about sprint planning and team goals for Q4',
      keywords: ['sprint', 'planning', 'goals', 'Q4'],
      themes: ['project management', 'team coordination'],
      timestamp: '2024-01-15T10:30:00Z',
    },
    {
      id: 'session-2',
      title: 'Technical Architecture Review',
      summary: 'Deep dive into microservices architecture and database design',
      keywords: ['architecture', 'microservices', 'database', 'design'],
      themes: ['technical design', 'system architecture'],
      timestamp: '2024-01-16T14:20:00Z',
    },
  ],
  entities: [
    { id: 'entity-1', name: 'Oliver', type: 'person' },
    { id: 'entity-2', name: 'Hazal', type: 'person' },
    { id: 'entity-3', name: 'PVM Project', type: 'project' },
    { id: 'entity-4', name: 'Sprint Deadline', type: 'concept' },
    { id: 'entity-5', name: 'Microservices', type: 'technology' },
    { id: 'entity-6', name: 'PostgreSQL', type: 'technology' },
  ],
  triples: [
    { id: 'triple-1', subject: 'entity-1', relation: 'works_on', object: 'entity-3', sessionId: 'session-1' },
    { id: 'triple-2', subject: 'entity-2', relation: 'collaborates_with', object: 'entity-1', sessionId: 'session-1' },
    { id: 'triple-3', subject: 'entity-1', relation: 'concerned_about', object: 'entity-4', sessionId: 'session-1' },
    { id: 'triple-4', subject: 'entity-3', relation: 'uses', object: 'entity-5', sessionId: 'session-2' },
    { id: 'triple-5', subject: 'entity-5', relation: 'depends_on', object: 'entity-6', sessionId: 'session-2' },
  ],
  chunks: [
    { id: 'chunk-1', text: 'Oliver mentioned stress about the PVM project deadline...', sessionId: 'session-1', tripleIds: ['triple-1', 'triple-3'] },
    { id: 'chunk-2', text: 'Hazal and Oliver discussed team collaboration strategies...', sessionId: 'session-1', tripleIds: ['triple-2'] },
    { id: 'chunk-3', text: 'Review of microservices architecture for the PVM project...', sessionId: 'session-2', tripleIds: ['triple-4', 'triple-5'] },
  ],
};

interface CustomNodeData {
  label: string;
  type: 'session' | 'entity' | 'triple' | 'chunk';
  expanded?: boolean;
  details?: any;
}

// Custom node component for better styling
const CustomNode: React.FC<{ data: CustomNodeData }> = ({ data }) => {
  const getIcon = () => {
    switch (data.type) {
      case 'session':
        return <MessageSquare className="w-4 h-4" />;
      case 'entity':
        return <Users className="w-4 h-4" />;
      case 'chunk':
        return <FileText className="w-4 h-4" />;
      default:
        return null;
    }
  };

  const getNodeClass = () => {
    switch (data.type) {
      case 'session':
        return 'graph-node-session';
      case 'entity':
        return 'graph-node-entity';
      case 'triple':
        return 'graph-node-triple';
      case 'chunk':
        return 'graph-node-chunk';
      default:
        return '';
    }
  };

  return (
    <div className={`graph-node ${getNodeClass()}`}>
      {/* Target handle (input) - top */}
      <Handle
        type="target"
        position={Position.Top}
        style={{ background: '#555', width: 12, height: 12 }}
      />
      
      <div className="graph-node-header">
        <div className="graph-node-icon">{getIcon()}</div>
        <div className="graph-node-label">{data.label}</div>
      </div>
      {data.details && (
        <div className="graph-node-details">{data.details}</div>
      )}
      
      {/* Source handle (output) - bottom */}
      <Handle
        type="source"
        position={Position.Bottom}
        style={{ background: '#555', width: 12, height: 12 }}
      />
    </div>
  );
};

const nodeTypes = {
  custom: CustomNode,
};

const GraphView: React.FC = () => {
  const [expandedSessions, setExpandedSessions] = useState<Set<string>>(new Set(['session-1']));

  // Generate initial nodes and edges based on mock data
  const generateGraphData = useCallback(() => {
    const nodes: Node[] = [];
    const edges: Edge[] = [];

    // Layer 1: Session Summaries (Top)
    mockGraphData.sessionSummaries.forEach((session, index) => {
      nodes.push({
        id: session.id,
        type: 'custom',
        position: { x: 200 + index * 500, y: 80 },
        data: {
          label: session.title,
          type: 'session',
          details: session.keywords.join(', '),
          expanded: expandedSessions.has(session.id),
        },
      });
    });

    // Layer 2: Entities and Triples (Middle)
    // First, collect all unique entities per session
    const entitiesPerSession = new Map<string, string[]>();
    mockGraphData.triples.forEach((triple) => {
      if (!entitiesPerSession.has(triple.sessionId)) {
        entitiesPerSession.set(triple.sessionId, []);
      }
      const entities = entitiesPerSession.get(triple.sessionId)!;
      if (!entities.includes(triple.subject)) entities.push(triple.subject);
      if (triple.object && !entities.includes(triple.object)) entities.push(triple.object);
    });

    // Create entity nodes and edges from session to entity
    let entityXOffset = 0;
    entitiesPerSession.forEach((entityIds, sessionId) => {
      if (expandedSessions.has(sessionId)) {
        entityIds.forEach((entityId, idx) => {
          const entity = mockGraphData.entities.find((e) => e.id === entityId);
          if (entity) {
            const nodeId = entityId; // Use the entity ID directly
            nodes.push({
              id: nodeId,
              type: 'custom',
              position: { x: 150 + entityXOffset + idx * 240, y: 280 },
              data: {
                label: entity.name,
                type: 'entity',
                details: entity.type,
              },
            });

            // Edge from session to entity
            edges.push({
              id: `${sessionId}-to-${nodeId}`,
              source: sessionId,
              target: nodeId,
              type: 'smoothstep',
              animated: false,
              style: { stroke: '#60a5fa', strokeWidth: 2 },
              markerEnd: { type: MarkerType.ArrowClosed, color: '#60a5fa' },
            });
          }
        });
        entityXOffset += entityIds.length * 240 + 80;
      }
    });

    // Add triples as connecting edges between entities
    mockGraphData.triples.forEach((triple) => {
      if (expandedSessions.has(triple.sessionId)) {
        const sourceNodeId = triple.subject; // Use entity ID directly
        const targetNodeId = triple.object;   // Use entity ID directly
        
        // Check if both nodes exist
        if (nodes.find(n => n.id === sourceNodeId) && nodes.find(n => n.id === targetNodeId)) {
          edges.push({
            id: triple.id,
            source: sourceNodeId,
            target: targetNodeId,
            label: triple.relation.replace(/_/g, ' '),
            type: 'smoothstep',
            animated: false,
            style: { stroke: '#a78bfa', strokeWidth: 2.5 },
            markerEnd: { type: MarkerType.ArrowClosed, color: '#a78bfa' },
            labelStyle: { fontSize: 12, fill: '#e6edf3', fontWeight: 600 },
            labelBgStyle: { fill: '#7c3aed', fillOpacity: 0.9 },
            labelBgPadding: [8, 12],
          });
        }
      }
    });

    // Layer 3: Memory Chunks (Bottom)
    let chunkXOffset = 0;
    mockGraphData.chunks.forEach((chunk, index) => {
      if (expandedSessions.has(chunk.sessionId)) {
        nodes.push({
          id: chunk.id,
          type: 'custom',
          position: { x: 200 + chunkXOffset, y: 520 },
          data: {
            label: `Chunk ${index + 1}`,
            type: 'chunk',
            details: chunk.text.substring(0, 35) + '...',
          },
        });

        // Connect chunks to their related triples
        chunk.tripleIds.forEach((tripleId) => {
          const triple = mockGraphData.triples.find((t) => t.id === tripleId);
          if (triple) {
            const entityNodeId = triple.subject; // Use entity ID directly
            if (nodes.find(n => n.id === entityNodeId)) {
              edges.push({
                id: `${chunk.id}-to-${entityNodeId}`,
                source: chunk.id,
                target: entityNodeId,
                type: 'smoothstep',
                animated: false,
                style: { stroke: '#fb923c', strokeWidth: 2, strokeDasharray: '5,5' },
                markerEnd: { type: MarkerType.Arrow, color: '#fb923c' },
              });
            }
          }
        });

        chunkXOffset += 350;
      }
    });

    console.log('Generated nodes:', nodes.length);
    console.log('Generated edges:', edges.length);
    console.log('Edges data:', edges);
    return { nodes, edges };
  }, [expandedSessions]);

  const { nodes: initialNodes, edges: initialEdges } = generateGraphData();
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  
  console.log('ReactFlow nodes:', nodes);
  console.log('ReactFlow edges:', edges);

  // Update graph when sessions are expanded/collapsed
  React.useEffect(() => {
    const { nodes: newNodes, edges: newEdges } = generateGraphData();
    setNodes(newNodes);
    setEdges(newEdges);
  }, [expandedSessions, generateGraphData, setNodes, setEdges]);

  const toggleSession = (sessionId: string) => {
    setExpandedSessions((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(sessionId)) {
        newSet.delete(sessionId);
      } else {
        newSet.add(sessionId);
      }
      return newSet;
    });
  };

  return (
    <div className="graph-view-container">
      {/* Header with Controls */}
      <div className="graph-header">
        <div className="graph-header-content">
          <h1>Memory Graph</h1>
          <p>
            Three-layer hierarchical view: Sessions → Entities/Triples → Chunks
          </p>
        </div>
        <div>
          {/* Legend */}
          <div className="graph-legend">
            <div className="graph-legend-item">
              <div className="graph-legend-color legend-session"></div>
              <span>Session</span>
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color legend-entity"></div>
              <span>Entity</span>
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color legend-triple"></div>
              <span>Triple</span>
            </div>
            <div className="graph-legend-item">
              <div className="graph-legend-color legend-chunk"></div>
              <span>Chunk</span>
            </div>
          </div>
        </div>
      </div>

      {/* Session Toggle Controls */}
      <div className="graph-session-controls">
        <span className="graph-session-controls-label">Sessions:</span>
        {mockGraphData.sessionSummaries.map((session) => (
          <button
            key={session.id}
            onClick={() => toggleSession(session.id)}
            className={`session-toggle-button ${expandedSessions.has(session.id) ? 'expanded' : ''}`}
          >
            {expandedSessions.has(session.id) ? (
              <ChevronDown className="w-4 h-4" />
            ) : (
              <ChevronRight className="w-4 h-4" />
            )}
            <span>{session.title}</span>
          </button>
        ))}
      </div>

      {/* Graph Canvas */}
      <div className="graph-canvas">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          attributionPosition="bottom-left"
          defaultEdgeOptions={{
            style: { strokeWidth: 2 },
          }}
          minZoom={0.2}
          maxZoom={2}
        >
          <Background variant={BackgroundVariant.Dots} gap={16} size={1.5} color="#6366f1" />
          <Controls />
          <MiniMap
            nodeColor={(node) => {
              const data = node.data as CustomNodeData;
              switch (data.type) {
                case 'session':
                  return '#60a5fa';
                case 'entity':
                  return '#4ade80';
                case 'triple':
                  return '#a78bfa';
                case 'chunk':
                  return '#fb923c';
                default:
                  return '#94a3b8';
              }
            }}
            maskColor="rgb(240, 240, 255, 0.7)"
          />
        </ReactFlow>
      </div>
    </div>
  );
};

export default GraphView;
