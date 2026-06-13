from tools import search_listings, suggest_outfit, create_fit_card
from utils.data_loader import get_example_wardrobe

item = search_listings("vintage graphic tee", size=None, max_price=50)[0]
outfit = suggest_outfit(item, get_example_wardrobe())

print("=== 测试 1：正常生成 ===")
card1 = create_fit_card(outfit, item)
print(card1)

print("\n=== 测试 2：再生成一次（内容应该不同）===")
card2 = create_fit_card(outfit, item)
print(card2)

print("\n=== 测试 3：空 outfit guard ===")
card3 = create_fit_card("", item)
print(card3)
print(f"Guard 触发正确: {'Cannot create fit card' in card3}")