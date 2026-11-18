from .registry import register_extractor
from .faststats_common_extractor import make_extractor

# Georgia sub-markets
register_extractor("georgia submarkets")(
    make_extractor(start_row=4420, start_col=2)
)

# Arizona sub-markets
register_extractor("arizona submarkets")(
    make_extractor(start_row=8087, start_col=2)
)