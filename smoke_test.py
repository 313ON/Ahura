import os
import sys
from pathlib import Path
from ahura.openrouter_client import OpenRouterClient
from ahura.model_router import AhuraModelRouter
from ahura.router_config import load_profiles_from_file

def run_smoke_test():
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        print("[-] ERROR: OPENROUTER_API_KEY environment variable not set.")
        sys.exit(1)

    print("[+] Initializing Clients...")
    client = OpenRouterClient(api_key=api_key, app_title="ForgeOS-SmokeTest")
    
    # 1. Test Key Limits
    try:
        print("[+] Testing API Authentication & Limits...")
        limits = client.get_key_limits()
        print(f"    [OK] Key Label: {limits.label}")
        print(f"    [OK] Remaining Credits: {limits.limit_remaining}")
    except Exception as e:
        print(f"    [!] Auth Test Failed: {e}")
        return

    # 2. Test Model Router
    try:
        print("[+] Initializing Router with ahura_router.json...")
        profiles = load_profiles_from_file(Path("ahura_router.json"))
        router = AhuraModelRouter(client, profiles)
        print("    [OK] Router ready.")
    except Exception as e:
        print(f"    [!] Router Init Failed: {e}")
        return

    # 3. Test Actual Request (Default Profile)
    try:
        print("[+] Running Chat Completion test (Default Profile)...")
        messages = [{"role": "user", "content": "Hello, ForgeOS!"}]
        result = router.route_chat(messages, profile_name="default")
        print(f"    [OK] Model used: {result.model_used}")
        if result.ok:
            print(f"    [OK] Response: {result.text[:50]}...")
        else:
            print(f"    [FAIL] {result.error_type}: {result.message}")
            return 1
    except Exception as e:
        print(f"    [!] Chat Test Failed: {e}")
        return

    print("\n[***] SMOKE TEST PASSED SUCCESSFULLY [***]")

if __name__ == "__main__":
    run_smoke_test()
