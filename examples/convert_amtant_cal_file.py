# -*- coding: utf-8 -*-
"""
Read an amtant.cal file provided by Zonge.  


Apparently, the file includes the 6th and 8th harmonic of the given frequency, which
is a fancy way of saying f * 6 and f * 8. 

variables
-----------

    **ant_fn**: full path to the calibration file
    
    **birrp**: If the calibration files are written for BIRRP then need to add
    a line at the beginning of the file that describes any scaling factors for 
    the calibrations, should be 1, 1, 1
    
    **angular_frequency**: Puts the frequency in angular frequency (2 * pi * f)
     
    **quadrature**: puts the response in amplitude and phase (True) or 
    real and imaginary (False)
    
    **nf**: number of expected frequencies
 
"""
# =============================================================================
# Imports
# =============================================================================
from pathlib import Path
import numpy as np
import pandas as pd

# =============================================================================
# Variables
# =============================================================================
ant_fn = Path(r"c:\Users\jpeacock\OneDrive - DOI\mt\antenna_20190411.cal")
save_path = Path(ant_fn.parent, "ant_responses")
birrp = False
angular_frequency = False
quadrature = False
nf = 48

if quadrature:
    cal_dtype = [("frequency", np.float), ("amplitude", np.float), ("phase", np.float)]

else:
    cal_dtype = [("frequency", np.float), ("real", np.float), ("imaginary", np.float)]


# =============================================================================
# Script
# =============================================================================
if not save_path.exists():
    save_path.mkdir()

with open(ant_fn, "r") as fid:
    lines = fid.readlines()

ant_dict = {}
ff = -2
for line in lines:
    if "antenna" in line.lower():
        f = float(line.split()[2].strip())
        if angular_frequency:
            f = 2 * np.pi * f

        ff += 2
    elif len(line.strip().split()) == 0:
        continue
    else:
        line_list = line.strip().split()
        ant = line_list[0]
        amp6 = float(line_list[1])
        phase6 = float(line_list[2]) / 1000
        amp8 = float(line_list[3])
        phase8 = float(line_list[4]) / 1000

        if not quadrature:
            z_real6 = amp6 * np.cos(phase6)
            z_imag6 = amp6 * np.sin(phase6)

            z_real8 = amp8 * np.cos(phase8)
            z_imag8 = amp8 * np.sin(phase8)

        try:
            ant_dict[ant]
        except KeyError:
            if birrp:
                # BIRRP now expects the first line to be a scaling factor
                # need to set this to 1
                nf += 1
                ant_dict[ant] = np.zeros(nf, dtype=cal_dtype)
                ant_dict[ant][0] = (1, 1, 1)  # needed for birrp

            else:
                ant_dict[ant] = np.zeros(nf, dtype=cal_dtype)

        if not quadrature:
            ant_dict[ant][ff] = (f * 6, z_real6, z_imag6)
            ant_dict[ant][ff + 1] = (f * 8, z_real8, z_imag8)
        else:
            ant_dict[ant][ff] = (f * 6, amp6, phase6)
            ant_dict[ant][ff + 1] = (f * 8, amp8, phase8)


for key in ant_dict.keys():
    df = pd.DataFrame(ant_dict[key])

    df.to_csv(
        save_path.joinpath(f"{key}.csv"), index=False, header=True, float_format="%.5e"
    )
