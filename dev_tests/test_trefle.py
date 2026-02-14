import os
import requests
import json

print("PYTHON SEES:", os.environ.get("TREFLE_API_KEY"))

BASE_URL = "https://trefle.io/api/v1"
API_KEY = os.getenv("usr-Nmg_DjNbByPs1CnLW7VIV_eFW5q3Lej86O1Kt7-wefU")


def test_trefle_search(query: str):
    if not API_KEY:
        raise RuntimeError("Missing TREFLE_API_KEY")

    url = f"{BASE_URL}/plants/search"
    params = {
        "q": query,
        "token": API_KEY,
    }

    response = requests.get(url, params=params, timeout=15)

    if response.status_code != 200:
        raise RuntimeError(
            f"API request failed: {response.status_code} - {response.text}"
        )

    data = response.json()

    print("\n--- RAW RESPONSE STRUCTURE ---")
    print(json.dumps(data, indent=2))

    plants = data.get("data", [])

    if plants:
        print("\n--- FIRST PLANT ENTRY ONLY ---")
        print(json.dumps(plants[0], indent=2))


if __name__ == "__main__":
    test_trefle_search("tomato")

