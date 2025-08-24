import { useState, useRef, useCallback, useEffect, useMemo } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import ReactFlow, {
  addEdge,
  useNodesState,
  useEdgesState,
  Controls,
  Background,
  MiniMap,
  Panel,
  useReactFlow,
  ReactFlowProvider,
  getBezierPath,
} from 'reactflow';
import 'reactflow/dist/style.css';

import UserQueryNode from './nodes/UserQueryNode';
import KnowledgeBaseNode from './nodes/KnowledgeBaseNode';
import LLMEngineNode from './nodes/LLMEngineNode';
import OutputNode from './nodes/OutputNode';
import ChatInterface from './ChatInterface';
import { workflowsAPI } from '../services/api';

const nodeTypes = {
  userQuery: UserQueryNode,
  knowledgeBase: KnowledgeBaseNode,
  llmEngine: LLMEngineNode,
  output: OutputNode,
};

// Custom edge component with delete button
const CustomEdge = ({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  style = {},
  markerEnd,
  onEdgeClick,
  selected,
}) => {
  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  const [isHovered, setIsHovered] = useState(false);

  // Increase visible stroke width while respecting provided style
  const visibleStyle = {
    stroke: '#333',
    strokeWidth: Math.max(4, (style && style.strokeWidth) ? style.strokeWidth : 0),
    ...style,
  };

  return (
    <>
      {/* Wide invisible hit path to make edge easier to hover/select */}
      <path
        d={edgePath}
        className="react-flow__edge-path"
        style={{ stroke: 'transparent', strokeWidth: 16, cursor: 'pointer' }}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />
      <path
        id={id}
        style={visibleStyle}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
      />
      {(selected || isHovered) && (
        <foreignObject
          width={40}
          height={40}
          x={labelX - 20}
          y={labelY - 20}
          className="edgebutton-foreignobject"
          requiredExtensions="http://www.w3.org/1999/xhtml"
        >
          <div className="flex items-center justify-center">
            <button
              className="edgebutton bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 transition-colors"
              onClick={(event) => {
                event.stopPropagation();
                onEdgeClick(event, id);
              }}
            >
              ×
            </button>
          </div>
        </foreignObject>
      )}
    </>
  );
};

// Separate component for the flow content
const FlowContent = ({ 
  nodes, 
  setNodes, 
  edges, 
  setEdges, 
  onNodesChange, 
  onEdgesChange, 
  onConnect, 
  onNodeClick, 
  onPaneClick, 
  onDragOver, 
  onDrop, 
  nodeTypes, 
  handleRunWorkflow, 
  showChat, 
  setShowChat, 
  itemId, 
  workflowId 
}) => {
  const { project } = useReactFlow();
  const reactFlowWrapper = useRef(null);

  const onDropCallback = useCallback(
    (event) => {
      event.preventDefault();

      const reactFlowBounds = reactFlowWrapper.current.getBoundingClientRect();
      const type = event.dataTransfer.getData('application/reactflow');
      const position = project({
        x: event.clientX - reactFlowBounds.left,
        y: event.clientY - reactFlowBounds.top,
      });

      const newId = `${type}_${Date.now()}`;
      const newNode = {
        id: newId,
        type,
        position,
        data: { 
          label: type,
          onChange: (newData) => {
            // Update node data when configuration changes
            setNodes((nds) =>
              nds.map((node) =>
                node.id === newId 
                  ? { ...node, data: { ...node.data, ...newData } }
                  : node
              )
            );
          }
        },
      };

      setNodes((nds) => nds.concat(newNode));
    },
    [project, setNodes],
  );

  // Handle edge deletion
  const onEdgeClick = useCallback((event, edgeId) => {
    setEdges((eds) => eds.filter((edge) => edge.id !== edgeId));
  }, [setEdges]);

  // Handle node deletion
  const onNodeDelete = useCallback((nodeId) => {
    setNodes((nds) => nds.filter((node) => node.id !== nodeId));
    // Also remove any edges connected to this node
    setEdges((eds) => eds.filter((edge) => edge.source !== nodeId && edge.target !== nodeId));
  }, [setNodes, setEdges]);

  // Handle node deletion with keyboard
  useEffect(() => {
    const handleKeyDown = (event) => {
      if (event.key === 'Delete' || event.key === 'Backspace') {
        setNodes((nds) => nds.filter((node) => !node.selected));
        setEdges((eds) => eds.filter((edge) => !edge.selected));
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [setNodes, setEdges]);

  const edgeTypes = useMemo(() => ({
    custom: (props) => <CustomEdge {...props} onEdgeClick={onEdgeClick} />,
  }), [onEdgeClick]);

  // Create node types with delete function
  const nodeTypesWithDelete = useMemo(() => {
    const mapped = {};
    Object.keys(nodeTypes).forEach((key) => {
      const NodeComponent = nodeTypes[key];
      mapped[key] = (props) => (
        <NodeComponent
          {...props}
          onNodeDelete={onNodeDelete}
          workflowId={workflowId || null}
        />
      );
    });
    return mapped;
  }, [nodeTypes, onNodeDelete, workflowId]);

  return (
    <div ref={reactFlowWrapper} className="h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        onDragOver={onDragOver}
        onDrop={onDropCallback}
        nodeTypes={nodeTypesWithDelete}
        edgeTypes={edgeTypes}
        onEdgeClick={onEdgeClick}
        deleteKeyCode="Delete"
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
        <Panel position="bottom-left" className="bg-white rounded-lg shadow-md p-2">
          <div className="flex space-x-2">
            <button
              onClick={handleRunWorkflow}
              className="px-3 py-1 bg-green-500 text-white rounded hover:bg-green-600 text-sm"
            >
              ▶️ Run
            </button>
            <button
              onClick={() => setShowChat(!showChat)}
              className="px-3 py-1 bg-blue-500 text-white rounded hover:bg-blue-600 text-sm"
            >
              💬 Chat
            </button>
          </div>
        </Panel>
        <Panel position="top-right" className="bg-white rounded-lg shadow-md p-2">
          <div className="text-xs text-gray-600">
            <div>💡 <strong>Delete:</strong> Select element + Delete key</div>
            <div>💡 <strong>Connect:</strong> Drag from node handles</div>
            <div>💡 <strong>Remove:</strong> Click red × button on selected elements</div>
          </div>
        </Panel>
      </ReactFlow>

      {/* Chat Interface */}
      {showChat && (
        <div className="absolute bottom-4 right-4 w-96 h-96 bg-white rounded-lg shadow-lg border">
          <ChatInterface 
            workflowId={workflowId}
            hasUserQuery={nodes.some(n => n.type === 'userQuery')}
            onClose={() => setShowChat(false)}
          />
        </div>
      )}
    </div>
  );
};

const WorkflowBuilder = () => {
  const { itemId } = useParams();
  const navigate = useNavigate();
  const [nodes, setNodes, onNodesChange] = useNodesState([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);
  
  // Save nodes to localStorage as backup
  useEffect(() => {
    if (nodes.length > 0) {
      localStorage.setItem(`workflow-nodes-${itemId}`, JSON.stringify(nodes));
    }
  }, [nodes, itemId]);
  
  // Save edges to localStorage as backup
  useEffect(() => {
    if (edges.length > 0) {
      localStorage.setItem(`workflow-edges-${itemId}`, JSON.stringify(edges));
    }
  }, [edges, itemId]);
  const [selectedNode, setSelectedNode] = useState(null);
  const [showChat, setShowChat] = useState(false);
  const [workflowData, setWorkflowData] = useState(null);
  const [isLoading, setIsLoading] = useState(false);
  const [savedWorkflowId, setSavedWorkflowId] = useState(null);
  const [toast, setToast] = useState({ message: '', type: 'success', visible: false });
  const toastTimerRef = useRef(null);

  const showToast = useCallback((message, type = 'success') => {
    if (toastTimerRef.current) clearTimeout(toastTimerRef.current);
    setToast({ message, type, visible: true });
    toastTimerRef.current = setTimeout(() => {
      setToast((t) => ({ ...t, visible: false }));
    }, 3000);
  }, []);

  // Load workflow data on component mount
  useEffect(() => {
    loadWorkflowData();
  }, [itemId]);



  const loadWorkflowData = async () => {
    try {
      console.log('Loading workflow data for itemId:', itemId);
      
      // Try to load existing workflow for this item
      const workflows = await workflowsAPI.getAll();
      console.log('All workflows:', workflows);
      
      const existingWorkflow = workflows.find(w => w.item_id === itemId);
      console.log('Existing workflow found:', existingWorkflow);
      
      if (existingWorkflow) {
        console.log('Setting saved workflow ID:', existingWorkflow.id);
        setWorkflowData(existingWorkflow);
        setSavedWorkflowId(existingWorkflow.id);
        
        // Load existing nodes and edges
        if (existingWorkflow.components) {
          console.log('Loading existing components:', existingWorkflow.components);
          // Reattach onChange handlers so node UIs can persist config changes
          const nodesWithHandlers = (existingWorkflow.components.nodes || []).map((n) => ({
            ...n,
            data: {
              ...(n.data || {}),
              onChange: (newData) => {
                setNodes((nds) =>
                  nds.map((node) =>
                    node.id === n.id
                      ? { ...node, data: { ...node.data, ...newData } }
                      : node
                  )
                );
              },
            },
          }));
          setNodes(nodesWithHandlers);
          setEdges(existingWorkflow.components.edges || []);
        } else {
          // Fallback to localStorage if no components in database
          const savedNodes = localStorage.getItem(`workflow-nodes-${itemId}`);
          const savedEdges = localStorage.getItem(`workflow-edges-${itemId}`);
          
          if (savedNodes) {
            try {
              const parsedNodes = JSON.parse(savedNodes);
              const nodesWithHandlers = parsedNodes.map((n) => ({
                ...n,
                data: {
                  ...(n.data || {}),
                  onChange: (newData) => {
                    setNodes((nds) =>
                      nds.map((node) =>
                        node.id === n.id
                          ? { ...node, data: { ...node.data, ...newData } }
                          : node
                      )
                    );
                  },
                },
              }));
              setNodes(nodesWithHandlers);
              console.log('Loaded nodes from localStorage');
            } catch (error) {
              console.error('Error loading nodes from localStorage:', error);
            }
          }
          
          if (savedEdges) {
            try {
              const parsedEdges = JSON.parse(savedEdges);
              setEdges(parsedEdges);
              console.log('Loaded edges from localStorage');
            } catch (error) {
              console.error('Error loading edges from localStorage:', error);
            }
          }
        }
      } else {
        console.log('No existing workflow found, creating new one');
        setWorkflowData({
          id: itemId,
          name: `Workflow for Item ${itemId}`,
          components: { nodes: [], edges: [] }
        });
      }
    } catch (error) {
      console.error('Error loading workflow:', error);
      setWorkflowData({
        id: itemId,
        name: `Workflow for Item ${itemId}`,
        components: { nodes: [], edges: [] }
      });
    }
  };

  const onConnect = useCallback(
    (params) => setEdges((eds) => addEdge({
      ...params,
      type: 'custom', // Use custom edge type
      style: { stroke: '#333', strokeWidth: 4 }
    }, eds)),
    [setEdges],
  );

  const onDragOver = useCallback((event) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onNodeClick = useCallback((event, node) => {
    setSelectedNode(node);
  }, []);

  const onPaneClick = useCallback(() => {
    setSelectedNode(null);
  }, []);



  const handleSaveWorkflow = async () => {
    setIsLoading(true);
    try {
      const workflowComponents = {
        nodes: nodes.map(node => {
          const { onChange, ...restData } = node.data || {};
          return ({
          id: node.id,
          type: node.type,
          position: node.position,
          // Persist only serializable data (e.g., LLM config) and drop functions
          data: restData,
        });
        }),
        edges: edges.map(edge => ({
          id: edge.id,
          source: edge.source,
          target: edge.target,
          type: edge.type
        }))
      };

      const workflowData = {
        name: `Workflow for Item ${itemId}`,
        description: 'AI Workflow',
        components: workflowComponents
      };

      console.log('Saving workflow with data:', workflowData);
      console.log('Saved workflow ID:', savedWorkflowId);
      console.log('Type of savedWorkflowId:', typeof savedWorkflowId);
      console.log('Boolean check for savedWorkflowId:', !!savedWorkflowId);

      let result;
      if (savedWorkflowId) {
        // Update existing workflow
        console.log('Updating existing workflow:', savedWorkflowId);
        result = await workflowsAPI.update(savedWorkflowId, workflowData);
      } else {
        // Create new workflow
        console.log('Creating new workflow');
        result = await workflowsAPI.create(workflowData, itemId);
        console.log('Created workflow result:', result);
        setSavedWorkflowId(result.id);
      }

      console.log('Workflow save result:', result);
      showToast('Workflow saved successfully!', 'success');
    } catch (error) {
      console.error('Error saving workflow:', error);
      showToast(`Failed to save workflow: ${error.message}`, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunWorkflow = () => {
    if (nodes.length === 0) {
      showToast('Please add components to your workflow first', 'error');
      return;
    }
    if (!savedWorkflowId) {
      showToast('Please save your workflow first before running it', 'error');
      return;
    }
    // Validate that there is an Output node and it has an incoming connection
    const outputNode = nodes.find(n => n.type === 'output');
    if (!outputNode) {
      showToast('Add an Output node to run the workflow', 'error');
      return;
    }
    const hasIncomingToOutput = edges.some(e => e.target === outputNode.id);
    if (!hasIncomingToOutput) {
      showToast('Connect something into the Output node', 'error');
      return;
    }
    setShowChat(true);
  };

  const handleBack = () => {
    navigate('/');
  };

  const onDragStart = (event, nodeType) => {
    event.dataTransfer.setData('application/reactflow', nodeType);
    event.dataTransfer.effectAllowed = 'move';
  };

  return (
    <div className="h-screen flex flex-col bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center space-x-3">
          <button
            onClick={handleBack}
            className="p-2 text-gray-600 hover:text-gray-900 hover:bg-gray-100 rounded-md transition-colors"
            title="Back to Dashboard"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div className="w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">ai</span>
          </div>
          <h1 className="text-xl font-semibold text-gray-900">AI Workflow Builder</h1>
          <span className="text-sm text-gray-500">- Item {itemId}</span>
        </div>
        <div className="flex items-center space-x-3">
          <button
            onClick={handleSaveWorkflow}
            disabled={isLoading}
            className="flex items-center space-x-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
          >
            <span>💾</span>
            <span>{isLoading ? 'Saving...' : 'Save'}</span>
          </button>
          <div className="w-8 h-8 bg-purple-500 rounded-full flex items-center justify-center">
            <span className="text-white font-bold text-sm">S</span>
          </div>
        </div>
      </div>

      <div className="flex flex-1 overflow-hidden">
        {/* Left Sidebar */}
        <div className="w-64 bg-white border-r border-gray-200 p-4">
          <button className="w-full mb-6 px-4 py-3 bg-white border border-gray-300 rounded-md hover:bg-gray-50 flex items-center space-x-3">
            <span>📁</span>
            <span>Chat With AI</span>
          </button>

          <h3 className="font-semibold text-gray-900 mb-4">Components</h3>
          <div className="space-y-2">
            {[
              { type: 'userQuery', name: 'User Query', icon: '📄' },
              { type: 'knowledgeBase', name: 'Knowledge Base', icon: '📚' },
              { type: 'llmEngine', name: 'LLM Engine', icon: '✨' },
              { type: 'output', name: 'Output', icon: '📤' },
            ].map((component) => (
              <div
                key={component.type}
                draggable
                onDragStart={(event) => onDragStart(event, component.type)}
                className="px-4 py-3 bg-white border border-gray-300 rounded-md hover:bg-gray-50 cursor-move flex items-center justify-between"
              >
                <div className="flex items-center space-x-3">
                  <span className="text-lg">{component.icon}</span>
                  <span className="text-sm font-medium">{component.name}</span>
                </div>
                <span className="text-gray-400">☰</span>
              </div>
            ))}
          </div>
        </div>

        {/* Main Canvas */}
        <div className="flex-1 relative">
          <ReactFlowProvider>
            <FlowContent
              nodes={nodes}
              setNodes={setNodes}
              edges={edges}
              setEdges={setEdges}
              onNodesChange={onNodesChange}
              onEdgesChange={onEdgesChange}
              onConnect={onConnect}
              onNodeClick={onNodeClick}
              onPaneClick={onPaneClick}
              onDragOver={onDragOver}
              onDrop={() => {}}
              nodeTypes={nodeTypes}
              handleRunWorkflow={handleRunWorkflow}
              showChat={showChat}
              setShowChat={setShowChat}
              itemId={itemId}
              workflowId={savedWorkflowId}
            />
          </ReactFlowProvider>
        </div>
      </div>
      {toast.visible && (
        <div
          className={`fixed bottom-4 right-4 z-50 px-4 py-3 rounded shadow text-sm ${
            toast.type === 'success' ? 'bg-green-600 text-white' : 'bg-red-600 text-white'
          }`}
        >
          {toast.message}
        </div>
      )}
    </div>
  );
};

export default WorkflowBuilder;
