import numpy as np
import pandas as pd

class QpaError(Exception):
    """Custom exception for Quantitative Phase Analysis errors."""
    pass

def calculate_rir_quantification(phase_data):
    """
    Calculates the weight percent of each phase using the RIR method.
    """
    if not phase_data:
        return []
    i_over_rir_sum = 0
    i_over_rir_values = []
    for phase in phase_data:
        intensity = phase.get('intensity', 0)
        rir = phase.get('rir', 0)
        if rir <= 0:
            raise QpaError(f"RIR value for a phase must be greater than 0.")
        value = intensity / rir
        i_over_rir_values.append(value)
        i_over_rir_sum += value
    if i_over_rir_sum == 0:
        return [0.0] * len(phase_data)
    weight_percents = [(val / i_over_rir_sum) * 100.0 for val in i_over_rir_values]
    return weight_percents