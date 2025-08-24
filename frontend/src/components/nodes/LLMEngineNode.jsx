import { memo, useState, useEffect } from 'react';
import { Handle, Position } from 'reactflow';

const LLMEngineNode = memo(({ data, isConnectable, selected, id, onNodeDelete }) => {
  const [config, setConfig] = useState({
    provider: 'openai',
    model: 'gpt-3.5-turbo',
    api_key: '',
    temperature: 0.7,
    max_tokens: 1000,
    use_web_search: false,
    serp_api_key: '',
    custom_prompt: ''
  });

  // Initialize config from data if available
  useEffect(() => {
    if (data) {
      setConfig(prev => ({
        ...prev,
        ...data
      }));
    }
  }, [data]);

  const handleConfigChange = (field, value) => {
    let newConfig = {
      ...config,
      [field]: value
    };
    
    // If provider changes, ensure model is valid for that provider
    if (field === 'provider') {
      const options = getModelOptions(value);
      const firstModel = options[0]?.value;
      if (firstModel && !options.find(o => o.value === newConfig.model)) {
        newConfig = { ...newConfig, model: firstModel };
      }
    }
    
    setConfig(newConfig);
    
    // Update the node data so it gets saved with the workflow
    if (data && data.onChange) {
      data.onChange(newConfig);
    }
  };

  const getModelOptions = (provider) => {
    switch (provider) {
      case 'openai':
        return [
          { value: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
          { value: 'gpt-4', label: 'GPT-4' },
          { value: 'gpt-4-turbo', label: 'GPT-4 Turbo' }
        ];
      case 'anthropic':
        return [
          { value: 'claude-3-sonnet', label: 'Claude 3 Sonnet' },
          { value: 'claude-3-opus', label: 'Claude 3 Opus' },
          { value: 'claude-3-haiku', label: 'Claude 3 Haiku' }
        ];
      case 'gemini':
        return [
          { value: 'gemini-2.5-pro', label: 'Gemini 2.5 Pro' },
          { value: 'gemini-2.5-flash', label: 'Gemini 2.5 Flash' },
          { value: 'gemini-2.5-flash-lite', label: 'Gemini 2.5 Flash Lite' },
          { value: 'gemini-2.0-flash', label: 'Gemini 2.0 Flash' },
          { value: 'gemini-2.0-flash-lite', label: 'Gemini 2.0 Flash Lite' }
        ];
      default:
        return [];
    }
  };

  const handleDelete = (e) => {
    e.stopPropagation();
    if (onNodeDelete) {
      onNodeDelete(id);
    }
  };

  return (
    <div className={`px-4 py-2 shadow-md rounded-md bg-white border-2 min-w-[350px] relative ${
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
        <div className="rounded-full w-12 h-12 flex items-center justify-center bg-purple-100">
          ✨
        </div>
        <div className="ml-2">
          <div className="text-lg font-bold">LLM Engine</div>
          <div className="text-gray-500">AI model processing</div>
        </div>
      </div>
      
      <div className="mt-3 space-y-2">
        <div>
          <label className="block text-xs font-medium text-gray-700">Provider</label>
          <select
            value={config.provider}
            onChange={(e) => handleConfigChange('provider', e.target.value)}
            className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
          >
            <option value="openai">OpenAI</option>
            <option value="anthropic">Anthropic (Claude)</option>
            <option value="gemini">Google Gemini</option>
          </select>
        </div>
        
        <div>
          <label className="block text-xs font-medium text-gray-700">Model</label>
          <select
            value={config.model}
            onChange={(e) => handleConfigChange('model', e.target.value)}
            className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
          >
            {getModelOptions(config.provider).map(option => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-medium text-gray-700">
            API Key <span className="text-red-500">*</span>
          </label>
          <input
            type="password"
            value={config.api_key}
            onChange={(e) => handleConfigChange('api_key', e.target.value)}
            placeholder={`Enter your ${config.provider} API key`}
            className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
          />
          <p className="text-xs text-gray-500 mt-1">
            Your API key is stored locally and only used for this workflow
          </p>
        </div>
        
        <div className="grid grid-cols-2 gap-2">
          <div>
            <label className="block text-xs font-medium text-gray-700">Temperature</label>
            <input
              type="range"
              min="0"
              max="2"
              step="0.1"
              value={config.temperature}
              onChange={(e) => handleConfigChange('temperature', parseFloat(e.target.value))}
              className="mt-1 block w-full"
            />
            <span className="text-xs text-gray-500">{config.temperature}</span>
          </div>
          
          <div>
            <label className="block text-xs font-medium text-gray-700">Max Tokens</label>
            <input
              type="number"
              value={config.max_tokens}
              onChange={(e) => handleConfigChange('max_tokens', parseInt(e.target.value))}
              className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
            />
          </div>
        </div>
        
        <div>
          <label className="flex items-center text-xs font-medium text-gray-700">
            <input
              type="checkbox"
              checked={config.use_web_search}
              onChange={(e) => handleConfigChange('use_web_search', e.target.checked)}
              className="mr-2"
            />
            Use Web Search
          </label>
        </div>
        
        {config.use_web_search && (
          <div>
            <label className="block text-xs font-medium text-gray-700">
              SERP API Key <span className="text-red-500">*</span>
            </label>
            <input
              type="password"
              value={config.serp_api_key}
              onChange={(e) => handleConfigChange('serp_api_key', e.target.value)}
              placeholder="Enter your SERP API key for web search"
              className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
            />
            <p className="text-xs text-gray-500 mt-1">
              Required for web search functionality. Get your key from <a href="https://serpapi.com" target="_blank" rel="noopener noreferrer" className="text-blue-500 hover:underline">serpapi.com</a>
            </p>
          </div>
        )}
        
        <div>
          <label className="block text-xs font-medium text-gray-700">Custom Prompt (Optional)</label>
          <textarea
            value={config.custom_prompt}
            onChange={(e) => handleConfigChange('custom_prompt', e.target.value)}
            placeholder="Enter custom prompt..."
            className="mt-1 block w-full text-xs border border-gray-300 rounded px-2 py-1"
            rows="2"
          />
        </div>

        {!config.api_key && (
          <div className="bg-yellow-50 border border-yellow-200 rounded p-2">
            <p className="text-xs text-yellow-800">
              ⚠️ API key required for real LLM responses. Without it, mock responses will be used.
            </p>
          </div>
        )}
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

LLMEngineNode.displayName = 'LLMEngineNode';

export default LLMEngineNode;
