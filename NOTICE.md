# Third-party provenance

## SPYCE — the capillary-electrophoresis engine

`drylab/ce.py` is a restructured derivative of **SPYCE 2.0** by Prateek
Gupta and Supreet Singh Bahga (Indian Institute of Technology Delhi),
described in:

- Gupta, P.; Bahga, S. S. *Electrophoresis* **2021**, 42, 890–898.
  DOI 10.1002/elps.202000259
- Bahga, S. S.; Gupta, P. *Electrophoresis* **2021**, 42, 2321–2328.
  Electrophoresis simulations using Chebyshev pseudo-spectral method on a
  moving mesh. DOI 10.1002/elps.202100279

The numerical scheme — Chebyshev pseudo-spectral differentiation via FFT,
the arcsine grid map of Kosloff & Tal-Ezer, Hou–Li spectral filtering, the
local-equilibrium pH solve, and adaptive Runge–Kutta stepping — is theirs.

### Permission

SPYCE 2.0 is distributed without a licence file. Prof. Bahga granted
permission by email on 2026-08-05, quoted here in full so the terms travel
with the code:

> Thank you for showing interest in our work. Feel free to use the code
> however you wish, as long as it remains available to the community for
> free.

**This grant carries an obligation.** drylab's CE module, and anything
derived from it, must remain freely available to the community. drylab is
released under CC BY-NC-SA 3.0 US, which satisfies that condition; a
future relicensing that put the CE module behind a paywall would NOT, and
would breach the terms under which this code exists.

### Notes for anyone building on this

- The permission is an email from the corresponding author, not a public
  licence on SPYCE itself. It is recorded here because a downstream user
  cannot otherwise discover it. If you need a firmer footing, contact the
  authors directly (bahga@mech.iitd.ac.in).
- What is theirs and what is not: the numerical scheme is SPYCE's. The
  electroosmotic-flow model, the Joule-heating calculations, the
  composition validation, the ion library and all of the plotting and
  notebook code are drylab's own — SPYCE models transport explicitly
  without bulk flow, so EOF has no counterpart there.
- SPYCE remains the validation oracle: `validation/compare_ce.py` checks
  drylab against a dump from stock SPYCE, and the agreement is reported in
  the README.

## Other references

The HPLC model derives from the JavaScript simulator by Matt Libby, itself
derived from the **HPLC Simulator** of Paul Boswell, Peter Carr and Dwight
Stoll (J. Chem. Educ. 2013, 90, 198–202). The GC model is validated
against GasChromatographySimulator.jl (Jan Leppert, MIT). The Craig model
is validated against Appendix 16 of Harvey's *Analytical Chemistry 2.0*.
