# cython: infer_types=True # DEVNOTE this is a compiler directive to let cython infer types on its own instead of requiring the user to specify all types. However, it will only infer types at the top level indentation. Nested scopes requires manual typing.
import numpy as np
import cython 

# Cython function including interface with numpy... and will run much slower than Python :)
def compute_np(array_1, array_2, a, b, c):
    return np.clip(array_1, 2, 10) * a + array_2 * b + c
