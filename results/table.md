### Results table

| Exp | Attack | Source | Adapt | Defense | Clean MF1 | ASR (installed) | ctrl: freq | ctrl: gaussian | ctrl: patch | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | — | Clean | None | - | 78.2 ± 0.2 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 100.0 ± 0.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 100.0 ± 0.0 | **97.6 ± 2.1** | _97.6 ± 2.1_ | 18.2 ± 16.9 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 75.8 ± 2.0 | **86.3 ± 11.9** | _86.3 ± 11.9_ | 28.3 ± 3.9 | 21.9 ± 18.1 | 3 |
| E4 | freq | Backdoored | MAPU | - | 100.0 ± 0.0 | **80.2 ± 5.0** | _80.2 ± 5.0_ | 0.5 ± 0.8 | 0.5 ± 0.8 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **52.3 ± 30.6** | _52.3 ± 30.6_ | 0.9 ± 0.8 | 0.9 ± 0.8 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **52.8 ± 29.5** | _52.8 ± 29.5_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **37.5 ± 37.6** | _37.5 ± 37.6_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **5.1 ± 8.8** | _5.1 ± 8.8_ | 0.0 ± 0.0 | 0.5 ± 0.8 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 92.2 ± 13.6 | **73.1 ± 1.7** | _73.1 ± 1.7_ | 7.5 ± 13.0 | 8.0 ± 12.6 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 95.1 ± 8.6 | **31.3 ± 15.5** | _31.3 ± 15.5_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 100.0 ± 0.0 | **87.0 ± 11.8** | 0.0 ± 0.0 | _87.0 ± 11.8_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 77.2 ± 1.1 | **100.0 ± 0.0** | 0.9 ± 1.6 | _100.0 ± 0.0_ | 1.9 ± 2.2 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 100.0 ± 0.0 | **0.5 ± 0.8** | 0.0 ± 0.0 | _0.5 ± 0.8_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **1.4 ± 1.4** | 4.6 ± 8.0 | _1.4 ± 1.4_ | 0.0 ± 0.0 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **4.8 ± 4.4** | 0.0 ± 0.0 | _4.8 ± 4.4_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 79.8 ± 13.1 | **20.7 ± 2.9** | 6.6 ± 11.4 | _20.7 ± 2.9_ | 7.0 ± 12.2 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 98.5 ± 2.5 | **0.5 ± 0.8** | 0.0 ± 0.0 | _0.5 ± 0.8_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 100.0 ± 0.0 | **70.3 ± 2.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _70.3 ± 2.7_ | 3 |
| E3 | patch | Backdoored | None | - | 69.9 ± 10.3 | **99.5 ± 0.8** | 1.9 ± 2.1 | 6.6 ± 3.4 | _99.5 ± 0.8_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 100.0 ± 0.0 | **1.4 ± 0.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.4 ± 0.0_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **17.1 ± 14.8** | 0.0 ± 0.0 | 0.5 ± 0.8 | _17.1 ± 14.8_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **8.4 ± 8.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _8.4 ± 8.6_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **0.9 ± 0.8** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.9 ± 0.8_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **3.3 ± 1.7** | 0.0 ± 0.0 | 0.5 ± 0.8 | _3.3 ± 1.7_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 100.0 ± 0.0 | **6.2 ± 7.2** | 0.0 ± 0.0 | 0.0 ± 0.0 | _6.2 ± 7.2_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **35.2 ± 22.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _35.2 ± 22.6_ | 3 |

Dataset har · scenario 2->11 · mean ± std across seeds, all values %.

*Attack* is the trigger the source model was poisoned with and *ASR (installed)* is
its attack success rate. The `ctrl:` columns apply every trigger to every model as a
control. E1 and E2 use a clean source model.

Clean MF1 is macro-F1 on the target test split. ASR excludes windows whose true label
is already the target class.
