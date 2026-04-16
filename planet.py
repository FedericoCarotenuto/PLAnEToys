"""
PLAnET – Phyllosphere–Linked Aerobiology and Emissions Tool
============================================================
Python translation of the original MATLAB PLAnET model (Šantl-Temkiv et al.
/ original MATLAB formulation).

The model describes both phyllospheric microbial population dynamics and net
fluxes of microorganisms on the basis of simple meteorological variables.

Three public callables are exposed:
  - ``settvel``   – gravitational settling velocity for a spherical particle
  - ``slinnmod``  – impaction/interception deposition velocity (Slinn model)
  - ``PLAnET``    – the full model (population + flux dynamics)

Usage (Jupyter-friendly)
------------------------
>>> import numpy as np
>>> from planet import PLAnET, ModelConstants, ModelParams
>>>
>>> data = np.loadtxt("my_forcing.csv", delimiter=",")
>>> result = PLAnET(data, ustar_flag=False, depo_flag=True)
>>> result.population        # ndarray, CFU m-2
>>> result.net_flux          # ndarray, CFU m-2 s-1

References
----------
Original MATLAB implementation: PLAnET Patch 1 (24/09/2018).
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from typing import Optional

import numpy as np


# ---------------------------------------------------------------------------
# Data containers
# ---------------------------------------------------------------------------

@dataclass
class ModelConstants:
    """
    Physical / experimental constants that rarely change.

    Attributes
    ----------
    z : float
        Height of anemometer used to derive u* from wind speed (m).
        Default: 10 m.
    z0 : float
        Surface roughness length (m). Default: 0.15 m.
    d : float
        Integration time-step (s). Default: 1800 s (half-hourly).
    dia : float
        Diameter of the biological aerosol particle (µm). Default: 3.3 µm.
    zc : float
        Canopy average height (m). Default: 0.2 m.
    """
    z: float = 10.0
    z0: float = 0.15
    d: float = 1800.0
    dia: float = 3.3
    zc: float = 0.2


@dataclass
class ModelParams:
    """
    Ecophysiological and emission parameters of the PLAnET model.

    These are the 11 tuneable parameters described in the original MATLAB
    header.  Default values are those from the original model formulation.

    Attributes
    ----------
    T_min : float
        Minimum growth temperature (°C).
    T_max : float
        Maximum growth temperature (°C).
    T_opt : float
        Optimal growth temperature (°C).
    k_min : float
        Lower population boundary (CFU m-2).
    k_max : float
        Upper population boundary (CFU m-2).
    slp : float
        Gompertz coefficient 1 (amplitude) for upward flux.
    slp2 : float
        Gompertz coefficient 2 (rate) for upward flux.
    slp3 : float
        Gompertz coefficient 3 (inflection) for upward flux.
    c : float
        Scaling coefficient multiplying the growth of microorganisms.
    lai1 : float
        Slope of the LAI–background-concentration linear relationship.
    lai2 : float
        Offset of the LAI–background-concentration linear relationship.
    """
    T_min: float = 12.959980999122827
    T_max: float = 30.159885612670195
    T_opt: float = 21.559933305896510
    k_min: float = 5.003398245516982e+04
    k_max: float = 4.816110269787611e+05
    slp: float = 30.0
    slp2: float = 256.26
    slp3: float = 19.0
    c: float = 0.132575241852830
    lai1: float = 26.99
    lai2: float = 115.9

    @classmethod
    def from_array(cls, arr: np.ndarray) -> "ModelParams":
        """
        Build a ``ModelParams`` instance from an 11-element array,
        following the same ordering as the original MATLAB ``params`` vector.

        Parameters
        ----------
        arr : array-like, shape (11,)

        Returns
        -------
        ModelParams
        """
        arr = np.asarray(arr, dtype=float)
        if arr.size != 11:
            raise ValueError(
                f"params array must have exactly 11 elements, got {arr.size}."
            )
        return cls(
            T_min=arr[0], T_max=arr[1], T_opt=arr[2],
            k_min=arr[3], k_max=arr[4],
            slp=arr[5], slp2=arr[6], slp3=arr[7],
            c=arr[8],
            lai1=arr[9], lai2=arr[10],
        )


@dataclass
class PLAnETResult:
    """
    Container for all outputs of the PLAnET model.

    All arrays have shape ``(n_timesteps,)``.

    Attributes
    ----------
    population : np.ndarray
        Phyllospheric microbial population (CFU m-2).
    growth : np.ndarray
        Microbial growth rate (dimensionless, per time-step fraction).
    k_max : np.ndarray
        LAI-modulated population cap at each time step (CFU m-2).
    gross_out : np.ndarray
        Gross upward (emission) flux (CFU m-2 s-1).
    gross_in : np.ndarray
        Gross downward (deposition) flux (CFU m-2 s-1).
    conc : np.ndarray
        Background airborne microbial concentration (CFU m-3).
    net_flux : np.ndarray
        Net microbial flux; positive = upward / outgoing (CFU m-2 s-1).
    vg : np.ndarray
        Gravitational settling velocity (m s-1). NaN when depo_flag=False.
    vimp : np.ndarray
        Impaction/interception deposition velocity (m s-1). NaN when
        depo_flag=False.
    vdep : np.ndarray
        Total deposition velocity vg + vimp (m s-1). NaN when
        depo_flag=False.
    dflag : np.ndarray
        Boolean array; True where deposition module was active.
    dieout : np.ndarray
        Lateral die-out flow due to habitat loss (CFU m-2).
    overflow : np.ndarray
        Boolean array flagging population overflow warnings.
    underflow : np.ndarray
        Boolean array flagging population underflow warnings.
    """
    population: np.ndarray = field(default_factory=lambda: np.array([]))
    growth: np.ndarray = field(default_factory=lambda: np.array([]))
    k_max: np.ndarray = field(default_factory=lambda: np.array([]))
    gross_out: np.ndarray = field(default_factory=lambda: np.array([]))
    gross_in: np.ndarray = field(default_factory=lambda: np.array([]))
    conc: np.ndarray = field(default_factory=lambda: np.array([]))
    net_flux: np.ndarray = field(default_factory=lambda: np.array([]))
    vg: np.ndarray = field(default_factory=lambda: np.array([]))
    vimp: np.ndarray = field(default_factory=lambda: np.array([]))
    vdep: np.ndarray = field(default_factory=lambda: np.array([]))
    dflag: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    dieout: np.ndarray = field(default_factory=lambda: np.array([]))
    overflow: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))
    underflow: np.ndarray = field(default_factory=lambda: np.array([], dtype=bool))


# ---------------------------------------------------------------------------
# Physical sub-models
# ---------------------------------------------------------------------------

def settvel(
    d: float | np.ndarray,
    T: float | np.ndarray,
    P: float | np.ndarray,
) -> float | np.ndarray:
    """
    Compute gravitational settling velocity for a spherical bioaerosol.

    Uses Stokes' law with the Cunningham slip-correction factor and a
    temperature-/pressure-dependent mean free path.

    Parameters
    ----------
    d : float or ndarray
        Particle diameter (µm).
    T : float or ndarray
        Air temperature (K).
    P : float or ndarray
        Air pressure (Pa).

    Returns
    -------
    vg : float or ndarray
        Gravitational settling velocity (m s-1).

    Notes
    -----
    Constants follow Cox & Wathes (1995) *Bioaerosols Handbook* for
    bioaerosol density and Cunningham slip-correction factors.

    Examples
    --------
    >>> settvel(3.3, 293.15, 101325)
    """
    # --- constants ---
    rho_p: float = 1100.0      # bioaerosol density (kg m-3)  [Cox & Wathes 1995]
    eta: float = 1.833e-5      # dynamic air viscosity (Pa s)
    a1: float = 1.257          # Cunningham slip factor 1
    a2: float = 0.4            # Cunningham slip factor 2
    a3: float = 1.1            # Cunningham slip factor 3
    lr: float = 0.0665         # reference mean free path of air (µm)
    g: float = 9.78            # gravitational acceleration (m s-2)

    # temperature- and pressure-dependent mean free path (µm)
    kP = P / 1000.0  # Pa -> kPa
    l = lr * (101.0 / kP) * (T / 293.0) * ((1.0 + 110.0 / 293.0) / (1.0 + 110.0 / T))

    # Cunningham slip-correction factor
    Cc = 1.0 + (2.0 * l / d) * (a1 + a2 * np.exp((-a3 * d) / (2.0 * l)))

    # diameter in metres
    dm = d / 1.0e6

    vg = (g * rho_p * dm**2 * Cc) / (18.0 * eta)
    return vg


def slinnmod(
    wsp: float | np.ndarray,
    ust: float | np.ndarray,
    dp: float | np.ndarray,
    vg: float | np.ndarray,
    zc: float,
    z0: float,
) -> float | np.ndarray:
    """
    Compute impaction/interception deposition velocity (Slinn model).

    This is valid only for particles ≥ 1 µm (diffusional effects are
    not included).

    Parameters
    ----------
    wsp : float or ndarray
        Wind speed at reference height (m s-1).
    ust : float or ndarray
        Friction velocity u* (m s-1).
    dp : float or ndarray
        Particle diameter (µm).  Must be ≥ 1 µm.
    vg : float or ndarray
        Gravitational settling velocity (m s-1), typically from
        :func:`settvel`.
    zc : float
        Canopy average height (m).
    z0 : float
        Roughness length (m).

    Returns
    -------
    vimp : float or ndarray
        Impaction/interception deposition velocity (m s-1).

    Raises
    ------
    ValueError
        If any ``dp`` value is < 1 µm (outside valid range).

    Notes
    -----
    Vegetation collection parameters follow the default Slinn
    formulation; they may be adjusted via the constants block below.

    Examples
    --------
    >>> vg_val = settvel(3.3, 293.15, 101325)
    >>> slinnmod(5.0, 0.3, 3.3, vg_val, zc=0.2, z0=0.15)
    """
    # --- model parameters ---
    a_small: float = 10e-6    # diameter of smallest interceptor (m)  [vegetative hairs]
    a_big: float = 1e-3       # diameter of largest interceptor (m)
    cvcd: float = 1.0 / 3.0  # ratio Cv/Cd (viscous drag / avg drag)
    F: float = 0.01           # fraction of momentum collected by small collectors
    b: float = 2.0            # rebound factor exponent

    # --- physical constant ---
    von_karman: float = 0.4

    # Validate particle diameter range
    dp_arr = np.atleast_1d(np.asarray(dp, dtype=float))
    if np.any(dp_arr < 1.0):
        raise ValueError(
            "slinnmod is implemented without diffusional effects and is "
            "reliable only for particles ≥ 1 µm. "
            f"Received dp = {dp_arr[dp_arr < 1.0]}."
        )

    # Convert diameter from µm to m
    dp_m = dp_arr * 1e-6

    l = zc  # mixing length ≈ canopy height
    gam = (l * 100.0) ** 0.5

    Cd = ust**2 / wsp**2
    uhur = (ust / (von_karman * wsp)) * np.log(l / z0)

    St = (vg * ust) / (a_big * 9.78)

    Ein = cvcd * (F * (dp_m / (dp_m + a_small)) + (1.0 - F) * (dp_m / (dp_m + a_big)))
    Eim = St / (1.0 + St**2)
    R = np.exp(-b * np.sqrt(St))
    epsilon = (Ein + Eim) * R

    sqrt_eps = np.sqrt(epsilon)
    vimp = Cd * wsp * (
        1.0 + uhur * ((1.0 - epsilon) / (epsilon + sqrt_eps * np.tanh(gam) * sqrt_eps))
    ) ** -1

    # Return scalar if scalar was given
    if vimp.ndim == 0 or vimp.size == 1:
        return float(vimp.flat[0])
    return vimp


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------

def PLAnET(
    data: np.ndarray,
    ustar_flag: bool,
    depo_flag: bool,
    params: Optional[ModelParams] = None,
    constants: Optional[ModelConstants] = None,
) -> PLAnETResult:
    """
    Run the PLAnET microbial population-dynamics and flux model.

    Parameters
    ----------
    data : np.ndarray, shape (n, 4) or (n, 5)
        Forcing data matrix.  Columns:

        ======  =============================================================
        Col 0   Temperature (°C)
        Col 1   Pressure (Pa)
        Col 2   Wind speed (m s-1) **or** friction velocity u* (m s-1),
                depending on ``ustar_flag``
        Col 3   Leaf Area Index (LAI)
        Col 4   Wind speed (m s-1) – **required only when** ``ustar_flag=True``
                **and** ``depo_flag=True``
        ======  =============================================================

    ustar_flag : bool
        If ``True``, column 2 is interpreted as friction velocity u*.
        If ``False``, column 2 is wind speed and u* is derived internally
        using the log-wind profile with ``z`` and ``z0`` from
        ``constants``.

    depo_flag : bool
        If ``True``, gravitational settling and impaction/interception
        deposition are computed and included in the net flux.

    params : ModelParams, optional
        Ecophysiological parameters.  If ``None``, the default parameter
        set from the original model formulation is used.

    constants : ModelConstants, optional
        Physical / experimental constants.  If ``None``, defaults are used.

    Returns
    -------
    PLAnETResult
        A dataclass containing all output arrays.  All flux arrays are in
        CFU m-2 s-1; population is in CFU m-2.

    Raises
    ------
    ValueError
        On invalid input shapes or flag combinations.
    RuntimeError
        If an internal population balance cannot be resolved (indicates
        inconsistent input parameters).

    Notes
    -----
    * The model assumes a **half-hourly time step** by default (``d=1800 s``
      in :class:`ModelConstants`).  Change ``constants.d`` for other
      cadences.
    * Starting population is set to ``k_min``, so datasets should ideally
      begin in winter / low-LAI conditions.

    Examples
    --------
    Minimal example with synthetic data:

    >>> import numpy as np
    >>> from planet import PLAnET
    >>> rng = np.random.default_rng(42)
    >>> n = 48  # one day of half-hourly data
    >>> data = np.column_stack([
    ...     rng.uniform(15, 25, n),    # Temperature (°C)
    ...     np.full(n, 101325.0),      # Pressure (Pa)
    ...     rng.uniform(1, 5, n),      # Wind speed (m s-1)
    ...     rng.uniform(0.5, 3.0, n),  # LAI
    ... ])
    >>> result = PLAnET(data, ustar_flag=False, depo_flag=False)
    >>> result.population.shape
    (48,)
    """
    # --- resolve defaults ---
    if params is None:
        params = ModelParams()
    if constants is None:
        constants = ModelConstants()

    p = params
    c_ = constants

    # --- validate input shape ---
    data = np.asarray(data, dtype=float)
    if data.ndim != 2:
        raise ValueError("data must be a 2-D array.")
    n_steps, n_cols = data.shape

    if ustar_flag and depo_flag and n_cols < 5:
        raise ValueError(
            "When ustar_flag=True and depo_flag=True, a 5th column "
            "with wind speed is required."
        )
    if n_cols < 4:
        raise ValueError(
            "data must have at least 4 columns: "
            "[T (°C), P (Pa), wind/u* (m s-1), LAI]."
        )

    # --- unpack forcing ---
    T = data[:, 0]
    P = data[:, 1]
    wspeed = data[:, 2]
    lai_vals = data[:, 3]

    # --- derive u* ---
    if ustar_flag:
        ust = wspeed.copy()
        wsp = data[:, 4] if depo_flag else None
    else:
        ust = 0.4 * wspeed / np.log(c_.z / c_.z0)
        wsp = wspeed if depo_flag else None

    # --- pre-allocate output arrays ---
    pop = np.zeros(n_steps)
    growth = np.zeros(n_steps)
    kmax_out = np.zeros(n_steps)
    removal = np.zeros(n_steps)
    Fd = np.zeros(n_steps)
    Fn = np.zeros(n_steps)
    dieout = np.zeros(n_steps)
    conc = np.zeros(n_steps)
    vg_arr = np.full(n_steps, np.nan)
    vimp_arr = np.full(n_steps, np.nan)
    vdep_arr = np.full(n_steps, np.nan)
    dflag = np.zeros(n_steps, dtype=bool)
    ovflw = np.zeros(n_steps, dtype=bool)
    undflw = np.zeros(n_steps, dtype=bool)

    # Warn about conc being undefined when deposition is off.
    # NOTE: in the original MATLAB, conc was computed inside the depo_flag==1
    # block and left uninitialized otherwise. The model was always used with
    # depo_flag=1 in practice, so this was never triggered. Here we pre-allocate
    # conc to zeros, which is safe but still meaningless — hence the warning.
    if not depo_flag:
        warnings.warn(
            "depo_flag=False: result.conc will be all zeros and should not be "
            "interpreted as background airborne concentration. This matches the "
            "behaviour of the original MATLAB model.",
            UserWarning,
            stacklevel=2,
        )

    # Initial population = k_min
    N0 = p.k_min
    kmax_buffer = p.k_max

    # --- main time loop ---
    for k in range(n_steps):

        # current population (scalar)
        popul = N0 if k == 0 else pop[k - 1]

        # LAI-modulated population cap
        kmax = p.k_min + (kmax_buffer - p.k_min) * lai_vals[k]
        kmax_out[k] = kmax

        # ----------------------------------------------------------------
        # GROWTH  (modified Yin temperature response function)
        # ----------------------------------------------------------------
        if T[k] < p.T_min or T[k] > p.T_max:
            growth[k] = 0.0
        else:
            growth[k] = (
                ((p.T_max - T[k]) / (p.T_max - p.T_opt))
                * ((T[k] - p.T_min) / (p.T_opt - p.T_min))
                ** ((p.T_opt - p.T_min) / (p.T_max - p.T_opt))
            ) * p.c

        # ----------------------------------------------------------------
        # GROSS UPWARD FLUX  (Gompertz-based emission)
        # ----------------------------------------------------------------
        rem_k = (
            p.slp * np.exp(-p.slp2 * np.exp(-p.slp3 * ust[k]))
            * c_.d
            * (popul / kmax)
        )
        removal[k] = max(rem_k, 0.0)  # no negative upward flux

        if np.isnan(removal[k]):
            raise RuntimeError(
                f"removal is NaN at time step k={k}. "
                "Check input parameters and forcing data."
            )

        # ----------------------------------------------------------------
        # GROSS DOWNWARD FLUX  (settling + impaction)
        # ----------------------------------------------------------------
        if depo_flag:
            vg_k = settvel(c_.dia, T[k] + 273.15, P[k])
            vg_arr[k] = vg_k

            if ust[k] > 0.0 and wsp[k] > 0.0:
                vimp_k = slinnmod(wsp[k], ust[k], c_.dia, vg_k, c_.zc, c_.z0)
            else:
                vimp_k = 0.0
            vimp_arr[k] = vimp_k
            vdep_arr[k] = vg_k + vimp_k

            conc[k] = p.lai1 * lai_vals[k] + p.lai2
            # multiply by time-step to get CFU m-2
            Fd[k] = vdep_arr[k] * conc[k] * c_.d
            dflag[k] = True

            # Net flux: negative = outgoing (removes from pop), positive = deposited
            Fn[k] = -removal[k] + Fd[k]
        else:
            Fn[k] = -removal[k]
            Fd[k] = 0.0

        # ----------------------------------------------------------------
        # POPULATION UPDATE
        # ----------------------------------------------------------------
        pop[k] = popul + popul * growth[k] + Fn[k]

        # -- above cap: stunt growth or trigger die-out ---
        if pop[k] > kmax:
            stunted_growth = (kmax - popul - Fn[k]) / popul
            if stunted_growth >= 0.0:
                if growth[k] == 0.0:
                    raise RuntimeError(
                        f"Attempting to stunt growth when growth=0 at k={k}. "
                        "Check model parameters."
                    )
                growth[k] = stunted_growth
                pop[k] = popul + popul * growth[k] + Fn[k]
                dieout[k] = 0.0
            else:
                growth[k] = 0.0
                pop[k] = popul + popul * growth[k] + Fn[k]
                dieout[k] = 0.0
                if pop[k] > kmax:
                    # LAI-driven habitat loss → lateral die-out
                    dieout[k] = pop[k] - kmax
                    pop[k] = popul + popul * growth[k] + Fn[k] - dieout[k]

        # -- below floor: prevent emission, boost growth or allow deposition ---
        elif pop[k] < p.k_min:
            removal[k] = 0.0
            Fn[k] = -removal[k] + Fd[k]

            candidate = popul + popul * growth[k] + Fn[k]

            if candidate >= p.k_min:
                pop[k] = candidate
                dieout[k] = 0.0
                # rare edge: deposition pushes above kmax when LAI is very low
                if pop[k] > kmax:
                    pop[k] = kmax
            elif (p.k_min - popul - Fn[k]) / popul > 0.0:
                # growth boost to reach k_min
                growth[k] = (p.k_min - popul - Fn[k]) / popul
                pop[k] = popul + popul * growth[k] + Fn[k]
                dieout[k] = 0.0
            else:
                raise RuntimeError(
                    f"Cannot resolve population below k_min at k={k}. "
                    "There are likely major issues in input parameters."
                )
        else:
            dieout[k] = 0.0

        # ----------------------------------------------------------------
        # OVERFLOW / UNDERFLOW SANITY CHECKS
        # ----------------------------------------------------------------
        if pop[k] > kmax:
            rel_err = abs(kmax - pop[k]) / min(abs(kmax), abs(pop[k]))
            if rel_err >= 1e-4:
                warnings.warn(
                    f"Population overflow at time step k={k} "
                    f"(pop={pop[k]:.3e}, kmax={kmax:.3e}).",
                    RuntimeWarning,
                    stacklevel=2,
                )
                ovflw[k] = True

        elif pop[k] < p.k_min:
            rel_err = abs(p.k_min - pop[k]) / min(abs(p.k_min), abs(pop[k]))
            if rel_err >= 1e-4:
                warnings.warn(
                    f"Population underflow at time step k={k} "
                    f"(pop={pop[k]:.3e}, k_min={p.k_min:.3e}).",
                    RuntimeWarning,
                    stacklevel=2,
                )
                undflw[k] = True

    # --- convert integrated fluxes back to rates (CFU m-2 s-1) ---
    removal_rate = removal / c_.d          # gross out flux
    Fd_rate = Fd / c_.d                    # gross in flux
    # sign convention: positive = upward / outgoing
    Fn_rate = -1.0 * (Fn / c_.d)

    return PLAnETResult(
        population=pop,
        growth=growth,
        k_max=kmax_out,
        gross_out=removal_rate,
        gross_in=Fd_rate,
        conc=conc,
        net_flux=Fn_rate,
        vg=vg_arr,
        vimp=vimp_arr,
        vdep=vdep_arr,
        dflag=dflag,
        dieout=dieout,
        overflow=ovflw,
        underflow=undflw,
    )
