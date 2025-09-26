<?php

namespace App\Models;

/**
 * ReleaseSheet Model
 * 用于管理Warp2Api项目的发布表单和版本信息
 */
class ReleaseSheet {
    
    protected $table = 'release_sheets';
    protected $fillable = [
        'version',
        'release_date',
        'description',
        'features',
        'bug_fixes',
        'breaking_changes',
        'migration_notes',
        'status'
    ];
    
    protected $casts = [
        'features' => 'array',
        'bug_fixes' => 'array',
        'breaking_changes' => 'array',
        'release_date' => 'datetime'
    ];
    
    public function __construct($attributes = []) {
        $this->attributes = array_merge([
            'version' => '1.0.0',
            'status' => 'draft',
            'features' => [],
            'bug_fixes' => [],
            'breaking_changes' => []
        ], $attributes);
    }
    
    /**
     * 获取发布版本信息
     */
    public function getVersionInfo() {
        return [
            'version' => $this->getAttribute('version'),
            'release_date' => $this->getAttribute('release_date'),
            'status' => $this->getAttribute('status')
        ];
    }
    
    /**
     * 添加新功能
     */
    public function addFeature($feature) {
        $features = $this->getAttribute('features') ?? [];
        $features[] = [
            'title' => $feature['title'] ?? '',
            'description' => $feature['description'] ?? '',
            'type' => $feature['type'] ?? 'enhancement',
            'added_at' => date('Y-m-d H:i:s')
        ];
        $this->setAttribute('features', $features);
        return $this;
    }
    
    /**
     * 添加bug修复
     */
    public function addBugFix($bugFix) {
        $bugFixes = $this->getAttribute('bug_fixes') ?? [];
        $bugFixes[] = [
            'issue' => $bugFix['issue'] ?? '',
            'solution' => $bugFix['solution'] ?? '',
            'severity' => $bugFix['severity'] ?? 'medium',
            'fixed_at' => date('Y-m-d H:i:s')
        ];
        $this->setAttribute('bug_fixes', $bugFixes);
        return $this;
    }
    
    /**
     * 设置发布状态
     */
    public function setStatus($status) {
        $allowedStatuses = ['draft', 'review', 'approved', 'released'];
        if (in_array($status, $allowedStatuses)) {
            $this->setAttribute('status', $status);
        }
        return $this;
    }
    
    /**
     * 生成发布说明
     */
    public function generateReleaseNotes() {
        $version = $this->getAttribute('version');
        $releaseDate = $this->getAttribute('release_date');
        $description = $this->getAttribute('description');
        $features = $this->getAttribute('features') ?? [];
        $bugFixes = $this->getAttribute('bug_fixes') ?? [];
        $breakingChanges = $this->getAttribute('breaking_changes') ?? [];
        
        $notes = "# Warp2Api Release Notes - v{$version}\n\n";
        
        if ($releaseDate) {
            $notes .= "**Release Date:** " . date('Y-m-d', strtotime($releaseDate)) . "\n\n";
        }
        
        if ($description) {
            $notes .= "## Overview\n{$description}\n\n";
        }
        
        if (!empty($features)) {
            $notes .= "## ✨ New Features\n";
            foreach ($features as $feature) {
                $notes .= "- **{$feature['title']}**: {$feature['description']}\n";
            }
            $notes .= "\n";
        }
        
        if (!empty($bugFixes)) {
            $notes .= "## 🐛 Bug Fixes\n";
            foreach ($bugFixes as $fix) {
                $notes .= "- {$fix['issue']}: {$fix['solution']}\n";
            }
            $notes .= "\n";
        }
        
        if (!empty($breakingChanges)) {
            $notes .= "## ⚠️ Breaking Changes\n";
            foreach ($breakingChanges as $change) {
                $notes .= "- {$change}\n";
            }
            $notes .= "\n";
        }
        
        return $notes;
    }
    
    /**
     * 验证发布表单
     */
    public function validate() {
        $errors = [];
        
        if (empty($this->getAttribute('version'))) {
            $errors[] = 'Version is required';
        }
        
        if (empty($this->getAttribute('description'))) {
            $errors[] = 'Description is required';
        }
        
        $features = $this->getAttribute('features') ?? [];
        if (empty($features)) {
            $errors[] = 'At least one feature is required';
        }
        
        return empty($errors) ? true : $errors;
    }
    
    /**
     * 获取属性值
     */
    public function getAttribute($key) {
        return $this->attributes[$key] ?? null;
    }
    
    /**
     * 设置属性值
     */
    public function setAttribute($key, $value) {
        $this->attributes[$key] = $value;
        return $this;
    }
    
    /**
     * 转换为数组
     */
    public function toArray() {
        return $this->attributes;
    }
    
    /**
     * 转换为JSON
     */
    public function toJson() {
        return json_encode($this->toArray(), JSON_PRETTY_PRINT);
    }
}

// 示例用法
if (basename($_SERVER['PHP_SELF']) == basename(__FILE__)) {
    // 创建发布表单实例
    $releaseSheet = new ReleaseSheet([
        'version' => '2.0.0',
        'description' => 'Major update with dual API compatibility',
        'release_date' => '2025-09-26'
    ]);
    
    // 添加功能
    $releaseSheet->addFeature([
        'title' => 'OpenAI API兼容性',
        'description' => '完全支持OpenAI Chat Completions API格式',
        'type' => 'feature'
    ]);
    
    $releaseSheet->addFeature([
        'title' => 'Claude API兼容性', 
        'description' => '新增Claude Messages API支持',
        'type' => 'feature'
    ]);
    
    $releaseSheet->addFeature([
        'title' => '流式响应优化',
        'description' => '改进SSE流式传输性能',
        'type' => 'enhancement'
    ]);
    
    // 添加bug修复
    $releaseSheet->addBugFix([
        'issue' => 'JWT token刷新问题',
        'solution' => '改进自动token刷新机制',
        'severity' => 'high'
    ]);
    
    $releaseSheet->addBugFix([
        'issue' => '代理连接错误',
        'solution' => '禁用代理设置以避免连接问题',
        'severity' => 'medium'
    ]);
    
    // 设置状态
    $releaseSheet->setStatus('approved');
    
    // 验证和输出
    $validation = $releaseSheet->validate();
    if ($validation === true) {
        echo "✅ 发布表单验证通过\n\n";
        echo $releaseSheet->generateReleaseNotes();
    } else {
        echo "❌ 验证失败:\n";
        foreach ($validation as $error) {
            echo "- {$error}\n";
        }
    }
}
?>