import asyncio
import httpx
import os
from collections import Counter

async def fetch_ip(client, i, results):
    try:
        resp = await client.get("https://ipinfo.io/ip", headers={"Connection": "close"}, timeout=10)
        ip = resp.text.strip()
        results.append(ip)
        print(f"Request {i+1}: {ip}")
    except Exception as e:
        print(f"Request {i+1}: ERROR - {e}")

async def main():
    http_proxy = os.environ.get("HTTP_PROXY")
    https_proxy = os.environ.get("HTTPS_PROXY")

    transport = httpx.AsyncHTTPTransport(proxy=http_proxy or https_proxy)

    results = []  # 用于收集所有请求的 IP

    async with httpx.AsyncClient(transport=transport) as client:
        tasks = [fetch_ip(client, i, results) for i in range(300)]  # 100 次请求
        await asyncio.gather(*tasks)

    # 统计 IP 出现次数
    counter = Counter(results)
    print("\n=== Summary ===")
    for ip, count in counter.items():
        print(f"{ip} -> {count} times ({count/len(results)*300:.1f}%)")

    print(f"\nTotal unique IPs: {len(counter)} / {len(results)} requests")

if __name__ == "__main__":
    asyncio.run(main())
