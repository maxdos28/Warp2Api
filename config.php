<?php
/**
 * Warp2Api PHP Configuration
 * 为Cline和其他PHP工具提供基本配置
 */

// 基本配置
define('APP_NAME', 'Warp2Api');
define('APP_VERSION', '2.0.0');
define('APP_ENV', 'development');

// 服务器配置
define('BRIDGE_HOST', '127.0.0.1');
define('BRIDGE_PORT', 28888);
define('API_HOST', '127.0.0.1');
define('API_PORT', 28889);

// API 配置
$config = [
    'app' => [
        'name' => APP_NAME,
        'version' => APP_VERSION,
        'environment' => APP_ENV,
        'debug' => true
    ],
    
    'servers' => [
        'bridge' => [
            'host' => BRIDGE_HOST,
            'port' => BRIDGE_PORT,
            'url' => 'http://' . BRIDGE_HOST . ':' . BRIDGE_PORT
        ],
        'api' => [
            'host' => API_HOST,
            'port' => API_PORT,
            'url' => 'http://' . API_HOST . ':' . API_PORT
        ]
    ],
    
    'models' => [
        'claude-4-sonnet' => 'Claude 4 Sonnet 模型',
        'claude-4-opus' => 'Claude 4 Opus 模型',
        'claude-4.1-opus' => 'Claude 4.1 Opus 模型',
        'gemini-2.5-pro' => 'Gemini 2.5 Pro 模型',
        'gpt-4.1' => 'GPT-4.1 模型',
        'gpt-4o' => 'GPT-4o 模型',
        'gpt-5' => 'GPT-5 基础模型',
        'o3' => 'o3 模型',
        'o4-mini' => 'o4-mini 模型'
    ],
    
    'features' => [
        'openai_api' => true,
        'claude_api' => true,
        'streaming' => true,
        'jwt_auth' => true,
        'websocket_monitoring' => true,
        'rate_limiting' => true
    ],
    
    'paths' => [
        'logs' => '/workspace/logs',
        'proto' => '/workspace/proto',
        'scripts' => '/workspace/scripts'
    ]
];

/**
 * 获取配置值
 */
function getConfig($key = null, $default = null) {
    global $config;
    
    if ($key === null) {
        return $config;
    }
    
    $keys = explode('.', $key);
    $value = $config;
    
    foreach ($keys as $k) {
        if (is_array($value) && array_key_exists($k, $value)) {
            $value = $value[$k];
        } else {
            return $default;
        }
    }
    
    return $value;
}

/**
 * 检查功能是否启用
 */
function isFeatureEnabled($feature) {
    return getConfig("features.{$feature}", false);
}

/**
 * 获取服务器URL
 */
function getServerUrl($server) {
    return getConfig("servers.{$server}.url");
}

/**
 * 获取支持的模型列表
 */
function getSupportedModels() {
    return getConfig('models', []);
}

// 输出配置信息（仅在直接运行时）
if (basename($_SERVER['PHP_SELF']) == basename(__FILE__)) {
    echo "Warp2Api PHP Configuration Loaded\n";
    echo "==================================\n";
    echo "App: " . getConfig('app.name') . " v" . getConfig('app.version') . "\n";
    echo "Environment: " . getConfig('app.environment') . "\n";
    echo "Bridge Server: " . getServerUrl('bridge') . "\n";
    echo "API Server: " . getServerUrl('api') . "\n";
    echo "Supported Models: " . count(getSupportedModels()) . "\n";
    echo "Features Enabled: " . count(array_filter(getConfig('features'))) . "\n";
}
?>