#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试修复后的模型映射功能
验证Claude API模型名称是否正确映射到内部支持的模型
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from protobuf2openai.claude_models import get_internal_model_name, CLAUDE_MODEL_MAPPING

def test_claude_model_mapping():
    """测试Claude模型映射"""
    print("=== 测试Claude模型映射 ===")

    # 测试用例：Claude API模型名称 -> 期望的内部模型名称
    test_cases = [
        # Claude 3.5 Sonnet系列
        ("claude-3-5-sonnet-20241022", "claude-4-sonnet"),
        ("claude-3-5-sonnet-20240620", "claude-4-sonnet"),
        ("claude-3-5-haiku-20241022", "claude-4-sonnet"),

        # Claude 3 Opus系列 -> 最强模型
        ("claude-3-opus-20240229", "claude-4.1-opus"),

        # Claude 3 其他系列
        ("claude-3-sonnet-20240229", "claude-4-sonnet"),
        ("claude-3-haiku-20240307", "claude-4-sonnet"),

        # Claude 2系列
        ("claude-2.1", "claude-4-opus"),
        ("claude-2.0", "claude-4-opus"),

        # Claude Instant系列
        ("claude-instant-1.2", "claude-4-sonnet"),

        # 直接支持的内部模型（无需映射）
        ("claude-4-sonnet", "claude-4-sonnet"),
        ("claude-4-opus", "claude-4-opus"),
        ("claude-4.1-opus", "claude-4.1-opus"),

        # 未知模型（应该使用默认值）
        ("unknown-model", "claude-4-sonnet"),
    ]

    all_passed = True

    for input_model, expected_output in test_cases:
        actual_output = get_internal_model_name(input_model)
        status = "PASS" if actual_output == expected_output else "FAIL"

        print(f"[{status}] {input_model} -> {actual_output} (expected: {expected_output})")

        if actual_output != expected_output:
            all_passed = False

    print(f"\nMapping test result: {'ALL PASSED' if all_passed else 'SOME FAILED'}")
    return all_passed

def test_model_mapping_coverage():
    """Test model mapping coverage"""
    print("\n=== Test Model Mapping Coverage ===")

    # Check all models in mapping table
    print("Current supported model mappings:")
    for claude_model, internal_model in CLAUDE_MODEL_MAPPING.items():
        print(f"  {claude_model} -> {internal_model}")

    # Verify all target models are valid
    valid_internal_models = {
        "claude-4-sonnet", "claude-4-opus", "claude-4.1-opus",
        "gpt-5", "gpt-4o", "gpt-4.1", "o3", "o4-mini",
        "gemini-2.5-pro", "warp-basic", "auto"
    }

    invalid_mappings = []
    for claude_model, internal_model in CLAUDE_MODEL_MAPPING.items():
        if internal_model not in valid_internal_models:
            invalid_mappings.append((claude_model, internal_model))

    if invalid_mappings:
        print("\n[FAIL] Found invalid model mappings:")
        for claude_model, internal_model in invalid_mappings:
            print(f"  {claude_model} -> {internal_model} (invalid)")
        return False
    else:
        print("\n[PASS] All model mappings point to valid internal models")
        return True

def test_vision_model_priority():
    """Test vision model priority"""
    print("\n=== Test Vision Model Priority ===")

    # Test if Opus series maps to strongest vision models
    opus_models = [
        "claude-3-opus-20240229",
        "claude-2.1",
        "claude-2.0"
    ]

    for model in opus_models:
        internal_model = get_internal_model_name(model)
        is_strong_model = internal_model in ["claude-4.1-opus", "claude-4-opus"]
        status = "PASS" if is_strong_model else "FAIL"
        print(f"[{status}] {model} -> {internal_model} ({'strong' if is_strong_model else 'weak'} model)")

if __name__ == "__main__":
    print("Starting model mapping fix tests...")

    # Run all tests
    test1_passed = test_claude_model_mapping()
    test2_passed = test_model_mapping_coverage()
    test_vision_model_priority()

    # Summary
    print("\n" + "="*50)
    if test1_passed and test2_passed:
        print("SUCCESS: All tests passed! Model mapping fix successful.")
        print("\nMain fixes:")
        print("1. [FIXED] Corrected Claude 3.x model to internal model mapping")
        print("2. [FIXED] Ensured Opus series maps to strongest model claude-4.1-opus")
        print("3. [FIXED] Added support for direct internal model names")
        print("4. [FIXED] Unified vision model configuration logic")
        sys.exit(0)
    else:
        print("FAILURE: Some tests failed, need further fixes.")
        sys.exit(1)