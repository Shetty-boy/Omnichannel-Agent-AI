from recommendation_agent import get_recommendations

print("---- CATEGORY TEST ----")
print(get_recommendations(category="smartphone"))

print("\n---- TEXT TEST ----")
print(get_recommendations(query="phone"))
