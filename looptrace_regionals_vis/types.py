"""General custom data types"""

from collections.abc import Mapping

import pandas as pd

MappingLike = Mapping[str, object] | pd.Series
