EXTRACTOR_REGISTRY = {}

def register_extractor(market_key):
    def decorator(func):
        EXTRACTOR_REGISTRY[market_key.lower()] = func
        return func
    return decorator
