#!/usr/bin/env python3
"""
创建明确标识的测试图片
"""
import base64

def create_distinct_test_images():
    """创建几个不同的明确标识的测试图片"""
    
    # 1. 纯蓝色方块 (更大的图片)
    blue_square = create_colored_square('blue')
    
    # 2. 纯绿色方块
    green_square = create_colored_square('green')
    
    # 3. 黑白棋盘格
    checkerboard = create_checkerboard()
    
    return {
        'blue_square': blue_square,
        'green_square': green_square, 
        'checkerboard': checkerboard
    }

def create_colored_square(color):
    """创建纯色方块的PNG数据"""
    if color == 'blue':
        # 蓝色像素的PNG数据 (手工制作的最小PNG)
        # 这是一个2x2的蓝色正方形
        png_hex = (
            "89504e470d0a1a0a0000000d49484452000000020000000208060000007b"
            "cf7db80000001049444154789c6300010000050005015a2f59b30000000049"
            "454e44ae426082"
        )
        return base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')
    
    elif color == 'green':
        # 绿色像素的PNG数据
        png_hex = (
            "89504e470d0a1a0a0000000d49484452000000020000000208060000007b"
            "cf7db80000001049444154789c630001000005000501ff2f59b30000000049"
            "454e44ae426082"
        )
        return base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')
    
    # 默认返回红色
    return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=="

def create_checkerboard():
    """创建黑白棋盘格图案"""
    # 这是一个4x4的黑白棋盘格PNG
    png_hex = (
        "89504e470d0a1a0a0000000d49484452000000040000000408060000000c"
        "a346310000002049444154789c6300008080ff81ffffff00008080ff8100"
        "00ffffff008080ff810000ff000000494e44ae426082"
    )
    return base64.b64encode(bytes.fromhex(png_hex)).decode('utf-8')

def print_image_info(name, base64_data):
    """打印图片信息"""
    import hashlib
    raw_data = base64.b64decode(base64_data)
    print(f"{name}:")
    print(f"  Base64长度: {len(base64_data)}")
    print(f"  原始字节数: {len(raw_data)}")
    print(f"  MD5哈希: {hashlib.md5(raw_data).hexdigest()}")
    print()

if __name__ == "__main__":
    images = create_distinct_test_images()
    
    print("创建的测试图片信息:")
    print("="*50)
    
    for name, data in images.items():
        print_image_info(name, data)
    
    # 保存到文件供其他脚本使用
    import json
    with open('test_images.json', 'w') as f:
        json.dump(images, f)
    
    print("测试图片已保存到 test_images.json")
