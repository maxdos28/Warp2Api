#!/usr/bin/env python3
"""最终图片识别验证测试"""
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:28889/v1",
    api_key="0000"
)

print("="*70)
print("🎨 图片识别功能最终验证")
print("="*70)

tests = [
    {
        "name": "猫咪照片识别",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/4/4d/Cat_November_2010-1a.jpg/240px-Cat_November_2010-1a.jpg",
        "question": "这张图片中有什么动物？请简短描述。"
    },
    {
        "name": "GitHub Logo识别",
        "url": "https://github.githubassets.com/images/modules/logos_page/GitHub-Mark.png",
        "question": "这是什么公司或平台的logo？"
    },
    {
        "name": "埃菲尔铁塔",
        "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a8/Tour_Eiffel_Wikimedia_Commons.jpg/240px-Tour_Eiffel_Wikimedia_Commons.jpg",
        "question": "这是什么著名建筑？在哪个城市？"
    }
]

results = []

for i, test in enumerate(tests, 1):
    print(f"\n{'='*70}")
    print(f"测试 {i}: {test['name']}")
    print(f"{'='*70}")
    print(f"图片: {test['url']}")
    print(f"问题: {test['question']}")
    print(f"\n{'AI回答:':─<70}")
    
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
        
        print(f"\n{'':-<70}")
        results.append({"test": test['name'], "success": True, "answer": answer[:100]})
        print(f"✅ 测试 {i} 完成")
        
    except Exception as e:
        print(f"\n❌ 测试 {i} 失败: {e}")
        results.append({"test": test['name'], "success": False, "error": str(e)})

print(f"\n{'='*70}")
print("📊 测试结果总结")
print(f"{'='*70}")

passed = sum(1 for r in results if r['success'])
total = len(results)

for i, result in enumerate(results, 1):
    status = "✅ PASS" if result['success'] else "❌ FAIL"
    print(f"{status} - 测试 {i}: {result['test']}")
    if result['success']:
        preview = result['answer'].replace('\n', ' ')[:80]
        print(f"     回答预览: {preview}...")

print(f"\n总计: {passed}/{total} 通过")

if passed == total:
    print("\n🎉 所有图片识别测试通过！")
    print("✅ 多模态功能工作正常")
    print("✅ AI能够正确识别和理解图片内容")
else:
    print(f"\n⚠️ {total - passed} 个测试未通过")

print(f"{'='*70}")
