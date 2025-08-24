import { memo } from 'react';
import { Handle, Position } from 'reactflow';

const OutputNode = memo(({ data, isConnectable, selected, id, onNodeDelete }) => {
  const handleDelete = (e) => {
    e.stopPropagation();
    if (onNodeDelete) {
      onNodeDelete(id);
    }
  };

  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-white border-2 min-w-[200px] relative ${
      selected ? 'border-blue-500' : 'border-gray-200'
    }`}>
      {/* Delete button */}
      {selected && (
        <button
          onClick={handleDelete}
          className="absolute -top-2 -right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs hover:bg-red-600 transition-colors z-10"
          title="Delete node"
        >
          ×
        </button>
      )}

      <Handle
        type="target"
        position={Position.Top}
        isConnectable={isConnectable}
        style={{ width: 14, height: 14 }}
      />
      <div className="flex items-center">
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-orange-100">
          📤
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold">Output</div>
          <div className="text-gray-500">Final result</div>
        </div>
      </div>
      <Handle
        type="source"
        position={Position.Bottom}
        isConnectable={isConnectable}
        style={{ width: 14, height: 14 }}
      />
    </div>
  );
});

OutputNode.displayName = 'OutputNode';

export default OutputNode;
