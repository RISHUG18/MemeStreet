import requests
import time

BASE_URL = "http://localhost:8000/api"

def test_portfolio_and_orders():
    # 1. Create a user
    username = f"trader_{int(time.time())}"
    user_data = {"username": username, "email": f"{username}@example.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/signup", json=user_data)
    if resp.status_code not in [200, 201]:
        print(f"Failed to register: {resp.text}")
        return
    
    # Login to get the token
    login_data = {"email": f"{username}@example.com", "password": "password123"}
    resp = requests.post(f"{BASE_URL}/auth/login", json=login_data)
    if resp.status_code != 200:
        print(f"Failed to login: {resp.text}")
        return
    
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"User {username} registered and logged in.")

    # 2. Create a meme to trade
    meme_data = {
        "ticker": f"TS{int(time.time()) % 100000000}",  # Keep ticker short
        "name": "Test Meme",
        "description": "Testing orders",
        "image_url": "http://example.com/image.png",
    }
    # We need to be logged in to create a meme usually, or use the create endpoint
    # Let's try to find an existing meme or create one
    resp = requests.post(f"{BASE_URL}/memes/", json=meme_data, headers=headers)
    if resp.status_code in [200, 201]:
        meme_id = resp.json()["id"]
        print(f"Meme created: {meme_id}")
    else:
        print(f"Failed to create meme: {resp.text}")
        # Try to get an existing meme
        resp = requests.get(f"{BASE_URL}/memes/")
        result = resp.json()
        memes = result.get("memes", []) if isinstance(result, dict) else result
        if not memes:
            print("No memes available to test.")
            return
        meme_id = memes[0]["id"]
        print(f"Using existing meme: {meme_id}")

    # 3. Place a Limit Buy Order (to create an open order)
    # We need to make sure the price is low enough so it doesn't execute immediately if there are sellers,
    # or high enough if we want to buy. But for a new meme, it might be in IPO or just have no liquidity.
    # Let's try to place a limit buy at a low price.
    # The buy endpoint uses query params: meme_id, quantity, max_price
    resp = requests.post(
        f"{BASE_URL}/trading/buy?meme_id={meme_id}&quantity=10&max_price=1.0",
        headers=headers
    )
    if resp.status_code == 200:
        result = resp.json()
        transaction = result.get("transaction", {})
        order_id = transaction.get("id")
        status = transaction.get("status")
        print(f"Order placed: {order_id}, status: {status}")
    else:
        print(f"Failed to place order: {resp.text}")
        return

    # 4. Check Portfolio for Open Orders
    resp = requests.get(f"{BASE_URL}/trading/portfolio", headers=headers)
    if resp.status_code == 200:
        portfolio = resp.json()
        open_orders = portfolio.get("open_orders", [])
        print(f"Open orders found: {len(open_orders)}")
        if open_orders:
            for order in open_orders:
                print(f"  - Order: {order.get('id')}, type={order.get('order_type')}, qty={order.get('quantity')}, price={order.get('price')}")
    else:
        print(f"Failed to fetch portfolio: {resp.text}")

    # 5. If we have an open order, try to cancel it
    if open_orders:
        order_id = open_orders[0]["id"]
        resp = requests.post(f"{BASE_URL}/trading/orders/{order_id}/cancel", headers=headers)
        if resp.status_code == 200:
            print("Order cancelled successfully.")
        else:
            print(f"Failed to cancel order: {resp.text}")

        # 6. Verify it's gone
        resp = requests.get(f"{BASE_URL}/trading/portfolio", headers=headers)
        portfolio = resp.json()
        new_orders = portfolio.get("open_orders", [])
        found = False
        for order in new_orders:
            if order["id"] == order_id:
                found = True
                break
        if not found:
            print("Verified: Order is removed from portfolio.")
        else:
            print("Error: Order still present in portfolio.")
    else:
        print("No open orders to cancel (order may have been filled during IPO).")

if __name__ == "__main__":
    test_portfolio_and_orders()
