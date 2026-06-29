from slowapi import Limiter
from slowapi.util import get_remote_address

# Limitador por IP de origem — instância única compartilhada entre main.py (registro do
# middleware/handler) e os controllers que decoram rotas sensíveis (ex.: /auth/login).
limiter = Limiter(key_func=get_remote_address)
