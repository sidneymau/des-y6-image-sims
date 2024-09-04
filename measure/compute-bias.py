import argparse
from pathlib import Path
import os

import joblib
import tqdm
import numpy as np
import fitsio

import des_y6utils

import selections
import weights
import util


def get_grid(data, ngrid):

    dgrid = 10_000 / ngrid
    xind = np.floor(data["x"] / dgrid)
    yind = np.floor(data["y"] / dgrid)
    gind = yind * ngrid + xind

    return gind


def load_file(fname, cuts=False):
    fits = fitsio.FITS(fname)
    w = fits[1].where("mdet_step == \"noshear\"")
    # w = fits[1].where("mdet_step == \"noshear\" && mdet_flags == 0")
    data = fits[1][w]
    if cuts:
        inds, = np.where(
            (data['psfrec_flags'] == 0) &
            (data['gauss_flags'] == 0) &
            (data['gauss_s2n'] > 5) &
            (data['pgauss_T_flags'] == 0) &
            (data['pgauss_s2n'] > 5) &
            (data['pgauss_band_flux_flags_g'] == 0) &
            (data['pgauss_band_flux_flags_r'] == 0) &
            (data['pgauss_band_flux_flags_i'] == 0) &
            (data['pgauss_band_flux_flags_z'] == 0) &
            (data['mask_flags'] == 0) &
            (data['shear_bands'] == '123')
        )
        data = data[inds]
        data = des_y6utils.mdet.add_extinction_correction_columns(data)

    # mask = selections.get_selection(data)

    # return data[mask]
    return data



def grid_file(*, fname, ngrid):
    d = fitsio.read(fname)
    # d = load_file(fname, cuts=False)
    cuts = d["mdet_flags"] == 0
    d = d[cuts]

    gind = get_grid(d, ngrid)

    # msk = selections.get_selection(d)

    vals = []

    ugind = np.unique(gind)
    for _gind in range(ngrid*ngrid):
        # gmsk = msk & (_gind == gind)
        gmsk = (_gind == gind)
        if np.any(gmsk):
            sval = []
            for shear in ["noshear", "1p", "1m", "2p", "2m"]:
                sgmsk = gmsk & (d["mdet_step"] == shear)
                if np.any(sgmsk):
                    _d = d[sgmsk]
                    _w = weights.get_shear_weights(_d)
                    # sval.append(np.mean(d["gauss_g_1"][sgmsk]))
                    # sval.append(np.mean(d["gauss_g_2"][sgmsk]))
                    # sval.append(np.sum(sgmsk))
                    sval.append(np.average(_d["gauss_g_1"], weights=_w))
                    sval.append(np.average(_d["gauss_g_2"], weights=_w))
                    sval.append(np.sum(_w))  # TODO should this be sum(_w) or sum(sgmsk)?
                else:
                    sval.append(np.nan)
                    sval.append(np.nan)
                    sval.append(np.nan)
            vals.append(tuple(sval + [_gind]))
        else:
            vals.append(tuple([np.nan] * 3 * 5 + [_gind]))

    return np.array(
        vals,
        dtype=[
            ("g1", "f8"),
            ("g2", "f8"),
            ("n", "f8"),
            ("g1_1p", "f8"),
            ("g2_1p", "f8"),
            ("n_1p", "f8"),
            ("g1_1m", "f8"),
            ("g2_1m", "f8"),
            ("n_1m", "f8"),
            ("g1_2p", "f8"),
            ("g2_2p", "f8"),
            ("n_2p", "f8"),
            ("g1_2m", "f8"),
            ("g2_2m", "f8"),
            ("n_2m", "f8"),
            ("grid_ind", "i4")
        ]
    )


# def grid_file_pair(*, fplus, fminus, ngrid, Tratio=0.5, s2n=10, mfrac=0.1):
#     dp = grid_file(fname=fplus, ngrid=ngrid, Tratio=Tratio, s2n=s2n, mfrac=mfrac)
#     dm = grid_file(fname=fminus, ngrid=ngrid, Tratio=Tratio, s2n=s2n, mfrac=mfrac)
# 
#     assert np.all(dp["grid_ind"] == dm["grid_ind"])
# 
#     dt = []
#     for tail in ["_p", "_m"]:
#         for name in dp.dtype.names:
#             if name != "grid_ind":
#                 dt.append((name + tail, "f8"))
#     dt.append(("grid_ind", "i4"))
#     d = np.zeros(ngrid * ngrid, dtype=dt)
#     for _d, tail in [(dp, "_p"), (dm, "_m")]:
#         for name in _d.dtype.names:
#             if name != "grid_ind":
#                 d[name + tail] = _d[name]
#     d["grid_ind"] = dp["grid_ind"]
# 
#     return d
def grid_file_pair(dset_plus, dset_minus, *, ngrid=1):
    dp = grid_file(fname=dset_plus, ngrid=ngrid)
    dm = grid_file(fname=dset_minus, ngrid=ngrid)

    assert np.all(dp["grid_ind"] == dm["grid_ind"])

    dt = []
    for tail in ["_p", "_m"]:
        for name in dp.dtype.names:
            if name != "grid_ind":
                dt.append((name + tail, "f8"))
    dt.append(("grid_ind", "i4"))
    d = np.zeros(ngrid * ngrid, dtype=dt)
    for _d, tail in [(dp, "_p"), (dm, "_m")]:
        for name in _d.dtype.names:
            if name != "grid_ind":
                d[name + tail] = _d[name]
    d["grid_ind"] = dp["grid_ind"]

    return d

def compute_shear_pair(d):
    g1_p = np.nansum(d["g1_p"] * d["n_p"]) / np.nansum(d["n_p"])
    g1p_p = np.nansum(d["g1_1p_p"] * d["n_1p_p"]) / np.nansum(d["n_1p_p"])
    g1m_p = np.nansum(d["g1_1m_p"] * d["n_1m_p"]) / np.nansum(d["n_1m_p"])
    R11_p = (g1p_p - g1m_p) / 0.02

    g1_m = np.nansum(d["g1_m"] * d["n_m"]) / np.nansum(d["n_m"])
    g1p_m = np.nansum(d["g1_1p_m"] * d["n_1p_m"]) / np.nansum(d["n_1p_m"])
    g1m_m = np.nansum(d["g1_1m_m"] * d["n_1m_m"]) / np.nansum(d["n_1m_m"])
    R11_m = (g1p_m - g1m_m) / 0.02

    g2_p = np.nansum(d["g2_p"] * d["n_p"]) / np.nansum(d["n_p"])
    g2p_p = np.nansum(d["g2_2p_p"] * d["n_2p_p"]) / np.nansum(d["n_2p_p"])
    g2m_p = np.nansum(d["g2_2m_p"] * d["n_2m_p"]) / np.nansum(d["n_2m_p"])
    R22_p = (g2p_p - g2m_p) / 0.02

    g2_m = np.nansum(d["g2_m"] * d["n_m"]) / np.nansum(d["n_m"])
    g2p_m = np.nansum(d["g2_2p_m"] * d["n_2p_m"]) / np.nansum(d["n_2p_m"])
    g2m_m = np.nansum(d["g2_2m_m"] * d["n_2m_m"]) / np.nansum(d["n_2m_m"])
    R22_m = (g2p_m - g2m_m) / 0.02

    # return (g1_p - g1_m) / (R11_p + R11_m) / 0.02 - 1., (g2_p + g2_m) / (R22_p + R22_m)
    # return (g1_p - g1_m) / (R11_p + R11_m) / 0.02 - 1., (g1_p + g1_m) / (R11_p + R11_m)
    return (g1_p - g1_m) / (R11_p + R11_m) / 0.02 - 1., (g1_p + g1_m) / (R11_p + R11_m), (g2_p + g2_m) / (R22_p + R22_m)


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "imsim_dir",
        type=str,
        help="Image simulation output directory",
    )
    parser.add_argument(
        "--seed",
        type=int,
        required=False,
        default=1,
        help="RNG seed [int]",
    )
    parser.add_argument(
        "--n_jobs",
        type=int,
        required=False,
        default=8,
        help="Number of joblib jobs [int]",
    )
    parser.add_argument(
        "--resample",
        type=str,
        required=False,
        default="jackknife",
        choices=["jackknife", "bootstrap"],
        help="Resample method [str]",
    )
    parser.add_argument(
        "--grid",
        type=int,
        required=False,
        default=1,
        help="How many patches in the subgrid [int]",
    )
    return parser.parse_args()


def main():

    args = get_args()

    grid = args.grid
    resample = args.resample

    pairs = {}

    imsim_path = Path(args.imsim_dir)
    config_name = imsim_path.name
    tile_dirs = imsim_path.glob("*")

    catalogs = util.gather_catalogs(imsim_path)
    ntiles = len(np.unique([tile for tile in catalogs.keys()]))

    results = []
    jobs = [
        joblib.delayed(grid_file_pair)(catalogs[tile]["plus"], catalogs[tile]["minus"], ngrid=grid)
        for tile in catalogs.keys()
    ]
    print(f"Processing {len(jobs)} paired simulations")

    with joblib.Parallel(n_jobs=args.n_jobs, backend="loky", verbose=10) as par:
        data = par(jobs)

    data = np.concatenate(data, axis=0)

    print(f"Computing uncertainties via {resample}")
    if resample == "bootstrap":
        ns = 1000  # number of bootstrap resamples
        rng = np.random.RandomState(seed=args.seed)

        m_mean, c_mean_1, c_mean_2 = compute_shear_pair(data)

        print(f"Bootstrapping with {ns} resamples")
        bootstrap = []
        for i in tqdm.trange(ns, ncols=80):
            rind = rng.choice(data.shape[0], size=data.shape[0], replace=True)
            _bootstrap = data[rind]
            bootstrap.append(compute_shear_pair(_bootstrap))

        bootstrap = np.array(bootstrap)
        m_std, c_std_1, c_std_2 = np.std(bootstrap, axis=0)

    elif resample == "jackknife":
        jackknife = []
        for i in tqdm.trange(len(data), ncols=80):
            _pre = data[:i]
            _post = data[i + 1:]
            _jackknife = np.concatenate((_pre, _post))
            jackknife.append(compute_shear_pair(_jackknife))

        _n = len(jackknife)
        # m_mean, c_mean_1, c_mean_2 = np.mean(jackknife, axis=0)
        jackknife_mean = np.mean(jackknife, axis=0)
        # jackknife_var = ((_n - 1) / _n) * np.sum(np.square(np.subtract(jackknife, jackknife_mean)), axis=0)
        jackknife_std = np.sqrt(((_n - 1) / _n) * np.sum(np.square(np.subtract(jackknife, jackknife_mean)), axis=0))

        m_mean, c_mean_1, c_mean_2 = jackknife_mean
        m_std, c_std_1, c_std_2 = jackknife_std

    # print("\v")
    # print("m:	(%0.3e, %0.3e)" % (m_mean - m_std * 3, m_mean + m_std * 3))
    # print("m mean:	%0.3e" % m_mean)
    # print("m std:	%0.3e [3 sigma]" % (m_std * 3))
    # print("\v")
    # print("c:	(%0.3e, %0.3e)" % (c_mean - c_std * 3, c_mean + c_std * 3))
    # print("c mean:	%0.3e" % c_mean)
    # print("c std:	%0.3e [3 sigma]" % (c_std * 3))
    # print("\v")
    # print(f"| {config_name} | {m_mean:0.3e} | {m_std*3:0.3e} | {c_mean_1:0.3e} | {c_std_1*3:0.3e} | {c_mean_2:0.3e} | {c_std_2*3:0.3e} | {ntiles} | {mfrac} |")
    results.append(
        (config_name, m_mean, m_std * 3, c_mean_1, c_std_1 * 3, c_mean_2, c_std_2 * 3, ntiles)
    )

    print(f"| configuration | m mean | m std (3σ) | c_1 mean | c_1 std (3σ) | c_2 mean | c_2 std (3σ) | # tiles |")
    # print(f"|---|---|---|---|---|---|")
    # header = ("configuration", "m mean", "m std (3σ)", "c_1 mean", "c_1 std (3σ)", "c_2 mean", "c_2 std (3σ)", "# tiles", "mfrac")
    # print(header)
    # columns = [
    #     [
    #         results[i][j] for i in range(len(results))
    #     ] for j in range(len(results[0]))
    # ]
    # data = {
    #     header[j]: [
    #         results[i][j] for i in range(len(results))
    #     ] for j in range(len(results[0]))
    # }
    # column_widths = [
    #     max([range(val) for val in col])
    #     for col in columns
    # ]
    for result in results:
        # print(result)
        print(f"| {result[0]} | {result[1]:0.3e} | {result[2]:0.3e} | {result[3]:0.3e} | {result[4]:0.3e} | {result[5]:0.3e} | {result[6]:0.3e} | {result[7]} |")


if __name__ == "__main__":
    main()
