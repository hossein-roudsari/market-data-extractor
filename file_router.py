# import extractors.southland_region_submarkets_extractor
# import extractors.florida_counties_extractor
# import extractors.greater_vancouver_submarkets_extractor
# import extractors.texas_submarkets_extractor
# import extractors.greater_toronto_submarkets_extractor
# import extractors.georgia_submarkets_extractor
# import extractors.fraser_valley_submarkets_extractor

# from extractors.registry import EXTRACTOR_REGISTRY

# def route_extraction(market_name: str, market_path: str):
#     market_name_lower = market_name.lower()
#     # market_key must be in market's data folder's name
#     for key, extractor_func in EXTRACTOR_REGISTRY.items():
#         if key in market_name_lower:
#             return extractor_func(market_path)

#     raise ValueError(f"No extractor found for market: {market_name}")


import pkgutil
import importlib
import extractors

# Dynamically import every module in extractors/, so all @register_extractor() calls run
for _, module_name, _ in pkgutil.iter_modules(extractors.__path__):
    importlib.import_module(f"extractors.{module_name}")

from extractors.registry import EXTRACTOR_REGISTRY

def route_extraction(market_name: str, market_path: str):
    market_name_lower = market_name.lower()
    # market_key must be in market's data folder's name
    for key, extractor_func in EXTRACTOR_REGISTRY.items():
        if key in market_name_lower:
            return extractor_func(market_path)

    raise ValueError(f"No extractor found for market: {market_name}")
