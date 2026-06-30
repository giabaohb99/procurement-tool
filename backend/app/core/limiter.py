from slowapi import Limiter
from slowapi.util import get_remote_address

# Giới hạn tần suất theo IP (in-memory, đủ cho quy mô nhỏ)
limiter = Limiter(key_func=get_remote_address, default_limits=["300/minute"])
