from tools import search_listings, suggest_outfit
from utils.data_loader import get_example_wardrobe, get_empty_wardrobe

# 先拿一个真实的 listing
item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
print(f"测试用 item: {item['title']}\n")

print("=== 测试 1：有衣橱 ===")
result1 = suggest_outfit(item, get_example_wardrobe())
print(result1)
print(f"\n返回类型: {type(result1)}, 非空: {bool(result1)}")

print("\n=== 测试 2：空衣橱 ===")
result2 = suggest_outfit(item, get_empty_wardrobe())
print(result2)
print(f"\n返回类型: {type(result2)}, 非空: {bool(result2)}")