from tools import search_listings

print("=== 测试 1：正常搜索 ===")
results = search_listings("vintage graphic tee", size=None, max_price=50)
print(f"找到 {len(results)} 条结果")
if results:
    print(f"Top result: {results[0]['title']} — ${results[0]['price']}")

print("\n=== 测试 2：无结果路径 ===")
results2 = search_listings("designer ballgown", size="XXS", max_price=5)
print(f"结果: {results2}")  # 期望: []

print("\n=== 测试 3：价格过滤 ===")
results3 = search_listings("jacket", size=None, max_price=30)
prices = [r["price"] for r in results3]
print(f"所有价格: {prices}")  # 期望全部 ≤ 30
print(f"价格过滤正确: {all(p <= 30 for p in prices)}")