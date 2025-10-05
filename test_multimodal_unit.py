#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多模态功能单元测试

测试图片处理逻辑，不需要启动完整服务器
"""

import sys
import asyncio
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))

def test_image_utils():
    """测试图片工具函数"""
    print("\n" + "="*60)
    print("测试 1: 图片工具函数")
    print("="*60)
    
    from protobuf2openai.image_utils import (
        is_base64_image,
        is_image_url,
        extract_base64_data,
        validate_image_data,
        encode_image_to_base64
    )
    
    # 测试 1.1: is_base64_image
    print("\n1.1 测试 is_base64_image()")
    data_url = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    assert is_base64_image(data_url) == True
    print("  ✅ Data URL 识别正确")
    
    pure_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    assert is_base64_image(pure_base64) == True
    print("  ✅ 纯 Base64 识别正确")
    
    # 测试 1.2: is_image_url
    print("\n1.2 测试 is_image_url()")
    assert is_image_url("https://example.com/image.jpg") == True
    assert is_image_url("http://example.com/photo.png") == True
    assert is_image_url("https://example.com/page.html") == False
    print("  ✅ URL 识别正确")
    
    # 测试 1.3: extract_base64_data
    print("\n1.3 测试 extract_base64_data()")
    mime, data = extract_base64_data(data_url)
    assert mime == "image/png"
    assert data is not None
    assert len(data) > 0
    print(f"  ✅ 提取成功: MIME={mime}, 大小={len(data)} bytes")
    
    # 测试 1.4: validate_image_data
    print("\n1.4 测试 validate_image_data()")
    is_valid, error = validate_image_data(data, mime)
    assert is_valid == True
    assert error is None
    print("  ✅ 图片数据验证通过")
    
    # 测试 1.5: encode_image_to_base64
    print("\n1.5 测试 encode_image_to_base64()")
    encoded = encode_image_to_base64(data, mime)
    assert encoded.startswith("data:image/png;base64,")
    print("  ✅ 图片编码成功")
    
    print("\n✅ 测试 1 完成\n")
    return True


def test_helpers():
    """测试辅助函数"""
    print("="*60)
    print("测试 2: 辅助函数")
    print("="*60)
    
    from protobuf2openai.helpers import (
        normalize_content_to_list,
        has_images,
        extract_images,
        segments_to_text
    )
    
    # 测试 2.1: 纯文本
    print("\n2.1 测试纯文本处理")
    content = "Hello, world!"
    segments = normalize_content_to_list(content)
    assert len(segments) == 1
    assert segments[0]["type"] == "text"
    assert segments[0]["text"] == "Hello, world!"
    print("  ✅ 纯文本处理正确")
    
    # 测试 2.2: 文本 + 图片
    print("\n2.2 测试文本+图片处理")
    content = [
        {"type": "text", "text": "这是一张图片："},
        {"type": "image_url", "image_url": {"url": "https://example.com/image.jpg"}}
    ]
    segments = normalize_content_to_list(content)
    assert len(segments) == 2
    assert segments[0]["type"] == "text"
    assert segments[1]["type"] == "image_url"
    print("  ✅ 文本+图片处理正确")
    
    # 测试 2.3: has_images
    print("\n2.3 测试 has_images()")
    assert has_images(segments) == True
    text_only = normalize_content_to_list("只有文本")
    assert has_images(text_only) == False
    print("  ✅ has_images() 正确")
    
    # 测试 2.4: extract_images
    print("\n2.4 测试 extract_images()")
    images = extract_images(segments)
    assert len(images) == 1
    assert images[0]["type"] == "image_url"
    print("  ✅ extract_images() 正确")
    
    # 测试 2.5: segments_to_text
    print("\n2.5 测试 segments_to_text()")
    text = segments_to_text(segments)
    assert text == "这是一张图片："
    print("  ✅ segments_to_text() 正确")
    
    print("\n✅ 测试 2 完成\n")
    return True


def test_multimodal_config():
    """测试配置"""
    print("="*60)
    print("测试 3: 多模态配置")
    print("="*60)
    
    from protobuf2openai.multimodal_config import config
    
    print("\n3.1 配置参数：")
    print(f"  - 多模态启用: {config.is_multimodal_enabled()}")
    print(f"  - 图片下载启用: {config.can_download_images()}")
    print(f"  - 最大图片大小: {config.MAX_IMAGE_SIZE_MB} MB")
    print(f"  - 下载超时: {config.IMAGE_DOWNLOAD_TIMEOUT} 秒")
    print(f"  - 支持格式: {len(config.SUPPORTED_IMAGE_FORMATS)} 种")
    
    print("\n3.2 配置摘要：")
    summary = config.get_config_summary()
    for key, value in summary.items():
        print(f"  - {key}: {value}")
    
    print("\n✅ 测试 3 完成\n")
    return True


async def test_image_processing():
    """测试图片处理异步函数"""
    print("="*60)
    print("测试 4: 图片处理函数")
    print("="*60)
    
    from protobuf2openai.image_utils import process_image_url
    
    # 测试 Base64 图片
    print("\n4.1 测试 Base64 图片处理")
    tiny_image = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
    result, error = await process_image_url({"url": tiny_image})
    
    if error:
        print(f"  ❌ 错误: {error}")
        return False
    else:
        print(f"  ✅ 处理成功，大小: {len(result)} 字符")
        assert result.startswith("data:image/png;base64,")
    
    print("\n✅ 测试 4 完成\n")
    return True


def main():
    """运行所有单元测试"""
    print("="*60)
    print("Warp2Api 多模态功能单元测试")
    print("="*60)
    print("\n这些测试验证代码逻辑，不需要启动服务器\n")
    
    results = []
    
    try:
        # 测试 1: 图片工具
        results.append(("图片工具测试", test_image_utils()))
        
        # 测试 2: 辅助函数
        results.append(("辅助函数测试", test_helpers()))
        
        # 测试 3: 配置
        results.append(("配置测试", test_multimodal_config()))
        
        # 测试 4: 异步图片处理
        result4 = asyncio.run(test_image_processing())
        results.append(("图片处理测试", result4))
        
    except Exception as e:
        print(f"\n❌ 测试过程中出错: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # 汇总结果
    print("="*60)
    print("测试结果汇总")
    print("="*60)
    
    passed = 0
    failed = 0
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\n总计: {passed} 通过, {failed} 失败")
    
    if failed == 0:
        print("\n🎉 所有单元测试通过！")
        print("\n📝 代码功能验证完成：")
        print("  ✅ 图片URL识别和验证")
        print("  ✅ Base64编码/解码")
        print("  ✅ 图片格式验证")
        print("  ✅ 内容解析（文本+图片）")
        print("  ✅ 图片提取和处理")
        print("  ✅ 配置管理")
        print("\n多模态支持功能已成功实现！")
        return 0
    else:
        print(f"\n⚠️ {failed} 个测试失败")
        return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️ 测试被用户中断")
        sys.exit(130)
