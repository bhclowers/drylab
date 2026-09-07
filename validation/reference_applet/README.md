# Efstathiou Craig-apparatus applet — decoded math

The page at `webapps.chem.uoa.gr/efs/applets/AppletCraig/Appl_Craig2.html`
carries an obfuscated JavaScript canvas app by C. E. Efstathiou (University of
Athens). The page cannot be fetched programmatically (it serves only a
"will not work in this browser" notice); the script below was supplied by the
user from the page source and deobfuscated by hand.

Only the *mathematics* is recorded here — no code is copied or redistributed.

## calculateFractions()

    C      = exp(lnFact(n) - lnFact(i) - lnFact(n - i))     # binomial coefficient
    total  = C * D**i / (D + 1)**n                          # fraction in tube i
    upper  = D * total / (D + 1)                            # = p * total
    lower  = total / (D + 1)                                # = q * total

With `p = D/(D+1)` and `q = 1/(D+1)`, `total` is algebraically identical to
equation A16.2 of *Analytical Chemistry 2.0* Appendix 16:

    f(r, n) = C(n, r) * p**r * q**(n-r)

and the phase split matches that appendix's statement that the upper phase
holds `p*f(r,n)` and the lower phase `q*f(r,n)`. **The applet and the textbook
are the same model.** Both are checked in `validation/compare_craig.py`.

## calculateElution()

    eluted = 1 - sum(total(n, i) for i in range(0, Ntubes + 1))

i.e. whatever the binomial places beyond the last tube has left the train.
The applet uses 20 tubes (indices 0..19) and lets the transfer count exceed
that, so analyte progressively elutes. This port follows the same behaviour
(`AnalyteResult.eluted`) rather than refusing such steps.

Reference values reproduced in the validation script (D_A = 0.50, D_B = 3.50,
20 tubes): at 25 transfers B is 50.76% eluted; at 40, A is 2.14% and B 100%;
at 60, A is 54.84%.

## Defaults observed in the applet

- 20 tubes, `D_A = 0.50`, `D_B = 3.50`
- Controls: RESTART, EXTRACT, TRANSFER (alternating enabled/disabled)
- Readouts: "Eluted A", "Eluted B" (percent), "Transfers"
- Upper plot: A- and B-fractions vs tube number (paired bars)
