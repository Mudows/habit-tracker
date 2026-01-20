from __future__ import annotations

def sparkline(values: list[int]) -> str:
    """
    Simple unicode sparkline for terminal.
    values: list of non-negative ints
    """
    if not values:
        return ""

    blocks = "▁▂▃▄▅▆▇█"
    vmin = min(values)
    vmax = max(values)

    if vmax == vmin:
        # tudo igual
        return blocks[0] * len(values)

    out = []
    for v in values:
        # normaliza 0..1
        t = (v - vmin) / (vmax - vmin)
        idx = int(round(t * (len(blocks) - 1)))
        out.append(blocks[idx])
    return "".join(out)
