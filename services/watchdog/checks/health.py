"""
HTTP Health Check для API endpoints
"""
import urllib.request
import urllib.error
from typing import Dict, Tuple
import json


def check_health_endpoint(url: str, timeout: int = 10) -> Tuple[bool, int, str]:
    """
    Проверяет HTTP endpoint
    Returns: (is_healthy, status_code, message)
    """
    try:
        request = urllib.request.Request(url, method='GET')
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status_code = response.getcode()
            body = response.read().decode('utf-8')
            is_healthy = status_code == 200
            return is_healthy, status_code, body[:200]
    except urllib.error.HTTPError as e:
        return False, e.code, str(e.reason)
    except urllib.error.URLError as e:
        return False, 0, f"Connection failed: {e.reason}"
    except TimeoutError:
        return False, 0, "Timeout"
    except Exception as e:
        return False, 0, f"Error: {str(e)}"


def check_all_endpoints(endpoints: Dict[str, str]) -> Dict[str, dict]:
    """
    Проверяет все endpoints
    Returns: {name: {"healthy": bool, "status_code": int, "message": str}}
    """
    results = {}
    for name, url in endpoints.items():
        is_healthy, status_code, message = check_health_endpoint(url)
        results[name] = {
            "healthy": is_healthy,
            "status_code": status_code,
            "message": message,
            "url": url
        }
    return results


if __name__ == "__main__":
    # Тест
    endpoints = {
        "prod": "http://localhost:8000/health",
        "dev": "http://localhost:8002/health",
    }
    results = check_all_endpoints(endpoints)
    for name, data in results.items():
        emoji = "✅" if data["healthy"] else "❌"
        print(f"{emoji} {name}: {data['status_code']} - {data['message'][:50]}")
