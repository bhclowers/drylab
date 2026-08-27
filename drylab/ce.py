"""Capillary zone electrophoresis: 1D electromigration on a Chebyshev grid.

PROVENANCE AND LICENCE
----------------------
This module is a RESTRUCTURED DERIVATIVE of SPYCE 2.0 (Prateek Gupta and
Supreet Singh Bahga, IIT Delhi), described in Electrophoresis 2021, DOI
10.1002/elps.202100279 and 10.1002/elps.202000259. The numerical scheme —
Chebyshev pseudo-spectral differentiation via FFT, the arcsine grid map of
Kosloff & Tal-Ezer, Hou-Li spectral filtering, the local-equilibrium pH
solve, and adaptive Runge-Kutta stepping — is theirs.

SPYCE ships without a licence file. Prof. Bahga granted permission by
email on 2026-08-05: "Feel free to use the code however you wish, as long
as it remains available to the community for free."

THAT GRANT CARRIES AN OBLIGATION: this module, and anything derived from
it, must remain freely available to the community. drylab's CC BY-NC-SA
licence satisfies it; putting this code behind a paywall would not, and
would breach the terms under which it exists. See NOTICE.md, which records
the grant in full — a downstream user cannot otherwise discover it, since
the permission is an email rather than a public licence on SPYCE itself.

Not from SPYCE: the electroosmotic-flow model (SPYCE models transport
explicitly WITHOUT bulk flow), the Joule-heating calculations, the
composition validation and the ion library are drylab's own.

Scope: CZE only (ruled 2026-08-05, "CZE first, then ITP/FASS"). The moving
mesh is deliberately NOT ported — it exists to resolve the sharp
self-sharpening fronts of ITP, whereas CZE zones on a near-uniform arcsine
grid are smooth. Adding it is the ITP work, not this.

REFERENCES
----------
Cite these when publishing work that uses this module (they are the
method; drylab is the restructuring):

- Gupta, P.; Bahga, S. S. *Electrophoresis* **2021**, *42*, 890-898.
  https://doi.org/10.1002/elps.202000259
- Bahga, S. S.; Gupta, P. Electrophoresis simulations using Chebyshev
  pseudo-spectral method on a moving mesh. *Electrophoresis* **2021**,
  *42*, 2321-2328. https://doi.org/10.1002/elps.202100279

Recorded exactly as in NOTICE.md (the first paper's title is not recorded
there and doi.org is unreachable from the build sandbox, so it is cited
by DOI rather than a possibly-misremembered title). No public repository
for SPYCE could be located (checked 2026-08-26): the papers and
NOTICE.md's recorded permission are the complete provenance trail.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Mapping, Sequence

import numpy as np

#: Gas constant, J/(mol K), and Faraday constant, C/mol.
R_GAS: float = 8.314
FARADAY: float = 96485.0
#: Ionic product of water in (mol/L)^2, the unit acid-base constants are
#: defined in. THE EQUILIBRIUM BLOCK WORKS IN mol/L WHILE TRANSPORT WORKS
#: IN mol/m^3: Ka = 10^-pKa is a mol/L quantity, so mixing it with an SI
#: hydronium concentration is wrong by exactly 1000 per proton. SPYCE's
#: own header carries the same warning. Conversions happen only at the
#: boundaries of the equilibrium functions, marked LITRES below.
KW_MOLAR: float = 1.0e-14
#: mol/m^3 per mol/L.
M3_PER_L: float = 1000.0
#: Courant-style safety factors for the step-size cap. Named, because they
#: are the difference between a march that runs and one that silently takes
#: ten steps: the RKF45 error estimate does not by itself keep an explicit
#: scheme inside its stability region.
CFL_MIGRATION: float = 0.2
CFL_DIFFUSION: float = 0.2

#: Hydronium and hydroxide mobilities, m^2/(V s).
MU_H: float = 362.5e-9
MU_OH: float = -205.0e-9


@dataclass(frozen=True)
class CESpecies:
    """One weak-electrolyte constituent.

    ``valences``, ``mobilities`` and ``p_ka`` are parallel per ionic form.
    Mobilities are SIGNED, m^2/(V s), as the sign carries the direction of
    migration and dropping it silently reverses an ion.
    """

    name: str
    valences: tuple[int, ...]
    mobilities: tuple[float, ...]
    p_ka: tuple[float, ...]

    def __post_init__(self) -> None:
        n = len(self.valences)
        if not (len(self.mobilities) == len(self.p_ka) == n):
            raise ValueError(
                f"{self.name}: valences, mobilities and p_ka must be the same "
                f"length, got {n}, {len(self.mobilities)}, {len(self.p_ka)}")
        if n == 0:
            raise ValueError(f"{self.name}: needs at least one ionic form")
        if 0 in self.valences:
            raise ValueError(
                f"{self.name}: valence 0 is implied by the neutral form and "
                f"must not be listed explicitly")


@dataclass(frozen=True)
class CEConditions:
    """Capillary, electrical and grid settings for one run."""

    length_m: float = 30.0e-3
    #: Applied voltage, V. This is what an operator sets on a CE instrument
    #: and what appears in a published method, so it is the primary control.
    #: Constant-CURRENT mode is the alternative the instrument also offers;
    #: pass current_a instead and leave voltage_v as None. Exactly one must
    #: be given -- accepting both would let them silently disagree.
    voltage_v: float | None = 3000.0
    current_a: float | None = None
    diameter_m: float = 50.0e-6
    temperature_k: float = 298.0
    n_points: int = 257
    t_final_s: float = 75.0
    #: Arcsine-map parameter; -> 1 gives a near-uniform physical grid.
    beta: float = 1.0 - 1.0e-5
    #: Electroosmotic mobility, m^2/(V s). Positive drives bulk flow toward
    #: the cathode, which is the usual direction for bare fused silica above
    #: about pH 4 (deprotonated silanols leave a negative wall, so the
    #: mobile counter-ion layer is cationic).
    #:
    #: THIS IS BEYOND THE ORACLE. SPYCE models transport explicitly "in the
    #: absence of bulk fluid flow due to pressure gradients and
    #: electroosmotic slip", so compare_ce.py can only validate the
    #: eof_mobility = 0 case. EOF is added here because without it anions
    #: and cations can never reach the same detector, which is the defining
    #: feature of a real CZE experiment; it is validated instead by the
    #: Galilean-shift invariant in compare_ce.py.
    eof_mobility: float = 0.0
    #: RKF45 relative tolerance. SPYCE's default is 1e-3; see the module
    #: docstring in validation/ for why a comparison must not assert tighter.
    tolerance: float = 1.0e-3
    max_steps: int = 200_000
    save_every: int = 10

    @property
    def area_m2(self) -> float:
        return 0.25 * math.pi * self.diameter_m ** 2

    def __post_init__(self) -> None:
        if (self.voltage_v is None) == (self.current_a is None):
            raise ValueError(
                "give exactly one of voltage_v (constant-voltage mode) or "
                "current_a (constant-current mode); passing both lets them "
                "disagree, passing neither leaves the field undefined")

    @property
    def field_v_per_m(self) -> float | None:
        """Nominal field, V/m. None in constant-current mode, where the
        field follows the local conductivity instead of being imposed."""
        if self.voltage_v is None:
            return None
        return self.voltage_v / self.length_m

    def current_density_for(self, conductivity: float) -> float:
        """Current density, A/m^2.

        In constant-voltage mode this depends on the electrolyte: j = sigma*E.
        The solver therefore has to ask for it once the conductivity of the
        initial state is known, rather than treating it as a fixed input.
        """
        if self.current_a is not None:
            return self.current_a / self.area_m2
        return conductivity * self.field_v_per_m


@dataclass(frozen=True)
class CERun:
    """Space-time field returned by one march.

    Holding the WHOLE field is what makes the front-end's time slider free:
    the march happens once, and scrubbing re-slices this rather than
    re-solving (ruled 2026-08-05).
    """

    times_s: np.ndarray                 # (n_saved,)
    position_m: np.ndarray              # (n_points,)
    concentrations: np.ndarray          # (n_species, n_points, n_saved), mol/m^3
    hydronium: np.ndarray               # (n_points, n_saved), mol/m^3
    conductivity: np.ndarray            # (n_points, n_saved), S/m
    species_names: tuple[str, ...]
    conditions: CEConditions
    n_steps: int = 0
    current_density: float = 0.0

    @property
    def position_mm(self) -> np.ndarray:
        return self.position_m * 1000.0

    def concentrations_mM(self) -> np.ndarray:
        """mol/m^3 -> mM. Numerically 1:1, named so the unit is explicit."""
        return self.concentrations

    def detector_trace(self, position_mm: float) -> tuple[int, np.ndarray]:
        """(node index, concentrations at that node over time)."""
        node = int(np.argmin(np.abs(self.position_mm - position_mm)))
        return node, self.concentrations[:, node, :]


def _cheb_grid(n_points: int) -> np.ndarray:
    """Chebyshev-Gauss-Lobatto points, xi = cos(j pi / N), descending."""
    n = n_points - 1
    return np.cos(np.arange(n_points) * math.pi / n)


def _cheb_diff_xi(f: np.ndarray, n_points: int) -> np.ndarray:
    """d f / d xi on the Chebyshev grid, along the last axis.

    Trefethen's ``chebfft`` (Spectral Methods in MATLAB, Program 18),
    INCLUDING THE ENDPOINT FORMULAE. The interior points divide the
    theta-derivative by -sqrt(1-xi^2), which vanishes at xi = +-1; the
    endpoints therefore need closed forms built from the transform
    coefficients directly.

    Omitting them (as an earlier version did, clamping the singular divisor
    instead) made the domain behave as PERIODIC: a zone reaching one end
    reappeared at the other, and the integrated mass jumped by more than an
    order of magnitude. Bahga & Gupta flag this explicitly -- the physical
    derivative is computed "with special formulae for the endpoints".
    """
    n = n_points - 1
    # Even extension in theta so the FFT sees a periodic function.
    ext = np.concatenate([f, f[..., -2:0:-1]], axis=-1)
    coeffs = np.real(np.fft.fft(ext, axis=-1))
    k = np.concatenate([np.arange(n), [0], np.arange(1 - n, 0)])
    d_theta = np.real(np.fft.ifft(1j * k * coeffs, axis=-1))

    xi = _cheb_grid(n_points)
    out = np.zeros_like(f, dtype=float)
    interior = slice(1, n)
    out[..., interior] = (-d_theta[..., interior]
                          / np.sqrt(1.0 - xi[interior] ** 2))

    # Endpoints: sum over the Chebyshev coefficients.
    idx = np.arange(n)
    w = coeffs[..., :n] * (idx ** 2)
    out[..., 0] = w.sum(axis=-1) / n + 0.5 * n * coeffs[..., n]
    alt = ((-1.0) ** (idx + 1)) * (idx ** 2)
    out[..., n] = ((coeffs[..., :n] * alt).sum(axis=-1) / n
                   + 0.5 * ((-1.0) ** (n + 1)) * n * coeffs[..., n])
    return out


def _spectral_filter(f: np.ndarray, n_points: int) -> np.ndarray:
    """Hou-Li Fourier smoothing, applied to the state each accepted step.

    The nonlinear flux term multiplies truncated Chebyshev series, which
    aliases energy into the highest resolvable wavenumbers. Left
    unattenuated that energy grows until the solution is destroyed: a zone
    reaching the end of the capillary produced a peak reappearing at the
    far end with the integrated mass up more than an order of magnitude.
    Correct endpoint differentiation alone did NOT fix it -- the aliasing
    is a separate mechanism and needs this filter, exactly as SPYCE
    applies it.

    Weighting is exp(-36 (k/k_max)^36) (Hou & Li 2007): essentially unity
    across the resolved band and a very sharp cutoff at the top, so it
    removes the aliased tail without smearing the physical solution.
    """
    n = n_points - 1
    ext = np.concatenate([f, f[..., -2:0:-1]], axis=-1)
    m = ext.shape[-1]
    freq = np.fft.fftfreq(m) * 2.0 * n
    weight = np.exp(-36.0 * (np.abs(freq) / float(n)) ** 36.0)
    out = np.real(np.fft.ifft(np.fft.fft(ext, axis=-1) * weight, axis=-1))
    return out[..., :n_points]


def _equilibrium_tables(species: Sequence[CESpecies], temperature_k: float):
    """Per-species ionisation tables, ordered by ascending valence.

    Returns (L, mu, z, D) each (n_species, max_forms), where L are the
    cumulative acid-dissociation products that convert total concentration
    and hydronium into the fraction in each ionic form.
    """
    max_forms = max(len(s.valences) for s in species) + 1
    n = len(species)
    L = np.zeros((n, max_forms))
    mu = np.zeros((n, max_forms))
    z = np.zeros((n, max_forms))
    D = np.zeros((n, max_forms))
    for i, sp in enumerate(species):
        zl = np.asarray(sp.valences, dtype=int)
        ml = np.asarray(sp.mobilities, dtype=float)
        kl = 10.0 ** (-np.asarray(sp.p_ka, dtype=float))
        # Nernst-Einstein. z=0 would divide by zero, which is why the
        # neutral form is inserted separately below rather than listed.
        dl = R_GAS * temperature_k * np.abs(ml) / (FARADAY * np.abs(zl))
        order = np.argsort(zl)
        zl, ml, kl, dl = zl[order], ml[order], kl[order], dl[order]
        neg, pos = zl < 0, zl > 0
        ml = np.concatenate([ml[neg], [0.0], ml[pos]])
        kl = np.concatenate([kl[neg], [1.0], kl[pos]])
        dl = np.concatenate([dl[neg], [float(np.mean(dl))], dl[pos]])
        zl = np.concatenate([zl[neg], [0], zl[pos]])
        n_forms = len(zl)
        z[i, :n_forms], mu[i, :n_forms] = zl, ml
        D[i, :n_forms] = dl
        lowest = int(np.min(zl))
        for zz in zl:
            idx = int(zz) - lowest
            if zz < 0:
                L[i, idx] = np.prod(kl[idx:-lowest])
            elif zz > 0:
                L[i, idx] = 1.0 / np.prod(kl[-lowest:idx + 1])
            else:
                L[i, idx] = 1.0
    return L, mu, z, D, max_forms


def _solve_hydronium(c_tot, L, z, max_forms, c_h_guess, kw=KW_MOLAR,
                     iterations: int = 40, tol: float = 1e-12):
    """Vectorised Newton for cH at EVERY node simultaneously.

    The nodes are independent within a step, which is what makes this a
    single array operation instead of a Python loop over the grid — the
    difference between an interactive model and an unusable one.
    """
    # LITRES: work in mol/L here; c_tot stays mol/m^3 and is converted once.
    c_h = np.array(c_h_guess, dtype=float, copy=True) / M3_PER_L
    c_tot = np.asarray(c_tot, dtype=float) / M3_PER_L
    powers = np.arange(max_forms)
    for _ in range(iterations):
        # (forms, nodes) matrix of cH^k
        ch_pow = c_h[None, :] ** powers[:, None]
        # per species: numerator L*cH^k, denominator sum over forms
        num = L[:, :, None] * ch_pow[None, :, :]
        denom = num.sum(axis=1)
        frac = num / denom[:, None, :]
        charge = (z[:, :, None] * frac * c_tot[:, None, :]).sum(axis=(0, 1))
        g = charge + c_h - kw / c_h
        # derivative via the same tables
        dfrac_num = (powers[None, :, None] * num) / np.maximum(c_h[None, None, :], 1e-300)
        ddenom = dfrac_num.sum(axis=1)
        dfrac = (dfrac_num * denom[:, None, :] - num * ddenom[:, None, :]) / denom[:, None, :] ** 2
        dcharge = (z[:, :, None] * dfrac * c_tot[:, None, :]).sum(axis=(0, 1))
        dg = dcharge + 1.0 + kw / c_h ** 2
        step = g / dg
        c_h = np.maximum(c_h - step, 1e-14)
        if np.max(np.abs(step)) < tol * np.max(c_h):
            break
    return c_h * M3_PER_L        # back to mol/m^3 for the transport terms


def _spatial_properties(c_tot, c_h, L, mu, z, D, max_forms):
    """Effective mobility, effective diffusivity and conductivity per node."""
    powers = np.arange(max_forms)
    ch_pow = (c_h[None, :] / M3_PER_L) ** powers[:, None]   # LITRES
    num = L[:, :, None] * ch_pow[None, :, :]
    frac = num / num.sum(axis=1)[:, None, :]
    mu_eff = (mu[:, :, None] * frac).sum(axis=1)
    d_eff = (D[:, :, None] * frac).sum(axis=1)
    # Charge-weighted diffusivity, sum_z z*D_z*frac_z. This is what carries
    # the DIFFUSION POTENTIAL: species with different ionic diffusivities
    # separate charge slightly, adding a field on top of the ohmic drop
    # (eq. 2 of Bahga & Gupta 2021, eq. 7 of Gas & Bravenec 2021). Dropping
    # it is not a small tidy-up -- it is the term responsible for part of
    # electromigration dispersion, which is most of what CZE teaching is about.
    zd_eff = (z[:, :, None] * D[:, :, None] * frac).sum(axis=1)
    sigma = FARADAY * (
        (np.abs(z)[:, :, None] * np.abs(mu)[:, :, None] * frac
         * c_tot[:, None, :]).sum(axis=(0, 1))
        + (MU_H * c_h + abs(MU_OH) * KW_MOLAR * M3_PER_L**2 / c_h)
    )
    return mu_eff, d_eff, sigma, zd_eff


def _rhs(c_tot, x_xi, L, mu, z, D, max_forms, cond, c_h_guess, n_points,
         j):
    """d c / d t for all species, on the Chebyshev grid.

    Physical derivatives come from the theta-derivative by the chain rule
    d/dx = (1/x_xi) * (-1/sqrt(1-xi^2)) * d/dtheta, with the endpoint
    factor folded into ``x_xi`` by the caller.
    """
    c_h = _solve_hydronium(c_tot, L, z, max_forms, c_h_guess)
    mu_eff, d_eff, sigma, zd_eff = _spatial_properties(
        c_tot, c_h, L, mu, z, D, max_forms)
    # Gradients of every total concentration, once.
    dc_dx = _cheb_diff_xi(c_tot, n_points) / x_xi
    # Diffusive current density: F * sum_i z_i D_i dc_i/dx, plus the
    # hydronium and hydroxide contributions.
    d_h = R_GAS * cond.temperature_k * MU_H / FARADAY
    d_oh = R_GAS * cond.temperature_k * abs(MU_OH) / FARADAY
    c_oh = KW_MOLAR * M3_PER_L ** 2 / c_h
    dch_dx = _cheb_diff_xi(c_h, n_points) / x_xi
    dcoh_dx = _cheb_diff_xi(c_oh, n_points) / x_xi
    i_diff = FARADAY * ((zd_eff * dc_dx).sum(axis=0)
                        + d_h * dch_dx - d_oh * dcoh_dx)
    e_field = (j + i_diff) / sigma
    # EOF is PLUG flow: the same bulk velocity for every species, charged or
    # not, added to each ion's own electrophoretic velocity. That is why the
    # observed ("apparent") mobility is mu_ep + mu_eof, and why a neutral
    # marker reports mu_eof directly.
    total_flux = (mu_eff + cond.eof_mobility) * c_tot * e_field - d_eff * dc_dx
    dcdt = -_cheb_diff_xi(total_flux, n_points) / x_xi
    # OPEN-BOUNDARY CONDITION. The reservoirs at each end hold their
    # composition fixed, so dc/dt = 0 there and a zone that reaches the end
    # LEAVES the domain. Omitting this (as an earlier version did) makes
    # analytes pile up against the wall instead of eluting, which shows up
    # as every peak arriving simultaneously at the final time step.
    dcdt[:, 0] = 0.0
    dcdt[:, -1] = 0.0
    return dcdt, c_h, sigma, mu_eff, d_eff, e_field


def simulate_cze(species: Sequence[CESpecies],
                 initial_concentrations: np.ndarray,
                 conditions: CEConditions | None = None) -> CERun:
    """March a CZE separation and return the whole space-time field.

    ``initial_concentrations`` is (n_species, n_points) in mol/m^3 on the
    physical grid returned by :func:`grid_positions`.
    """
    cond = conditions or CEConditions()
    n = cond.n_points
    c = np.array(initial_concentrations, dtype=float, copy=True)
    if c.shape != (len(species), n):
        raise ValueError(
            f"initial_concentrations must be ({len(species)}, {n}), got "
            f"{c.shape}; build it on grid_positions(conditions)")
    L, mu, z, D, max_forms = _equilibrium_tables(species, cond.temperature_k)

    xi = _cheb_grid(n)
    x = grid_positions(cond)
    # dx/dxi for the arcsine map, and the -sqrt(1-xi^2) from d/dtheta.
    b = cond.beta
    dx_dxi = (cond.length_m / 2.0) * b / (np.arcsin(b) * np.sqrt(1.0 - (b * xi) ** 2))
    # _cheb_diff_xi returns d/dxi, so the only remaining factor is the map
    # Jacobian. The clamped -sqrt(1-xi^2) that used to live here was the
    # singular divisor at the endpoints; it is now handled inside the
    # differentiation by Trefethen's endpoint formulae.
    x_xi = dx_dxi

    # In constant-voltage mode the current density follows from the
    # electrolyte's conductivity, so it is established once from the initial
    # state. A real instrument in constant-voltage mode does let the current
    # drift as zones move; holding it fixed here is a stated simplification,
    # not an oversight, and it is exactly what constant-CURRENT mode does
    # anyway.
    c_h = np.full(n, 1e-4)
    _c_h0 = _solve_hydronium(c, L, z, max_forms, c_h)
    _, _, _sigma0, _ = _spatial_properties(c, _c_h0, L, mu, z, D, max_forms)
    j_applied = cond.current_density_for(float(np.median(_sigma0)))
    t = 0.0
    dt = cond.t_final_s / 5000.0
    dt_cap = dt
    times, saved_c, saved_h, saved_s = [0.0], [c.copy()], [c_h.copy()], None
    steps = 0
    # Cash-Karp / RKF45 coefficients.
    b5 = np.array([37/378, 0, 250/621, 125/594, 0, 512/1771])
    b4 = np.array([2825/27648, 0, 18575/48384, 13525/55296, 277/14336, 1/4])
    a = [[], [1/5], [3/40, 9/40], [3/10, -9/10, 6/5],
         [-11/54, 5/2, -70/27, 35/27],
         [1631/55296, 175/512, 575/13824, 44275/110592, 253/4096]]
    sigma_last = None
    while t < cond.t_final_s and steps < cond.max_steps:
        steps += 1
        if t + dt > cond.t_final_s:
            dt = cond.t_final_s - t
        ks = []
        for i in range(6):
            ci = c + dt * sum(a[i][jj] * ks[jj] for jj in range(i)) if i else c
            k, c_h_new, sigma, mu_eff, d_eff, e_field = _rhs(
                ci, x_xi, L, mu, z, D, max_forms, cond, c_h, n, j_applied)
            ks.append(k)
            if i == 0:
                c_h, sigma_last = c_h_new, sigma
                # STABILITY CAP, recomputed each step. Error control alone
                # let dt grow without bound here (10 steps for 20 s, where
                # the reference takes hundreds): the local error estimate
                # can look small while the scheme is already past its
                # stability limit. These are the physical limits -- how far
                # a band may migrate, and how far it may diffuse, in one
                # step relative to the finest grid spacing.
                dx_min = float(np.min(np.abs(np.diff(x))))
                v_max = float(np.max(np.abs(mu_eff * e_field))) + 1e-30
                d_max = float(np.max(np.abs(d_eff))) + 1e-30
                dt_cap = min(CFL_MIGRATION * dx_min / v_max,
                             CFL_DIFFUSION * dx_min ** 2 / d_max)
        k = np.array(ks)
        c5 = c + dt * np.tensordot(b5, k, axes=(0, 0))
        c4 = c + dt * np.tensordot(b4, k, axes=(0, 0))
        scale = np.maximum(np.abs(c5), 1e-6 * np.max(np.abs(c5)))
        err = float(np.max(np.abs(c5 - c4) / scale))
        if err <= cond.tolerance or dt <= 1e-12:
            t += dt
            # Filter BEFORE clipping: clipping introduces a kink, and
            # filtering that kink would smear it across the domain.
            c = np.maximum(_spectral_filter(c5, n), 0.0)
            if steps % cond.save_every == 0:
                times.append(t); saved_c.append(c.copy()); saved_h.append(c_h.copy())
        dt *= min(4.0, max(0.2, 0.9 * (cond.tolerance / max(err, 1e-16)) ** 0.2))
        dt = min(dt, dt_cap)
    if steps >= cond.max_steps:
        raise RuntimeError(
            f"CZE march hit the {cond.max_steps}-step ceiling at t={t:.4g} s "
            f"of {cond.t_final_s} s; the step controller is not converging")
    if times[-1] < cond.t_final_s:
        times.append(t); saved_c.append(c.copy()); saved_h.append(c_h.copy())
    conc = np.stack(saved_c, axis=-1)
    hyd = np.stack(saved_h, axis=-1)
    # Conductivity at EVERY saved time, not the last one broadcast: the
    # conductivity profile is a headline output for CE (it is what a
    # conductivity detector sees), so freezing it would be a silent lie in
    # exactly the plot a user would trust.
    sigma_field = np.stack(
        [_spatial_properties(conc[:, :, k], hyd[:, k], L, mu, z, D,
                             max_forms)[2]
         for k in range(conc.shape[-1])], axis=-1)
    return CERun(times_s=np.array(times), position_m=x, concentrations=conc,
                 hydronium=hyd, conductivity=sigma_field,
                 species_names=tuple(s.name for s in species),
                 conditions=cond, n_steps=steps,
                 current_density=j_applied)


def grid_positions(conditions: CEConditions) -> np.ndarray:
    """Physical node positions, m, under the arcsine map (Kosloff/Tal-Ezer)."""
    xi = _cheb_grid(conditions.n_points)
    b = conditions.beta
    return (conditions.length_m / 2.0) * (1.0 + np.arcsin(b * xi) / np.arcsin(b))


#: Curated ion library for the composition editor.
#:
#: Each entry is (valence, mobility m^2/(V s), pKa, note). Mobilities are
#: limiting aqueous values at 25 degC; pKa values are for the acid form.
#: Sources are the standard compilations used by every simulator in this
#: field (Hirokawa's tables and the values shipped in SPYCE's own sample
#: inputs), and they are here so a student picks a REAL ion rather than
#: inventing a plausible-looking number.
#:
#: NOTE ON THE pKa CONVENTION, which is the single easiest thing to get
#: wrong: an ion that is permanently charged needs a pKa FAR from the
#: working pH on the side that keeps it ionised. For a CATION that means a
#: HIGH pKa (its conjugate base never forms); for an ANION a LOW pKa.
#: Entering a low pKa for a permanent cation leaves it neutral and
#: motionless, which looks like a broken simulation rather than a data
#: error -- validate_composition() checks for exactly this.
CE_ION_LIBRARY: Mapping[str, tuple[int, float, float, str]] = MappingProxyType({
    # Permanently charged cations: migration order follows mobility alone.
    "potassium K+":   (1,  76.2e-9, 14.0, "fully ionised at any pH"),
    "sodium Na+":     (1,  51.9e-9, 14.0, "fully ionised at any pH"),
    "lithium Li+":    (1,  40.1e-9, 14.0, "fully ionised at any pH"),
    "ammonium NH4+":  (1,  76.1e-9,  9.25, "weak acid above pH 9"),
    # Permanently charged anions.
    "chloride Cl-":   (-1, -79.1e-9, -2.0, "fully ionised at any pH"),
    "sulfate SO4^2-": (-2, -82.9e-9,  1.99, "second proton, pKa2"),
    "nitrate NO3-":   (-1, -74.1e-9, -1.3, "fully ionised at any pH"),
    # Weak acids: effective mobility depends strongly on pH.
    "acetate":        (-1, -42.4e-9,  4.756, "classic BGE co-ion"),
    "benzoate":       (-1, -33.6e-9,  4.20, "UV-absorbing BGE co-ion"),
    "HEPES":          (-1, -21.8e-9,  7.5,  "biological buffer"),
    "MES":            (-1, -26.8e-9,  6.15, "biological buffer"),
    # Weak bases.
    "Tris":           (1,   29.5e-9,  8.076, "classic BGE counter-ion"),
    "imidazole":      (1,   52.0e-9,  7.05, "BGE counter-ion"),
    "pyridine":       (1,   30.0e-9,  5.16, "SPYCE sample analyte"),
    "aniline":        (1,   32.5e-9,  4.80, "SPYCE sample analyte"),
    "histidine":      (1,   29.6e-9,  6.04, "amphoteric; cationic form"),
})


def species_from_library(name: str) -> CESpecies:
    """Build a :class:`CESpecies` from the curated library."""
    try:
        valence, mobility, p_ka, _ = CE_ION_LIBRARY[name]
    except KeyError:
        raise KeyError(
            f"unknown ion {name!r}; known ions: {sorted(CE_ION_LIBRARY)}"
        ) from None
    return CESpecies(name, (valence,), (mobility,), (p_ka,))


def validate_composition(rows: Sequence[dict], working_ph: float = 7.0
                         ) -> tuple[list[str], list[str]]:
    """Check a composition table. Returns (errors, warnings).

    ERRORS block the run; WARNINGS are things that will produce a valid but
    surprising result, and the caller shows them without stopping.
    """
    errors: list[str] = []
    warnings: list[str] = []

    if not rows:
        errors.append("The composition is empty. Add at least a background "
                      "electrolyte and one sample component.")
        return errors, warnings

    names = [r["name"] for r in rows]
    dupes = sorted({n for n in names if names.count(n) > 1})
    if dupes:
        errors.append(
            "Two rows share the name " + ", ".join(repr(d) for d in dupes)
            + ". Give each component a distinct name.")

    bge = [r for r in rows if r["role"] == "BGE"]
    sample = [r for r in rows if r["role"] == "Sample"]
    if not bge:
        errors.append(
            "No background electrolyte. At least one BGE component is "
            "needed to carry the current.")
    if not sample:
        errors.append("No sample components, so there is nothing to separate.")

    # Charge balance: a BGE of co-ions only cannot be electroneutral.
    if bge and all(r["valence"] > 0 for r in bge):
        errors.append("The background electrolyte contains only cations; it "
                      "needs a counter-ion to be electroneutral.")
    if bge and all(r["valence"] < 0 for r in bge):
        errors.append("The background electrolyte contains only anions; it "
                      "needs a counter-ion to be electroneutral.")

    for r in rows:
        if r["concentration_mM"] <= 0.0:
            errors.append(f"{r['name']}: concentration must be positive.")
        if r["valence"] == 0:
            errors.append(f"{r['name']}: a neutral species does not migrate; "
                          f"give it a charge or remove it.")
        # The pKa-sign trap.
        if r["valence"] > 0 and r["p_ka"] < working_ph - 1.0:
            warnings.append(
                f"{r['name']} is a cation with pKa {r['p_ka']:g}, below the "
                f"working pH, so it will be mostly NEUTRAL and will barely "
                f"move. Permanently charged cations need a high pKa (K+ uses "
                f"14).")
        if r["valence"] < 0 and r["p_ka"] > working_ph + 1.0:
            warnings.append(
                f"{r['name']} is an anion with pKa {r['p_ka']:g}, above the "
                f"working pH, so it will be mostly protonated and will barely "
                f"move.")
        if r["role"] == "Sample" and r["concentration_mM"] > 0.1 * max(
                (b["concentration_mM"] for b in bge), default=1.0):
            warnings.append(
                f"{r['name']} is more than 10% of the BGE concentration. "
                f"Real CZE keeps the sample dilute; at this level the zone "
                f"distorts its own field (electromigration dispersion).")

    return errors, warnings


#: Thermal conductivity of dilute aqueous buffer, W/(m K), at ~25 degC.
BUFFER_THERMAL_CONDUCTIVITY: float = 0.60

#: Practical limits used to flag a thermally unrealistic run. Power per
#: unit length above roughly 1 W/m is where forced-air CE instruments stop
#: coping, and a radial dT above about 1.5 K measurably broadens peaks
#: because viscosity, and therefore mobility, varies across the bore.
#: These are guidance thresholds, NOT sharp physical boundaries.
JOULE_POWER_LIMIT_W_PER_M: float = 1.0
JOULE_DELTA_T_LIMIT_K: float = 1.5


def joule_power_per_length(conductivity: float, field: float,
                           diameter_m: float) -> float:
    """Ohmic power dissipated per unit capillary length, W/m.

    P/L = sigma * E^2 * A. This is the number a CE method is judged on,
    because it is what the instrument's cooling has to remove.
    """
    area = 0.25 * math.pi * diameter_m ** 2
    return conductivity * field * field * area


def joule_radial_delta_t(conductivity: float, field: float,
                         diameter_m: float,
                         thermal_conductivity: float
                         = BUFFER_THERMAL_CONDUCTIVITY) -> float:
    """Centre-to-wall temperature difference inside the bore, K.

    Steady conduction with uniform generation q = sigma*E^2 in a cylinder
    gives dT = q r^2 / (4 k). This is the difference ACROSS the liquid
    only; the wall and any outside cooling add further rise, so this is a
    lower bound on the real thermal gradient.

    It matters because viscosity falls about 2% per K, so mobility varies
    across the bore, the flow profile is no longer plug, and peaks broaden
    for a reason that has nothing to do with diffusion. Radius enters
    SQUARED, which is why capillary electrophoresis uses capillaries: the
    same field in a 5 mm tube would be unusable.
    """
    q = conductivity * field * field
    radius = 0.5 * diameter_m
    return q * radius * radius / (4.0 * thermal_conductivity)


def joule_report(conductivity: float, field: float, diameter_m: float
                 ) -> tuple[float, float, list[str]]:
    """(power per length, radial dT, warnings) for a set of conditions."""
    power = joule_power_per_length(conductivity, field, diameter_m)
    delta_t = joule_radial_delta_t(conductivity, field, diameter_m)
    warnings: list[str] = []
    if power > JOULE_POWER_LIMIT_W_PER_M:
        warnings.append(
            f"Joule heating is {power:.2f} W/m, above the ~"
            f"{JOULE_POWER_LIMIT_W_PER_M:g} W/m a typical air-cooled "
            f"instrument can remove. A real run would show a rising "
            f"baseline, drifting migration times, and possibly boiling.")
    if delta_t > JOULE_DELTA_T_LIMIT_K:
        warnings.append(
            f"The centre of the capillary would sit about {delta_t:.1f} K "
            f"above the wall. Viscosity falls ~2% per K, so mobility varies "
            f"across the bore and peaks broaden beyond what diffusion alone "
            f"predicts. THIS MODEL ASSUMES A UNIFORM TEMPERATURE and does "
            f"not simulate that broadening.")
    return power, delta_t, warnings
