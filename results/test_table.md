### Test subject pairs

| Exp | Attack | Source | Adapt | Defense | Clean MF1 | ASR (installed) | ctrl: freq | ctrl: gaussian | ctrl: patch | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | — | Clean | None | - | 99.3 ± 0.6 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 100.0 ± 0.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 96.9 ± 1.8 | **75.9 ± 4.2** | _75.9 ± 4.2_ | 17.0 ± 5.1 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 96.0 ± 2.5 | **94.5 ± 9.5** | _94.5 ± 9.5_ | 33.7 ± 2.4 | 5.4 ± 1.7 | 3 |
| E4 | freq | Backdoored | MAPU | - | 100.0 ± 0.0 | **61.9 ± 12.9** | _61.9 ± 12.9_ | 0.8 ± 0.7 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **28.8 ± 12.8** | _28.8 ± 12.8_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **29.6 ± 32.7** | _29.6 ± 32.7_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **16.0 ± 23.6** | _16.0 ± 23.6_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **0.0 ± 0.0** | _0.0 ± 0.0_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 100.0 ± 0.0 | **49.7 ± 23.4** | _49.7 ± 23.4_ | 0.8 ± 0.7 | 0.0 ± 0.0 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **0.4 ± 0.7** | _0.4 ± 0.7_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 95.8 ± 0.8 | **66.4 ± 50.5** | 0.8 ± 0.7 | _66.4 ± 50.5_ | 0.8 ± 1.3 | 3 |
| E3 | gaussian | Backdoored | None | - | 90.5 ± 6.6 | **85.6 ± 12.0** | 0.0 ± 0.0 | _85.6 ± 12.0_ | 0.0 ± 0.0 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 100.0 ± 0.0 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 98.5 ± 1.7 | **2.3 ± 1.1** | 0.4 ± 0.7 | _2.3 ± 1.1_ | 0.4 ± 0.7 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **1.1 ± 1.1** | 0.0 ± 0.0 | _1.1 ± 1.1_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 95.7 ± 7.5 | **7.0 ± 11.2** | 0.4 ± 0.7 | _7.0 ± 11.2_ | 0.8 ± 0.7 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 73.0 ± 20.3 | **13.9 ± 12.0** | 13.9 ± 12.0 | _13.9 ± 12.0_ | 13.9 ± 12.0 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 98.0 ± 0.9 | **67.7 ± 18.0** | 0.8 ± 0.7 | 0.8 ± 0.7 | _67.7 ± 18.0_ | 3 |
| E3 | patch | Backdoored | None | - | 99.7 ± 0.6 | **94.1 ± 3.2** | 0.0 ± 0.0 | 1.5 ± 1.3 | _94.1 ± 3.2_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 100.0 ± 0.0 | **1.6 ± 0.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.6 ± 0.7_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **1.6 ± 0.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.6 ± 0.7_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **22.8 ± 35.5** | 0.0 ± 0.0 | 0.0 ± 0.0 | _22.8 ± 35.5_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **0.8 ± 0.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.8 ± 0.7_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **0.8 ± 0.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.8 ± 0.7_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 100.0 ± 0.0 | **1.2 ± 0.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.2 ± 0.0_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.0 ± 0.0_ | 3 |
| E1 | — | Clean | None | - | 72.8 ± 2.8 | — | 6.9 ± 0.2 | 2.3 ± 2.1 | 5.9 ± 1.9 | 3 |
| E2 | — | Clean | MAPU | - | 90.1 ± 10.1 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 87.2 ± 9.4 | **88.8 ± 4.5** | _88.8 ± 4.5_ | 29.2 ± 17.9 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 70.1 ± 7.9 | **98.6 ± 2.5** | _98.6 ± 2.5_ | 43.7 ± 5.7 | 16.6 ± 12.1 | 3 |
| E4 | freq | Backdoored | MAPU | - | 92.0 ± 9.3 | **74.3 ± 3.1** | _74.3 ± 3.1_ | 0.5 ± 0.8 | 0.5 ± 0.8 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 98.7 ± 1.3 | **33.2 ± 4.7** | _33.2 ± 4.7_ | 0.5 ± 0.8 | 0.5 ± 0.8 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 89.2 ± 6.1 | **52.9 ± 16.1** | _52.9 ± 16.1_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 90.1 ± 7.6 | **35.8 ± 29.5** | _35.8 ± 29.5_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 88.2 ± 7.9 | **11.3 ± 8.7** | _11.3 ± 8.7_ | 0.5 ± 0.8 | 0.5 ± 0.8 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 71.8 ± 13.3 | **64.5 ± 11.7** | _64.5 ± 11.7_ | 14.1 ± 12.5 | 14.1 ± 12.5 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 87.1 ± 3.3 | **35.5 ± 18.1** | _35.5 ± 18.1_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 81.7 ± 3.6 | **94.2 ± 10.0** | 0.0 ± 0.0 | _94.2 ± 10.0_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 55.7 ± 7.2 | **99.0 ± 1.6** | 0.0 ± 0.0 | _99.0 ± 1.6_ | 0.5 ± 0.8 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 84.6 ± 5.6 | **1.0 ± 1.6** | 0.0 ± 0.0 | _1.0 ± 1.6_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 92.9 ± 4.8 | **2.3 ± 1.5** | 0.0 ± 0.0 | _2.3 ± 1.5_ | 0.5 ± 0.8 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 83.3 ± 4.1 | **51.1 ± 3.7** | 0.0 ± 0.0 | _51.1 ± 3.7_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 82.6 ± 3.7 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 90.2 ± 7.0 | **0.5 ± 0.8** | 0.0 ± 0.0 | _0.5 ± 0.8_ | 0.5 ± 0.8 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 68.7 ± 19.7 | **8.3 ± 9.7** | 6.5 ± 11.2 | _8.3 ± 9.7_ | 6.5 ± 11.2 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 82.8 ± 1.6 | **0.9 ± 0.8** | 0.0 ± 0.0 | _0.9 ± 0.8_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 86.0 ± 9.3 | **56.7 ± 2.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _56.7 ± 2.7_ | 3 |
| E3 | patch | Backdoored | None | - | 71.5 ± 5.4 | **100.0 ± 0.0** | 22.7 ± 8.3 | 30.0 ± 9.2 | _100.0 ± 0.0_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 90.1 ± 10.0 | **2.8 ± 1.4** | 0.0 ± 0.0 | 0.0 ± 0.0 | _2.8 ± 1.4_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 92.3 ± 13.3 | **13.2 ± 9.0** | 0.5 ± 0.8 | 0.5 ± 0.8 | _13.2 ± 9.0_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 89.1 ± 6.9 | **44.4 ± 11.3** | 0.0 ± 0.0 | 0.0 ± 0.0 | _44.4 ± 11.3_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 89.1 ± 9.3 | **2.8 ± 1.4** | 0.0 ± 0.0 | 0.0 ± 0.0 | _2.8 ± 1.4_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 82.7 ± 5.5 | **1.8 ± 0.8** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.8 ± 0.8_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 89.6 ± 7.4 | **8.3 ± 8.5** | 0.0 ± 0.0 | 0.0 ± 0.0 | _8.3 ± 8.5_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 84.8 ± 4.3 | **14.4 ± 3.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _14.4 ± 3.7_ | 3 |
| E1 | — | Clean | None | - | 95.4 ± 8.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 100.0 ± 0.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 85.4 ± 12.7 | **37.9 ± 9.9** | _37.9 ± 9.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 76.2 ± 2.4 | **99.6 ± 0.7** | _99.6 ± 0.7_ | 39.2 ± 3.6 | 32.0 ± 12.3 | 3 |
| E4 | freq | Backdoored | MAPU | - | 100.0 ± 0.0 | **21.8 ± 4.2** | _21.8 ± 4.2_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **6.9 ± 8.5** | _6.9 ± 8.5_ | 0.8 ± 1.5 | 0.0 ± 0.0 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 98.3 ± 1.5 | **3.8 ± 6.6** | _3.8 ± 6.6_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **12.9 ± 11.2** | _12.9 ± 11.2_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **0.5 ± 0.8** | _0.5 ± 0.8_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 95.4 ± 8.0 | **20.5 ± 2.0** | _20.5 ± 2.0_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **7.1 ± 11.0** | _7.1 ± 11.0_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 80.5 ± 3.4 | **74.0 ± 17.8** | 0.0 ± 0.0 | _74.0 ± 17.8_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 95.4 ± 8.0 | **98.6 ± 1.5** | 0.0 ± 0.0 | _98.6 ± 1.5_ | 0.0 ± 0.0 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 83.2 ± 8.6 | **0.5 ± 0.8** | 0.0 ± 0.0 | _0.5 ± 0.8_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 79.1 ± 0.9 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 84.8 ± 11.0 | **4.4 ± 5.5** | 0.0 ± 0.0 | _4.4 ± 5.5_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 84.2 ± 10.3 | **0.5 ± 0.8** | 0.0 ± 0.0 | _0.5 ± 0.8_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 84.4 ± 5.1 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 73.7 ± 7.8 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 85.2 ± 11.7 | **3.0 ± 3.0** | 0.0 ± 0.0 | _3.0 ± 3.0_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 75.2 ± 17.5 | **32.1 ± 8.3** | 0.5 ± 0.8 | 0.5 ± 0.8 | _32.1 ± 8.3_ | 3 |
| E3 | patch | Backdoored | None | - | 86.0 ± 8.8 | **97.3 ± 2.4** | 13.1 ± 12.4 | 28.8 ± 10.8 | _97.3 ± 2.4_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 90.3 ± 11.5 | **2.4 ± 1.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _2.4 ± 1.7_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 73.0 ± 9.0 | **8.5 ± 11.1** | 6.6 ± 11.4 | 6.6 ± 11.4 | _8.5 ± 11.1_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 88.4 ± 10.6 | **6.8 ± 11.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _6.8 ± 11.7_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 90.6 ± 11.0 | **1.5 ± 1.5** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.5 ± 1.5_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 75.0 ± 11.1 | **7.1 ± 11.0** | 6.6 ± 11.4 | 6.6 ± 11.4 | _7.1 ± 11.0_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 83.9 ± 18.5 | **0.9 ± 0.8** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.9 ± 0.8_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 89.5 ± 10.7 | **6.4 ± 11.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _6.4 ± 11.0_ | 3 |
| E1 | — | Clean | None | - | 98.6 ± 2.5 | — | 2.0 ± 3.4 | 2.4 ± 4.1 | 2.4 ± 4.1 | 3 |
| E2 | — | Clean | MAPU | - | 100.0 ± 0.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 99.6 ± 0.6 | **88.7 ± 5.4** | _88.7 ± 5.4_ | 13.1 ± 7.4 | 0.8 ± 1.4 | 3 |
| E3 | freq | Backdoored | None | - | 99.3 ± 0.6 | **91.8 ± 6.6** | _91.8 ± 6.6_ | 22.5 ± 1.0 | 0.8 ± 1.4 | 3 |
| E4 | freq | Backdoored | MAPU | - | 100.0 ± 0.0 | **59.2 ± 10.8** | _59.2 ± 10.8_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 100.0 ± 0.0 | **37.2 ± 10.9** | _37.2 ± 10.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **35.2 ± 9.8** | _35.2 ± 9.8_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **12.9 ± 20.3** | _12.9 ± 20.3_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 100.0 ± 0.0 | **15.6 ± 22.9** | _15.6 ± 22.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 67.2 ± 1.0 | **52.3 ± 1.0** | _52.3 ± 1.0_ | 0.8 ± 0.7 | 0.4 ± 0.7 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 100.0 ± 0.0 | **15.2 ± 23.3** | _15.2 ± 23.3_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 90.2 ± 10.1 | **72.7 ± 17.5** | 9.0 ± 9.8 | _72.7 ± 17.5_ | 10.0 ± 10.2 | 3 |
| E3 | gaussian | Backdoored | None | - | 93.4 ± 4.1 | **78.1 ± 20.4** | 0.4 ± 0.7 | _78.1 ± 20.4_ | 0.4 ± 0.7 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 99.6 ± 0.6 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 96.1 ± 6.8 | **8.6 ± 12.9** | 1.2 ± 1.2 | _8.6 ± 12.9_ | 2.0 ± 2.4 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 100.0 ± 0.0 | **3.0 ± 5.2** | 0.0 ± 0.0 | _3.0 ± 5.2_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **0.8 ± 1.4** | 0.0 ± 0.0 | _0.8 ± 1.4_ | 0.4 ± 0.7 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 89.7 ± 17.8 | **7.8 ± 13.6** | 7.8 ± 13.6 | _7.8 ± 13.6_ | 8.2 ± 13.3 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 66.5 ± 10.2 | **8.8 ± 11.1** | 0.4 ± 0.7 | _8.8 ± 11.1_ | 0.8 ± 1.4 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 91.9 ± 14.1 | **7.5 ± 12.9** | 1.2 ± 2.0 | _7.5 ± 12.9_ | 7.5 ± 12.9 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 94.9 ± 5.0 | **82.9 ± 14.7** | 0.8 ± 0.7 | 1.5 ± 0.6 | _82.9 ± 14.7_ | 3 |
| E3 | patch | Backdoored | None | - | 100.0 ± 0.0 | **98.0 ± 1.8** | 0.0 ± 0.0 | 0.4 ± 0.7 | _98.0 ± 1.8_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 100.0 ± 0.0 | **9.8 ± 13.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _9.8 ± 13.0_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 91.6 ± 14.6 | **22.1 ± 21.2** | 0.4 ± 0.7 | 4.7 ± 7.2 | _22.1 ± 21.2_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 99.6 ± 0.6 | **19.8 ± 22.4** | 0.4 ± 0.7 | 0.8 ± 0.7 | _19.8 ± 22.4_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 100.0 ± 0.0 | **7.8 ± 13.6** | 0.0 ± 0.0 | 0.4 ± 0.7 | _7.8 ± 13.6_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 68.7 ± 28.3 | **20.9 ± 20.0** | 14.3 ± 12.4 | 14.7 ± 12.8 | _20.9 ± 20.0_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 75.6 ± 21.4 | **15.0 ± 13.0** | 7.5 ± 12.9 | 7.1 ± 12.2 | _15.0 ± 13.0_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 91.8 ± 13.2 | **20.0 ± 18.9** | 0.4 ± 0.7 | 7.5 ± 12.9 | _20.0 ± 18.9_ | 3 |
| E1 | — | Clean | None | - | 88.8 ± 19.5 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 85.3 ± 8.0 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 85.2 ± 10.1 | **89.7 ± 7.1** | _89.7 ± 7.1_ | 23.9 ± 12.7 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 91.9 ± 9.0 | **92.6 ± 9.8** | _92.6 ± 9.8_ | 29.4 ± 9.1 | 5.1 ± 6.8 | 3 |
| E4 | freq | Backdoored | MAPU | - | 84.4 ± 7.4 | **48.1 ± 4.3** | _48.1 ± 4.3_ | 2.0 ± 3.5 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 85.3 ± 9.8 | **7.5 ± 5.5** | _7.5 ± 5.5_ | 5.8 ± 3.7 | 3.3 ± 5.7 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 78.2 ± 2.8 | **33.4 ± 17.5** | _33.4 ± 17.5_ | 11.8 ± 19.4 | 0.4 ± 0.7 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 90.2 ± 11.8 | **22.2 ± 11.9** | _22.2 ± 11.9_ | 3.3 ± 3.1 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 80.9 ± 8.4 | **5.0 ± 4.9** | _5.0 ± 4.9_ | 6.7 ± 5.8 | 3.3 ± 5.7 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 78.8 ± 18.3 | **33.4 ± 24.1** | _33.4 ± 24.1_ | 2.9 ± 4.0 | 0.0 ± 0.0 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 95.5 ± 4.3 | **2.9 ± 3.9** | _2.9 ± 3.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 71.8 ± 16.1 | **68.7 ± 19.5** | 6.7 ± 5.8 | _68.7 ± 19.5_ | 7.1 ± 6.2 | 3 |
| E3 | gaussian | Backdoored | None | - | 84.1 ± 14.5 | **90.2 ± 16.9** | 6.7 ± 5.8 | _90.2 ± 16.9_ | 7.5 ± 6.6 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 76.9 ± 7.3 | **9.7 ± 9.6** | 7.1 ± 6.2 | _9.7 ± 9.6_ | 7.6 ± 6.7 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 70.5 ± 7.2 | **3.4 ± 5.9** | 3.4 ± 5.9 | _3.4 ± 5.9_ | 3.4 ± 5.9 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 65.0 ± 13.5 | **6.7 ± 5.8** | 6.7 ± 5.8 | _6.7 ± 5.8_ | 6.7 ± 5.8 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 79.2 ± 8.0 | **8.8 ± 8.4** | 7.1 ± 6.2 | _8.8 ± 8.4_ | 7.6 ± 6.7 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 69.8 ± 30.2 | **9.9 ± 9.8** | 9.9 ± 9.8 | _9.9 ± 9.8_ | 9.9 ± 9.8 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 66.9 ± 3.9 | **6.7 ± 5.8** | 6.7 ± 5.8 | _6.7 ± 5.8_ | 6.7 ± 5.8 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 73.0 ± 14.3 | **11.3 ± 9.0** | 6.7 ± 5.8 | _11.3 ± 9.0_ | 6.7 ± 5.8 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 83.3 ± 17.8 | **81.9 ± 9.4** | 3.3 ± 5.7 | 3.3 ± 5.7 | _81.9 ± 9.4_ | 3 |
| E3 | patch | Backdoored | None | - | 91.7 ± 9.8 | **92.3 ± 11.3** | 2.1 ± 3.6 | 5.9 ± 5.2 | _92.3 ± 11.3_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 71.5 ± 12.1 | **15.4 ± 7.2** | 3.3 ± 5.7 | 3.3 ± 5.7 | _15.4 ± 7.2_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 71.0 ± 10.9 | **17.8 ± 8.5** | 3.3 ± 5.7 | 7.6 ± 6.7 | _17.8 ± 8.5_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 60.4 ± 6.7 | **24.0 ± 30.6** | 3.3 ± 5.7 | 3.3 ± 5.7 | _24.0 ± 30.6_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 71.0 ± 11.1 | **12.6 ± 11.1** | 0.0 ± 0.0 | 0.8 ± 0.7 | _12.6 ± 11.1_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 68.7 ± 18.3 | **19.5 ± 8.7** | 3.3 ± 5.7 | 10.1 ± 10.3 | _19.5 ± 8.7_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 69.7 ± 11.0 | **10.8 ± 9.3** | 0.0 ± 0.0 | 2.9 ± 5.0 | _10.8 ± 9.3_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 66.5 ± 11.3 | **25.6 ± 9.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _25.6 ± 9.6_ | 3 |

Dataset har · scenario 18->27, 20->5, 24->8, 28->27, 30->20 · mean ± std across seeds, all values %.

*Attack* is the trigger the source model was poisoned with and *ASR (installed)* is
its attack success rate. The `ctrl:` columns apply every trigger to every model as a
control. E1 and E2 use a clean source model.

Clean MF1 is macro-F1 on the target test split. ASR excludes windows whose true label
is already the target class.
