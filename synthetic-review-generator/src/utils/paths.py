import os
from datetime import datetime

def build_output_dirs(base="data/synthetic"):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")

    paths = {
        "timestamp": ts,
        "base": base,
        "logs": os.path.join(base, "logs"),
        "reviews": os.path.join(base, "reviews"),
        "models": os.path.join(base, "reviews_models"),
    }

    for p in paths.values():
        if isinstance(p, str):
            os.makedirs(p, exist_ok=True)

    return paths
