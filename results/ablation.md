### Secure-MAPU component and lambda ablation

patch family, seed 42, subject 2 -> 11. `C1`/`C0` = compression on/off,
`KT1`/`KT0` = knowledge transfer on/off, `lam` = spectral penalty weight.

| Condition | Compression | Knowledge transfer | lambda | Clean MF1 | ASR | Channels zeroed | Compressed abs-mean final |
|---|---|---|---|---|---|---|---|
| `C1-KT1-lam0` | yes | yes | 0.0 | 100.0 | **39.4** | 47 | 0.0e+00 |
| `C1-KT0-lam0` | yes | no | 0.0 | 100.0 | **4.2** | 47 | 0.0e+00 |
| `C0-KT1-lam0` | no | yes | 0.0 | 100.0 | **42.3** | 0 | - |
| `full-lam0` | yes | yes | 0.0 | 100.0 | **39.4** | 47 | 0.0e+00 |
| `full-lam0.0001` | yes | yes | 0.0001 | 100.0 | **38.0** | 47 | 0.0e+00 |
| `full-lam0.001` | yes | yes | 0.001 | 100.0 | **25.4** | 47 | 0.0e+00 |
| `full-lam0.01` | yes | yes | 0.01 | 100.0 | **22.5** | 47 | 0.0e+00 |
| `full-lam0.1` | yes | yes | 0.1 | 100.0 | **15.5** | 47 | 0.0e+00 |
| `full-lam1` | yes | yes | 1.0 | 100.0 | **1.4** | 47 | 0.0e+00 |
| `full-lam100` | yes | yes | 100.0 | 100.0 | **97.2** | 47 | 0.0e+00 |
| `noKT-lam0` | yes | no | 0.0 | 100.0 | **4.2** | 47 | 0.0e+00 |
| `noKT-lam0.0001` | yes | no | 0.0001 | 100.0 | **4.2** | 47 | 0.0e+00 |
| `noKT-lam0.001` | yes | no | 0.001 | 100.0 | **1.4** | 47 | 0.0e+00 |
| `noKT-lam0.01` | yes | no | 0.01 | 100.0 | **1.4** | 47 | 0.0e+00 |
| `noKT-lam0.1` | yes | no | 0.1 | 100.0 | **1.4** | 47 | 0.0e+00 |
| `noKT-lam1` | yes | no | 1.0 | 100.0 | **40.8** | 47 | 0.0e+00 |
| `noKT-lam100` | yes | no | 100.0 | 98.8 | **100.0** | 47 | 0.0e+00 |

Single seed, so differences of a few points are within noise. lambda = 100 is SSDA's
published value. The last column checks that compressed channels stay at zero during
adaptation. See docs/report.md for discussion.
