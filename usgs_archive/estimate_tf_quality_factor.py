# -*- coding: utf-8 -*-
"""
Created on Wed Mar  6 09:43:07 2019

Estimate Transfer Function Quality
    
    * based on simple statistics

@author: jpeacock
"""
# =============================================================================
# Imports
# =============================================================================
import os
import glob
import numpy as np
import pandas as pd
from scipy import interpolate
from mtpy.core import mt

# =============================================================================
#
# =============================================================================
class EMTFStats(object):
    """
    Class to estimate data quality of EM transfer functions
    
    :param tf_dir: transfer function directory
    :type tf_dir: string
    
    :param stat_limits: criteria for statistics based on a 0-5 rating scale 
    :type stat_limits: dictionary
    
    :Example: ::
        
        >>> from usgs_archive import estimate_tf_quality_factor as tfq
        >>> edi_dir = r"/home/edi_folders/survey_01"
        >>> q = EMTFStats()
        >>> stat_df = q.compute_statistics(edi_dir) 
        >>> q_df = q.estimate_data_quality(stat_df=stat_df)         
        >>> s_df = q.summarize_data_quality(q_df) 
    """

    def __init__(self, tf_dir=None, *args, **kwargs):
        self.tf_dir = tf_dir
        self.stat_limits = {
            "std": {
                5: (0, 0.5),
                4: (0.5, 1.25),
                3: (1.25, 2.5),
                2: (2.5, 10.0),
                1: (10.0, 25.0),
                0: (25.0, 1e36),
            },
            "corr": {
                5: (0.975, 1.0),
                4: (0.9, 0.975),
                3: (0.75, 0.9),
                2: (0.5, 0.75),
                1: (0.25, 0.5),
                0: (-1.0, 0.25),
            },
            "diff": {
                5: (0.0, 0.5),
                4: (0.5, 1.0),
                3: (1.0, 2.0),
                2: (2.0, 5.0),
                1: (5.0, 10.0),
                0: (10.0, 1e36),
            },
            "fit": {
                5: (0, 5),
                4: (5, 15),
                3: (15, 50),
                2: (50, 100),
                1: (100, 200),
                0: (200, 1e36),
            },
            "bad": {
                5: (0, 2),
                4: (2, 4),
                3: (4, 10),
                2: (10, 15),
                1: (15, 20),
                0: (20, 1e36),
            },
        }

        self.z_dict = {(0, 0): "xx", (0, 1): "xy", (1, 0): "yx", (1, 1): "yy"}
        self.t_dict = {(0, 0): "x", (0, 1): "y"}
        self.types = (
            [
                "{3}_{0}{1}_{2}".format(ii, jj, kk, ll)
                for ii in ["x", "y"]
                for jj in ["x", "y"]
                for kk in ["std", "corr", "diff", "fit"]
                for ll in ["res", "phase"]
            ]
            + [
                "{2}_{0}_{1}".format(ii, kk, ll)
                for ii in ["x", "y"]
                for kk in ["std", "corr", "diff", "fit"]
                for ll in ["tipper"]
            ]
            + [
                "bad_points_{2}_{0}{1}".format(ii, jj, ll)
                for ii in ["x", "y"]
                for jj in ["x", "y"]
                for ll in ["res", "phase"]
            ]
            + ["bad_points_tipper_{0}".format(ii) for ii in ["x", "y"]]
        )

    def locate_bad_res_points(self, res):
        """
        try to locate bad points to remove
        """
        ### estimate levearge points, or outliers
        ### estimate the median
        med = np.median(res)
        ### locate the point closest to the median
        tol = np.abs(res - np.median(res)).min()
        m_index = np.where(
            (abs(res - med) >= tol * 0.95) & (abs(res - med) <= tol * 1.05)
        )[0][0]
        r_index = m_index + 1

        bad_points = []
        # go to the right
        while r_index < res.shape[0]:
            if abs(res[r_index] - res[r_index - 1]) > np.cos(np.pi / 4) * res[r_index]:
                bad_points.append(r_index)
            r_index += 1

        # go to the left
        l_index = m_index - 1
        while l_index > -1:
            if abs(res[l_index] - res[l_index - 1]) > np.cos(np.pi / 4) * res[l_index]:
                bad_points.append(l_index)
            l_index -= 1

        return np.array(bad_points)

    def locate_bad_phase_points(self, phase, test=5):
        """
        try to locate bad points to remove
        """
        ### estimate levearge points, or outliers
        ### estimate the median
        med = np.median(phase)
        ### locate the point closest to the median
        ### locate the point closest to the median
        tol = np.abs(phase - np.median(phase)).min()
        m_index = np.where(
            (abs(phase - med) >= tol * 0.95) & (abs(phase - med) <= tol * 1.05)
        )[0][0]
        r_index = m_index + 1

        bad_points = []
        # go to the right
        while r_index < phase.shape[0]:
            if abs(phase[r_index] - phase[r_index - 1]) > test:
                bad_points.append(r_index)
            r_index += 1

        # go to the left
        l_index = m_index - 1
        while l_index > -1:
            if abs(phase[l_index] - phase[l_index - 1]) > test:
                bad_points.append(l_index)
            l_index -= 1

        return np.array(bad_points)

    def locate_bad_tipper_points(self, tipper, test=0.2):
        """
        try to locate bad points to remove
        """
        ### estimate levearge points, or outliers
        ### estimate the median
        med = np.median(tipper)
        ### locate the point closest to the median
        tol = np.abs(tipper - np.median(tipper)).min()
        m_index = np.where(
            (abs(tipper - med) >= tol * 0.95) & (abs(tipper - med) <= tol * 1.05)
        )[0][0]
        r_index = m_index + 1

        bad_points = []
        # go to the right
        while r_index < tipper.shape[0]:
            if abs(tipper[r_index] - tipper[r_index - 1]) > test:
                bad_points.append(r_index)
            r_index += 1

        # go to the left
        l_index = m_index - 1
        while l_index > -1:
            if abs(tipper[l_index] - tipper[l_index - 1]) > test:
                bad_points.append(l_index)
            l_index -= 1

        return np.array(bad_points)

    def compute_statistics(self, tf_dir=None):
        """
        Compute statistics of the transfer functions in a given directory.
        
        Statistics are:
            
            * one-lag autocorrelation coefficient, estimator for smoothness
            * average of errors on components
            * fit to a least-squres smooth curve
            * normalized standard deviation of the first derivative, another
              smoothness estimator
              
        :param tf_dir: path to directory of transfer functions
        :type tf_dir: string
        
        :returns: data frame of all the statistics estimated
        :rtype: pandas.DataFrame
        
        .. note:: Writes a file to the tf_dir named tf_quality_statistics.csv 
        """

        if tf_dir is not None:
            self.tf_dir = tf_dir

        edi_list = glob.glob("{0}\*.edi".format(self.tf_dir))

        stat_array = np.zeros(
            len(edi_list), dtype=[(key, np.float) for key in sorted(self.types)]
        )
        station_list = []
        for kk, edi in enumerate(edi_list):
            mt_obj = mt.MT(edi)
            station_list.append(mt_obj.station)

            for ii in range(2):
                for jj in range(2):
                    flip = False
                    comp = self.z_dict[(ii, jj)]

                    ### locate bad points
                    bad_points_res = self.locate_bad_res_points(
                        mt_obj.Z.resistivity[:, ii, jj]
                    )
                    stat_array[kk]["bad_points_res_{0}".format(comp)] = max(
                        [1, len(bad_points_res)]
                    )
                    bad_points_phase = self.locate_bad_phase_points(
                        mt_obj.Z.phase[:, ii, jj]
                    )
                    stat_array[kk]["bad_points_phase_{0}".format(comp)] = max(
                        [1, len(bad_points_res)]
                    )
                    ### need to get the data points that are within the reasonable range
                    ### and not 0
                    nz_index = np.nonzero(mt_obj.Z.resistivity[:, ii, jj])
                    nz_index = np.delete(nz_index, bad_points_res)
                    nz_index = np.delete(nz_index, bad_points_phase)

                    f = mt_obj.Z.freq[nz_index]
                    res = mt_obj.Z.resistivity[nz_index, ii, jj]
                    res_err = mt_obj.Z.resistivity_err[nz_index, ii, jj]
                    phase = mt_obj.Z.phase[nz_index, ii, jj]
                    phase_err = mt_obj.Z.phase_err[nz_index, ii, jj]

                    if len(f) < 2:
                        print(mt_obj.station, comp, nz_index)
                        continue

                    # need to sort the array to be ordered with assending
                    # frequency.  Check to see if f is ascending, if not flip
                    if f[0] > f[1]:
                        flip = True
                        f = f[::-1]
                        res = res[::-1]
                        res_err = res_err[::-1]
                        phase = phase[::-1]
                        phase_err = phase_err[::-1]

                    ### make parameter for least squares fit
                    k = 7  # order of the fit
                    # knots, has to be at least to the bounds of f
                    t = np.r_[(f[0],) * (k + 1), [min(1, f.mean())], (f[-1],) * (k + 1)]

                    ### estimate a least squares fit
                    try:
                        ls_res = interpolate.make_lsq_spline(f, res, t, k)
                        ls_phase = interpolate.make_lsq_spline(f, phase, t, k)

                        ### compute a standard deviation between the ls fit and data
                        stat_array[kk]["res_{0}_fit".format(comp)] = (
                            res - ls_res(f)
                        ).std()
                        stat_array[kk]["phase_{0}_fit".format(comp)] = (
                            phase - ls_phase(f)
                        ).std()
                    except (ValueError, np.linalg.LinAlgError) as error:
                        stat_array[kk]["res_{0}_fit".format(comp)] = np.NaN
                        stat_array[kk]["phase_{0}_fit".format(comp)] = np.NaN
                        print("{0} {1} {2}".format(mt_obj.station, comp, error))
                    ### taking median of the error is more robust
                    stat_array[kk]["res_{0}_std".format(comp)] = np.median(res_err)
                    stat_array[kk]["phase_{0}_std".format(comp)] = np.median(phase_err)

                    ### estimate smoothness
                    stat_array[kk]["res_{0}_corr".format(comp)] = np.corrcoef(
                        res[0:-1], res[1:]
                    )[0, 1]
                    stat_array[kk]["phase_{0}_corr".format(comp)] = np.corrcoef(
                        phase[0:-1], phase[1:]
                    )[0, 1]

                    ### estimate smoothness with difference
                    stat_array[kk]["res_{0}_diff".format(comp)] = np.abs(
                        np.median(np.diff(res))
                    )
                    stat_array[kk]["phase_{0}_diff".format(comp)] = np.abs(
                        np.median(np.diff(phase))
                    )

                    ### compute tipper
                    if ii == 0:
                        tcomp = self.t_dict[(0, jj)]
                        t_index = np.nonzero(mt_obj.Tipper.amplitude[:, 0, jj])
                        bad_points_t = self.locate_bad_tipper_points(
                            mt_obj.Tipper.amplitude[:, 0, jj]
                        )
                        stat_array[kk]["bad_points_tipper_{0}".format(tcomp)] = max(
                            [1, len(bad_points_t)]
                        )
                        t_index = np.delete(t_index, bad_points_t)
                        if t_index.size == 0:
                            continue
                        else:
                            tmag = mt_obj.Tipper.amplitude[t_index, 0, jj]
                            tmag_err = mt_obj.Tipper.amplitude_err[t_index, 0, jj]
                            tip_f = mt_obj.Tipper.freq[t_index]
                            if flip:
                                tmag = tmag[::-1]
                                tmag_err = tmag_err[::-1]
                                tip_f = tip_f[::-1]
                            tip_t = np.r_[
                                (tip_f[0],) * (k + 1),
                                [min(1, tip_f.mean())],
                                (tip_f[-1],) * (k + 1),
                            ]
                            try:
                                ls_tmag = interpolate.make_lsq_spline(
                                    tip_f, tmag, tip_t, k
                                )
                                stat_array[kk]["tipper_{0}_fit".format(tcomp)] = np.std(
                                    tmag - ls_tmag(tip_f)
                                )
                            except (ValueError, np.linalg.LinAlgError) as error:

                                stat_array[kk]["tipper_{0}_fit".format(tcomp)] = np.NaN
                                print(
                                    "{0} {1} {2}".format(mt_obj.station, tcomp, error)
                                )
                            stat_array[kk][
                                "tipper_{0}_std".format(tcomp)
                            ] = tmag_err.mean()
                            stat_array[kk][
                                "tipper_{0}_corr".format(tcomp)
                            ] = np.corrcoef(tmag[0:-1], tmag[1:])[0, 1]
                            stat_array[kk]["tipper_{0}_diff".format(tcomp)] = np.std(
                                np.diff(tmag)
                            ) / abs(np.mean(np.diff(tmag)))

        ### write file
        df = pd.DataFrame(stat_array, index=station_list)
        df = df.replace(0, np.NAN)
        df.to_csv(
            os.path.join(self.tf_dir, "tf_quality_statistics.csv"),
            index=True,
            na_rep="NaN",
        )

        return df

    def estimate_data_quality(self, stat_df=None, stat_fn=None):
        """
        Convert the statistical estimates into the rating between 0-5 given
        a certain criteria.
        
        .. note:: To change the criteria change self.stat_limits
        
        :param stat_df: Dataframe of the statistics
        :type stat_df: pandas.DataFrame
        
        :param stat_fn: name of .csv file of statistics
        :type stat_fn: string
        
        :returns: a dataframe of the converted statistics
        :rtype: pandas.DataFrame
        
        .. note:: Writes a file to the tf_dir named tf_quality_estimate.csv
        """
        if stat_df is not None:
            stat_df = stat_df

        if stat_fn is not None:
            stat_df = pd.read_csv(stat_fn, index_col=0)
            self.tf_dir = os.path.dirname(stat_fn)

        if stat_df is None:
            raise ValueError("No DataFrame to analyze")

        ### make a copy of the data fram to put quality factors in
        qual_df = pd.DataFrame(
            np.zeros(
                stat_df.shape[0], dtype=[(key, np.float) for key in sorted(self.types)]
            ),
            index=stat_df.index,
        )
        for col in qual_df.columns:
            qual_df[col].values[:] = np.NaN

        ### loop over quality factors
        for qkey in self.stat_limits.keys():
            for column in qual_df.columns:
                if qkey in column:
                    for ckey, cvalues in self.stat_limits[qkey].items():
                        qual_df[column][
                            (stat_df[column] > cvalues[0])
                            & (stat_df[column] <= cvalues[1])
                        ] = ckey

        ### write out file
        qual_df.to_csv(
            os.path.join(self.tf_dir, "tf_quality_estimate.csv"), na_rep="NaN"
        )

        return qual_df

    def summarize_data_quality(
        self,
        quality_df=None,
        quality_fn=None,
        weights={"bad": 0.35, "corr": 0.2, "diff": 0.2, "std": 0.2, "fit": 0.05},
    ):
        """
        Summarize the data quality into a single number for each station.
        
        :param quality_df: Dataframe of the quality factors
        :type quality_df: pandas.DataFrame
        
        :param quality_fn: name of .csv file of quality factors
        :type quality_fn: string
        
        :returns: a dataframe of the  summarized quality factors
        :rtype: pandas.DataFrame
        
        .. note:: Writes a file to the tf_dir named tf_quality.csv
        """
        if quality_df is not None:
            quality_df = quality_df

        if quality_fn is not None:
            quality_df = pd.read_csv(quality_fn, index_col=0)
            self.tf_dir = os.path.dirname(quality_fn)

        if quality_df is None:
            raise ValueError("No DataFrame to analyze")

        ### compute median value
        ### need to weight things differently
        bad_df = quality_df[[col for col in quality_df.columns if "bad" in col]]
        diff_df = quality_df[[col for col in quality_df.columns if "diff" in col]]
        fit_df = quality_df[[col for col in quality_df.columns if "fit" in col]]
        corr_df = quality_df[[col for col in quality_df.columns if "corr" in col]]
        std_df = quality_df[[col for col in quality_df.columns if "std" in col]]

        qf_df = (
            weights["bad"] * bad_df.median(axis=1)
            + weights["corr"] * corr_df.median(axis=1)
            + weights["diff"] * diff_df.median(axis=1)
            + weights["std"] * std_df.median(axis=1)
            + weights["fit"] * fit_df.median(axis=1)
        )

        qf_df = qf_df.round()
        qf_df.to_csv(os.path.join(self.tf_dir, "tf_quality.csv"), header=False)
        return qf_df

    def estimate_quality_factors(
        self,
        tf_dir=None,
        weights={"bad": 0.35, "corr": 0.2, "diff": 0.2, "std": 0.2, "fit": 0.05},
    ):
        """
        Convenience function doing all the steps to estimate quality factor
        """

        if tf_dir is not None:
            self.tf_dir = tf_dir
        assert os.path.isdir(self.tf_dir) is True, "{0} is not a directory".format(
            self.tf_dir
        )

        statistics_df = self.compute_statistics()
        qualities_df = self.estimate_data_quality(stat_df=statistics_df)
        qf_df = self.summarize_data_quality(quality_df=qualities_df, weights=weights)

        return qf_df


# =============================================================================
# Test
# =============================================================================
# edi_dir = r"c:\Users\jpeacock\Documents\edi_folders\imush_edi"
# q = EMTFStats()
# stat_df = q.compute_statistics(edi_dir)
# q_df = q.estimate_data_quality(stat_df=stat_df)
# s_df = q.summarize_data_quality(q_df)
