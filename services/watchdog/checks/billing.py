"""
Проверка балансов: OpenAI, Timeweb
"""
import urllib.request
import urllib.error
import json
import os
from typing import Dict, Tuple


def check_timeweb_balance(api_token: str) -> Tuple[bool, float, str]:
    """
    Проверяет баланс Timeweb
    Returns: (success, balance_rub, message)
    """
    if not api_token:
        return False, 0, "TIMEWEB_API_TOKEN not set"
    
    try:
        url = "https://api.timeweb.cloud/api/v1/account/finances"
        request = urllib.request.Request(url)
        request.add_header("Authorization", f"Bearer {api_token}")
        
        with urllib.request.urlopen(request, timeout=15) as response:
            data = json.loads(response.read().decode('utf-8'))
            balance = float(data.get('finances', {}).get('balance', 0))
            return True, balance, "OK"
    except urllib.error.HTTPError as e:
        return False, 0, f"HTTP {e.code}: {e.reason}"
    except Exception as e:
        return False, 0, f"Error: {str(e)}"


def check_openai_balance() -> Tuple[bool, float, str]:
    """
    Информация о балансе OpenAI
    OpenAI prepaid - проверка через dashboard, не через API
    Returns: (success, balance_usd, message)
    """
    # OpenAI не предоставляет API для проверки prepaid баланса
    # Возвращаем заглушку - баланс нужно проверять вручную
    return True, -1, "Prepaid account - check dashboard manually"


def check_all_billing(timeweb_token: str = None) -> Dict[str, dict]:
    """
    Проверяет все балансы
    """
    # Timeweb
    tw_success, tw_balance, tw_msg = check_timeweb_balance(
        timeweb_token or os.getenv("TIMEWEB_API_TOKEN", "")
    )
    
    # OpenAI
    oa_success, oa_balance, oa_msg = check_openai_balance()
    
    return {
        "timeweb": {
            "success": tw_success,
            "balance": tw_balance,
            "currency": "RUB",
            "message": tw_msg
        },
        "openai": {
            "success": oa_success,
            "balance": oa_balance,
            "currency": "USD",
            "message": oa_msg
        }
    }


if __name__ == "__main__":
    # Тест
    token = os.getenv("TIMEWEB_API_TOKEN", "")
    results = check_all_billing(token)
    
    tw = results["timeweb"]
    if tw["success"]:
        print(f"Timeweb: {tw['balance']:.2f} ₽")
    else:
        print(f"Timeweb: ❌ {tw['message']}")
    
    oa = results["openai"]
    print(f"OpenAI: {oa['message']}")
