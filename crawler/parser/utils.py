import inspect

from loguru import logger
import ua_generator


def error_handler(f):
    
    def wrapper(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            # logger.exception(e)
            return e
    
    async def wrapper_async(*args, **kwargs):
        try:
            return await f(*args, **kwargs)
        except Exception as e:
            # logger.exception(e)
            return e
    
    if inspect.iscoroutinefunction(f):
        return wrapper_async
    else:
        return wrapper


def append_ua_to_headers(headers: dict = {}):
    for k, v in ua_generator.generate().headers.get().items():
        headers[k] = v
        
    return headers
