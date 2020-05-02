def clamp(value, min, max):
    value = value if value > min else min
    value = value if value < max else max
    return value
