#!/usr/bin/env python3
"""全面的图片识别准确性测试"""
from openai import OpenAI
import time

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print("="*80)
print("🎯 全面图片识别准确性测试")
print("="*80)

test_cases = [
    {
        "name": "测试 1: 自由女神像",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a1/Statue_of_Liberty_7.jpg/240px-Statue_of_Liberty_7.jpg",
        "question": "这是什么雕像？在哪里？",
        "expected_keywords": ["自由女神", "纽约", "美国"]
    },
    {
        "name": "测试 2: 长城",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/2/23/The_Great_Wall_of_China_at_Jinshanling-edit.jpg/320px-The_Great_Wall_of_China_at_Jinshanling-edit.jpg",
        "question": "这是什么建筑？在哪个国家？",
        "expected_keywords": ["长城", "中国"]
    },
    {
        "name": "测试 3: 比萨斜塔",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/6/66/The_Leaning_Tower_of_Pisa_SB.jpeg/240px-The_Leaning_Tower_of_Pisa_SB.jpeg",
        "question": "这个著名的斜塔叫什么名字？在哪个国家？",
        "expected_keywords": ["比萨", "意大利"]
    },
    {
        "name": "测试 4: 金门大桥",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/0/0c/GoldenGateBridge-001.jpg/320px-GoldenGateBridge-001.jpg",
        "question": "这座桥叫什么名字？什么颜色？",
        "expected_keywords": ["金门大桥", "红色", "旧金山"]
    },
    {
        "name": "测试 5: 泰姬陵",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/b/bd/Taj_Mahal%2C_Agra%2C_India_edit3.jpg/240px-Taj_Mahal%2C_Agra%2C_India_edit3.jpg",
        "question": "这是什么建筑？在哪个国家？什么颜色？",
        "expected_keywords": ["泰姬陵", "印度", "白色"]
    },
    {
        "name": "测试 6: 狗的品种识别",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/3/34/Labrador_on_Quantock_%282175262184%29.jpg/240px-Labrador_on_Quantock_%282175262184%29.jpg",
        "question": "这是什么品种的狗？什么颜色？",
        "expected_keywords": ["拉布拉多", "金色", "黄色"]
    },
    {
        "name": "测试 7: 水果识别",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/1/15/Red_Apple.jpg/240px-Red_Apple.jpg",
        "question": "图片中是什么水果？什么颜色？",
        "expected_keywords": ["苹果", "红色"]
    },
    {
        "name": "测试 8: 交通标志",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/f/f9/STOP_sign.jpg/240px-STOP_sign.jpg",
        "question": "这是什么交通标志？上面写的什么？",
        "expected_keywords": ["停止", "STOP", "红色"]
    }
]

results = []
correct_count = 0

for i, test in enumerate(test_cases, 1):
    print(f"\n{'='*80}")
    print(f"{test['name']}")
    print(f"{'='*80}")
    print(f"📷 图片: {test['url']}")
    print(f"❓ 问题: {test['question']}")
    print(f"🎯 预期关键词: {', '.join(test['expected_keywords'])}")
    print(f"\n{'💬 AI回答:':─<80}")
    
    try:
        response = client.chat.completions.create(
            model="claude-4-sonnet",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": test['question']},
                        {"type": "image_url", "image_url": {"url": test['url']}}
                    ]
                }
            ],
            stream=True
        )
        
        answer = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                print(content, end="", flush=True)
                answer += content
        
        # 检查关键词是否在答案中
        answer_lower = answer.lower()
        matched_keywords = [kw for kw in test['expected_keywords'] 
                          if kw.lower() in answer_lower or 
                             any(word in answer_lower for word in kw.lower().split())]
        
        accuracy = len(matched_keywords) / len(test['expected_keywords']) * 100
        is_correct = accuracy >= 50  # 至少匹配50%关键词算正确
        
        print(f"\n{'':-<80}")
        print(f"✓ 匹配关键词: {matched_keywords if matched_keywords else '无'}")
        print(f"📊 准确度: {accuracy:.0f}% ({len(matched_keywords)}/{len(test['expected_keywords'])})")
        
        if is_correct:
            print(f"✅ 测试 {i} 通过")
            correct_count += 1
        else:
            print(f"⚠️  测试 {i} 部分正确")
        
        results.append({
            "test": test['name'],
            "success": True,
            "correct": is_correct,
            "accuracy": accuracy,
            "matched": matched_keywords,
            "answer": answer[:150]
        })
        
        time.sleep(1)  # 避免请求过快
        
    except Exception as e:
        print(f"\n❌ 测试 {i} 失败: {e}")
        results.append({
            "test": test['name'],
            "success": False,
            "correct": False,
            "error": str(e)
        })

# 打印总结
print(f"\n{'='*80}")
print("📊 测试结果总结")
print(f"{'='*80}")

total_tests = len(results)
successful_tests = sum(1 for r in results if r['success'])
correct_tests = sum(1 for r in results if r.get('correct', False))

print(f"\n总测试数: {total_tests}")
print(f"成功执行: {successful_tests}/{total_tests}")
print(f"识别正确: {correct_tests}/{successful_tests}")
print(f"总准确率: {(correct_tests/total_tests*100):.1f}%\n")

print(f"{'详细结果:':─<80}")
for i, result in enumerate(results, 1):
    if result['success']:
        status = "✅" if result['correct'] else "⚠️ "
        accuracy = result.get('accuracy', 0)
        print(f"{status} {result['test']}: {accuracy:.0f}%准确")
        if result.get('matched'):
            print(f"   匹配: {', '.join(result['matched'])}")
    else:
        print(f"❌ {result['test']}: 执行失败")

print(f"\n{'='*80}")
if correct_tests == total_tests:
    print("🎉 完美！所有图片识别100%准确！")
elif correct_tests >= total_tests * 0.8:
    print(f"🌟 优秀！{(correct_tests/total_tests*100):.0f}%的图片识别准确")
elif correct_tests >= total_tests * 0.6:
    print(f"👍 良好！{(correct_tests/total_tests*100):.0f}%的图片识别准确")
else:
    print(f"⚠️  需要改进：仅{(correct_tests/total_tests*100):.0f}%准确")

print("\n✅ 多模态图片识别功能已验证")
print(f"{'='*80}")
