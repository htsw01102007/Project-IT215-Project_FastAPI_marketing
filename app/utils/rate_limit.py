from collections import defaultdict
from datetime import datetime, timedelta

# Bộ nhớ tạm để lưu lượt thử đăng nhập thất bại
_failed_attempts = defaultdict(list)

def check_login_rate_limit(key: str, max_attempts: int = 5, window_seconds: int = 300) -> bool:
    now = datetime.now()
    cutoff = now - timedelta(seconds=window_seconds)
    
    # Lọc bỏ các lần thử đã quá cửa sổ thời gian
    _failed_attempts[key] = [t for t in _failed_attempts[key] if t > cutoff]
    
    if len(_failed_attempts[key]) >= max_attempts:
        return False
        
    return True

def record_failed_attempt(key: str):
    _failed_attempts[key].append(datetime.now())