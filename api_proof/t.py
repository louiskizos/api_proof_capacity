import requests
import json

def test_render_api():
    """Tester l'API sur Render.com"""
    
    BASE_URL = "https://api-proof-capacity.onrender.com"
    TOKEN = "5cd88561a131df7d7469f4c3ec11f40cc8b58a47"
  
    print("🌐 Test de l'API sur Render.com")
    print("="*50)
    
    # 1. Tester le login d'abord
    print("\n1. 🔐 Test de connexion...")
    
    login_data = {
        "email": "admin@example.com",
        "password": "Admint1234"
    }
    
    try:
        login_response = requests.post(
            f"{BASE_URL}/auth/login/",
            json=login_data,
            timeout=10
        )
        
        print(f"Login status: {login_response.status_code}")
        if login_response.status_code == 200:
            print("✅ Login réussi")
            data = login_response.json()
            print(f"Token: {data.get('token', 'N/A')[:20]}...")
            print(f"User: {data.get('user', {}).get('email', 'N/A')}")
        else:
            print(f"Login échoué: {login_response.text[:100]}")
            
    except Exception as e:
        print(f"❌ Erreur login: {e}")
    
    # 2. Tester la création de wallet (URL connue)
    print("\n2. 💼 Test création wallet...")
    
    wallet_data = {"name": "Test Render Wallet"}
    headers = {
        'Authorization': f'Token {TOKEN}',
        'Content-Type': 'application/json'
    }
    
    try:
        wallet_response = requests.post(
            f"{BASE_URL}/wallets/create/",
            json=wallet_data,
            headers=headers,
            timeout=10
        )
        
        print(f"Create wallet status: {wallet_response.status_code}")
        if wallet_response.status_code == 201:
            print("✅ Wallet créé")
            wallet_info = wallet_response.json()
            print(f"ID: {wallet_info.get('wallet', {}).get('id', 'N/A')}")
            print(f"Adresse: {wallet_info.get('wallet', {}).get('payment_address', 'N/A')[:30]}...")
        else:
            print(f"Create wallet échoué: {wallet_response.text[:200]}")
            
    except Exception as e:
        print(f"❌ Erreur création wallet: {e}")
    
    # 3. Essayer différentes URLs pour les wallets
    print("\n3. 🔍 Recherche de l'URL des wallets...")
    
    possible_urls = [
        "/wallets/",  # Peut-être une liste générale
        "/auth/wallets/",  # Vu dans la liste
        "/api/wallets/",  # Pattern commun
        "/user/wallets/",  # Celle qu'on cherchait
        "/wallets/user/",  # Autre possibilité
    ]
    
    for url in possible_urls:
        full_url = f"{BASE_URL}{url}"
        print(f"\n   Essai: {url}")
        
        try:
            response = requests.get(full_url, headers=headers, timeout=5)
            print(f"   Status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"   ✅ TROUVÉ! {url}")
                data = response.json()
                print(f"   Nombre de wallets: {data.get('count', len(data.get('wallets', [])))}")
                break
            elif response.status_code == 404:
                print(f"   ❌ 404 - Non trouvé")
            else:
                print(f"   ⚠️  {response.status_code}: {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")
    
    # 4. Tester d'autres endpoints connus
    print("\n4. 📡 Test d'autres endpoints...")
    
    endpoints = [
        ("/auth/profile/", "GET"),  # Profil utilisateur
        ("/wallets/network/info/", "GET"),  # Info réseau
        ("/api/transactions/", "GET"),  # Transactions
    ]
    
    for endpoint, method in endpoints:
        full_url = f"{BASE_URL}{endpoint}"
        print(f"\n   {method} {endpoint}")
        
        try:
            if method == "GET":
                response = requests.get(full_url, headers=headers, timeout=5)
            else:
                response = requests.post(full_url, headers=headers, timeout=5)
            
            print(f"   Status: {response.status_code}")
            if response.status_code == 200:
                print(f"   ✅ Fonctionne")
                try:
                    data = response.json()
                    print(f"   Données: {json.dumps(data)[:100]}...")
                except:
                    print(f"   Réponse: {response.text[:100]}")
            else:
                print(f"   ❌ {response.text[:100]}")
                
        except Exception as e:
            print(f"   ❌ Erreur: {e}")

if __name__ == "__main__":
    test_render_api()