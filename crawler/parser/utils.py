import inspect
import random
import string

import envyaml
from loguru import logger
import ua_generator


def error_handler(f):
    
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return e
    
    async def wrapper_async(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            logger.exception(e)
            return e
    
    if inspect.iscoroutinefunction(f):
        return wrapper_async
    else:
        return wrapper


def append_ua_to_headers(headers: dict = {}):
    for k, v in ua_generator.generate().headers.get().items():
        headers[k] = v
        
    return headers


def get_cfg():
    return envyaml.EnvYAML(yaml_file="config.yml", env_file='.env', include_environment=False, flatten=False)


def get_proxy_iproyal(country: str = None, session_seconds: int = None):
    cfg = get_cfg()["proxy"]["iproyal"]
    username, password = cfg["username"], cfg["password"]
    
    addons = ''
    if country:
        addons += f"_country-{country}"
    if session_seconds:
        sessioname = "".join(random.choices(string.ascii_letters + string.ascii_lowercase + string.ascii_uppercase, k=8))
        addons += f'_session-{sessioname}_lifetime-{session_seconds}s'
    
    url = f"http://{username}:{password}{addons}@{cfg["host"]}:{cfg["port"]}"
    return url

