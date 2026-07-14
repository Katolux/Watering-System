import os
import requests


BASE_URL = "https://perenual.com/api"
API_KEY = os.getenv("PERENUAL_API_KEY")


def test_perenual_search(query: str):
    if not API_KEY:
        raise RuntimeError("Missing PERENUAL_API_KEY")

    url = f"{BASE_URL}/species-list"
    params = {
        "key": API_KEY,
        "q": query,
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(
            f"API request failed: {response.status_code} - {response.text}"
        )

    data = response.json()

    plants = data.get("data", [])
    print(f"\nFound {len(plants)} plants for '{query}':\n")

    for plant in plants[:5]:  # show only first 5
        print("-" * 40)
        print(f"ID: {plant.get('id')}")
        print(f"Common name: {plant.get('common_name')}")
        print(f"Scientific name: {plant.get('scientific_name')}")
        print(f"Cycle: {plant.get('cycle')}")
        print(f"Watering: {plant.get('watering')}")
        print(f"Sunlight: {plant.get('sunlight')}")


if __name__ == "__main__":
    test_perenual_search("tomato")
