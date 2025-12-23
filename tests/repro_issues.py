import requests
import time
import sys

API_URL = "http://localhost:8000/api"

def create_user(username):
    email = f"{username}@example.com"
    password = "password123"
    try:
        res = requests.post(f"{API_URL}/auth/signup", json={
            "username": username,
            "email": email,
            "password": password
        })
        if res.status_code == 200:
            return res.json()
        # Try login if exists
        res = requests.post(f"{API_URL}/auth/login", json={
            "email": email,
            "password": password
        })
        return res.json()
    except Exception as e:
        print(f"Error creating user {username}: {e}")
        return None

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def run_test():
    print("--- Starting Reproduction Test ---")
    
    # 1. Create Creator
    creator = create_user("creator_test")
    if not creator:
        print("Failed to create creator")
        return
    creator_token = creator["access_token"]
    print("Creator authenticated")

    # 2. Create Meme
    meme_data = {
        "name": "Test IPO Batch",
        "ticker": f"TIB{int(time.time()) % 10000}",
        "description": "Testing IPO batching and listings",
        "image_url": "https://example.com/meme.jpg",
        "category": "other",
        "initial_price": 1.0,
        "total_shares": 1000,
        "ipo_percent": 0.1, # 100 shares IPO
        "ipo_duration_minutes": 60
    }
    res = requests.post(f"{API_URL}/memes/", json=meme_data, headers=get_headers(creator_token))
    if res.status_code != 200:
        print(f"Failed to create meme: {res.text}")
        return
    meme = res.json()
    meme_id = meme["id"]
    print(f"Meme created: {meme['ticker']} ({meme_id})")
    print(f"IPO Price: {meme['ipo_price']}")
    print(f"IPO Shares: {meme['ipo_shares_remaining']}")

    # 3. Test Voting Batching (during IPO)
    print("\n--- Testing Vote Batching ---")
    initial_price = meme["current_price"]
    
    # Vote 1
    res = requests.post(f"{API_URL}/memes/{meme_id}/upvote", headers=get_headers(creator_token))
    meme_after_1 = requests.get(f"{API_URL}/memes/{meme_id}").json()
    print(f"Price after 1 upvote: {meme_after_1['current_price']} (Expected: {initial_price})")
    
    if meme_after_1['current_price'] != initial_price:
        print("❌ FAILURE: Price changed immediately on first vote during IPO!")
    else:
        print("✅ SUCCESS: Price did not change on first vote.")

    # 4. Test Listings (Post-IPO)
    # First, we need to end IPO active state by buying all shares
    print("\n--- Testing Listings ---")
    
    # Create a buyer
    buyer = create_user("buyer_test")
    buyer_token = buyer["access_token"]
    
    # Buy all IPO shares (100)
    # Need money first? The system might not have a faucet, but let's assume new users have 0 balance.
    # Wait, does signup give balance? No.
    # We need to hack balance or use a user with balance.
    # Or we can just check the "Listing" logic by trying to SELL from creator?
    # Creator has 900 shares (90%).
    # But creator cannot sell if IPO is active.
    # So we MUST end IPO active state.
    # To end IPO active state, we must buy all 100 shares.
    # Or wait for time to expire (too long).
    # We need to fund the buyer.
    # There is no endpoint to fund user.
    # I'll use the `creator` who has shares, but they can't sell until IPO ends.
    
    # Let's try to place a BUY order as creator?
    # If IPO is active, BUY is fixed price.
    # We want to test "Listing".
    # Listings only happen in Secondary Market.
    # Secondary Market happens when IPO is NOT active.
    # IPO is active if time < end AND shares > 0.
    
    # I can't easily force IPO to end without DB access or buying.
    # I will use a python script to directly update MongoDB to set ipo_shares_remaining = 0
    # This simulates IPO sellout.
    
    print("Simulating IPO sellout via direct DB update (requires pymongo)...")
    # This part runs inside the python script, so I can use pymongo if installed in the environment I run this script in.
    # But I am running this script via `python3` in the shell. I need to make sure pymongo is available.
    # I'll assume I can use the app's environment.
    
    pass

if __name__ == "__main__":
    run_test()
