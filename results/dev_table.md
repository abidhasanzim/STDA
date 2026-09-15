### Development subject pairs

| Exp | Attack | Source | Adapt | Defense | Clean MF1 | ASR (installed) | ctrl: freq | ctrl: gaussian | ctrl: patch | Seeds |
|---|---|---|---|---|---|---|---|---|---|---|
| E1 | — | Clean | None | - | 85.6 ± 4.5 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 66.6 ± 10.1 | — | 7.7 ± 5.6 | 7.3 ± 6.4 | 6.9 ± 6.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 76.2 ± 11.7 | **85.2 ± 8.2** | _85.2 ± 8.2_ | 20.2 ± 8.1 | 0.8 ± 0.7 | 3 |
| E3 | freq | Backdoored | None | - | 84.2 ± 13.8 | **76.6 ± 6.1** | _76.6 ± 6.1_ | 12.8 ± 6.9 | 0.0 ± 0.0 | 3 |
| E4 | freq | Backdoored | MAPU | - | 71.8 ± 18.1 | **63.9 ± 15.6** | _63.9 ± 15.6_ | 9.9 ± 0.4 | 10.3 ± 0.5 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 48.7 ± 16.1 | **23.9 ± 14.8** | _23.9 ± 14.8_ | 10.9 ± 10.8 | 9.3 ± 8.6 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 71.5 ± 18.4 | **37.7 ± 8.2** | _37.7 ± 8.2_ | 11.1 ± 0.9 | 10.3 ± 0.5 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 71.8 ± 18.1 | **28.2 ± 18.4** | _28.2 ± 18.4_ | 10.3 ± 1.0 | 9.5 ± 0.3 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 61.0 ± 17.9 | **15.1 ± 6.7** | _15.1 ± 6.7_ | 14.7 ± 6.2 | 14.7 ± 7.1 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 65.5 ± 9.2 | **60.7 ± 20.2** | _60.7 ± 20.2_ | 12.2 ± 7.6 | 10.1 ± 9.1 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 71.2 ± 17.9 | **36.3 ± 12.4** | _36.3 ± 12.4_ | 9.9 ± 0.4 | 9.9 ± 0.4 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 53.7 ± 3.0 | **23.0 ± 5.0** | 0.0 ± 0.0 | _23.0 ± 5.0_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 76.3 ± 9.8 | **59.7 ± 16.9** | 1.1 ± 2.0 | _59.7 ± 16.9_ | 0.8 ± 1.3 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 57.7 ± 6.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 59.4 ± 14.2 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 63.4 ± 7.1 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 57.9 ± 6.3 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 59.9 ± 8.2 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 67.4 ± 3.9 | **6.9 ± 12.0** | 1.2 ± 2.1 | _6.9 ± 12.0_ | 6.1 ± 10.6 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 63.3 ± 6.0 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 71.2 ± 3.0 | **58.1 ± 10.5** | 4.8 ± 6.3 | 4.8 ± 6.4 | _58.1 ± 10.5_ | 3 |
| E3 | patch | Backdoored | None | - | 89.8 ± 4.9 | **85.2 ± 5.2** | 2.3 ± 2.0 | 4.7 ± 3.1 | _85.2 ± 5.2_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 71.5 ± 20.4 | **13.3 ± 12.2** | 0.4 ± 0.7 | 0.4 ± 0.7 | _13.3 ± 12.2_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 56.0 ± 10.1 | **16.7 ± 19.8** | 4.3 ± 5.4 | 4.3 ± 5.4 | _16.7 ± 19.8_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 72.7 ± 20.7 | **26.7 ± 21.1** | 0.4 ± 0.7 | 0.4 ± 0.7 | _26.7 ± 21.1_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 66.1 ± 18.4 | **7.9 ± 7.8** | 1.6 ± 2.8 | 3.2 ± 5.6 | _7.9 ± 7.8_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 59.8 ± 15.9 | **13.0 ± 11.3** | 1.2 ± 1.2 | 2.8 ± 3.9 | _13.0 ± 11.3_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 59.5 ± 14.7 | **6.2 ± 7.0** | 0.4 ± 0.7 | 0.8 ± 0.7 | _6.2 ± 7.0_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 70.7 ± 18.8 | **34.7 ± 21.2** | 1.6 ± 2.8 | 1.6 ± 2.8 | _34.7 ± 21.2_ | 3 |
| E1 | — | Clean | None | - | 74.3 ± 5.5 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 1.1 ± 1.1 | 3 |
| E2 | — | Clean | MAPU | - | 92.7 ± 12.6 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 91.8 ± 12.6 | **68.4 ± 5.6** | _68.4 ± 5.6_ | 5.4 ± 5.9 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 75.2 ± 17.1 | **93.8 ± 7.0** | _93.8 ± 7.0_ | 33.8 ± 5.6 | 16.9 ± 8.6 | 3 |
| E4 | freq | Backdoored | MAPU | - | 92.7 ± 12.6 | **37.8 ± 7.2** | _37.8 ± 7.2_ | 0.8 ± 0.7 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 77.1 ± 20.0 | **15.5 ± 13.4** | _15.5 ± 13.4_ | 7.7 ± 13.3 | 7.7 ± 13.3 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 92.7 ± 12.6 | **0.0 ± 0.0** | _0.0 ± 0.0_ | 0.4 ± 0.7 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 80.5 ± 2.0 | **5.0 ± 6.9** | _5.0 ± 6.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 83.4 ± 6.2 | **9.4 ± 12.5** | _9.4 ± 12.5_ | 0.0 ± 0.0 | 0.4 ± 0.7 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 73.7 ± 15.1 | **37.2 ± 9.3** | _37.2 ± 9.3_ | 6.9 ± 11.9 | 10.6 ± 10.4 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 90.5 ± 11.2 | **1.5 ± 2.5** | _1.5 ± 2.5_ | 0.4 ± 0.6 | 0.4 ± 0.6 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 91.2 ± 11.4 | **91.7 ± 1.4** | 0.0 ± 0.0 | _91.7 ± 1.4_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 72.6 ± 18.9 | **98.1 ± 2.5** | 0.0 ± 0.0 | _98.1 ± 2.5_ | 0.0 ± 0.0 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 92.7 ± 12.6 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 92.7 ± 12.6 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 92.7 ± 12.6 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 81.0 ± 2.5 | **0.4 ± 0.7** | 0.0 ± 0.0 | _0.4 ± 0.7_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 82.9 ± 6.5 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 71.2 ± 13.7 | **24.5 ± 9.4** | 6.1 ± 10.6 | _24.5 ± 9.4_ | 10.1 ± 8.8 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 92.7 ± 12.6 | **2.2 ± 2.2** | 0.0 ± 0.0 | _2.2 ± 2.2_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 92.4 ± 12.3 | **60.6 ± 11.5** | 0.0 ± 0.0 | 0.0 ± 0.0 | _60.6 ± 11.5_ | 3 |
| E3 | patch | Backdoored | None | - | 69.5 ± 10.7 | **99.2 ± 0.7** | 1.9 ± 1.2 | 3.8 ± 2.3 | _99.2 ± 0.7_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 92.7 ± 12.6 | **11.6 ± 10.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _11.6 ± 10.6_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 80.3 ± 18.8 | **15.5 ± 13.4** | 7.3 ± 12.6 | 7.3 ± 12.6 | _15.5 ± 13.4_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 92.7 ± 12.6 | **10.9 ± 15.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _10.9 ± 15.0_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 88.3 ± 8.7 | **12.4 ± 11.2** | 0.0 ± 0.0 | 0.0 ± 0.0 | _12.4 ± 11.2_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 74.0 ± 11.8 | **14.7 ± 11.9** | 7.7 ± 13.3 | 7.7 ± 13.3 | _14.7 ± 11.9_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 81.2 ± 14.4 | **17.8 ± 5.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _17.8 ± 5.6_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 89.5 ± 10.9 | **23.2 ± 19.5** | 0.0 ± 0.0 | 0.0 ± 0.0 | _23.2 ± 19.5_ | 3 |
| E1 | — | Clean | None | - | 78.8 ± 1.6 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 84.2 ± 6.6 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 77.2 ± 5.6 | **89.6 ± 5.6** | _89.6 ± 5.6_ | 10.0 ± 15.3 | 0.0 ± 0.0 | 3 |
| E3 | freq | Backdoored | None | - | 73.7 ± 8.9 | **97.8 ± 3.9** | _97.8 ± 3.9_ | 22.7 ± 10.7 | 0.4 ± 0.7 | 3 |
| E4 | freq | Backdoored | MAPU | - | 85.1 ± 8.1 | **84.9 ± 4.1** | _84.9 ± 4.1_ | 0.4 ± 0.6 | 0.0 ± 0.0 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 86.6 ± 10.7 | **42.4 ± 8.8** | _42.4 ± 8.8_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 91.4 ± 9.9 | **48.8 ± 17.9** | _48.8 ± 17.9_ | 0.4 ± 0.6 | 0.0 ± 0.0 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 78.3 ± 1.2 | **24.8 ± 40.9** | _24.8 ± 40.9_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 86.3 ± 11.0 | **0.4 ± 0.7** | _0.4 ± 0.7_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 62.7 ± 9.5 | **41.0 ± 15.5** | _41.0 ± 15.5_ | 7.9 ± 11.7 | 7.1 ± 12.3 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 91.9 ± 10.1 | **7.7 ± 4.7** | _7.7 ± 4.7_ | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 72.9 ± 13.1 | **100.0 ± 0.0** | 0.0 ± 0.0 | _100.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E3 | gaussian | Backdoored | None | - | 69.8 ± 8.0 | **83.1 ± 9.7** | 0.0 ± 0.0 | _83.1 ± 9.7_ | 0.0 ± 0.0 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 81.0 ± 9.3 | **3.6 ± 4.4** | 0.0 ± 0.0 | _3.6 ± 4.4_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 75.4 ± 15.0 | **3.2 ± 5.6** | 3.2 ± 5.6 | _3.2 ± 5.6_ | 3.2 ± 5.6 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 91.9 ± 10.1 | **13.5 ± 3.2** | 0.0 ± 0.0 | _13.5 ± 3.2_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 78.4 ± 14.5 | **1.2 ± 2.1** | 0.0 ± 0.0 | _1.2 ± 2.1_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 78.9 ± 19.3 | **0.0 ± 0.0** | 0.0 ± 0.0 | _0.0 ± 0.0_ | 0.0 ± 0.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 62.0 ± 7.9 | **6.2 ± 5.4** | 6.2 ± 5.4 | _6.2 ± 5.4_ | 6.2 ± 5.4 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 85.9 ± 23.4 | **10.3 ± 9.7** | 0.0 ± 0.0 | _10.3 ± 9.7_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 72.9 ± 13.1 | **63.6 ± 36.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _63.6 ± 36.6_ | 3 |
| E3 | patch | Backdoored | None | - | 79.0 ± 1.2 | **99.3 ± 1.3** | 0.0 ± 0.0 | 1.1 ± 1.9 | _99.3 ± 1.3_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 82.3 ± 3.3 | **10.6 ± 9.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _10.6 ± 9.6_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 79.4 ± 5.8 | **5.9 ± 5.2** | 3.2 ± 5.6 | 3.2 ± 5.6 | _5.9 ± 5.2_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 91.9 ± 10.1 | **2.0 ± 1.4** | 0.0 ± 0.0 | 0.0 ± 0.0 | _2.0 ± 1.4_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 81.2 ± 3.2 | **3.5 ± 6.0** | 0.0 ± 0.0 | 0.0 ± 0.0 | _3.5 ± 6.0_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 79.2 ± 17.6 | **0.4 ± 0.7** | 0.0 ± 0.0 | 0.0 ± 0.0 | _0.4 ± 0.7_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 72.4 ± 11.8 | **1.6 ± 1.8** | 0.0 ± 0.0 | 0.0 ± 0.0 | _1.6 ± 1.8_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 93.1 ± 10.9 | **25.7 ± 33.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _25.7 ± 33.6_ | 3 |
| E1 | — | Clean | None | - | 12.9 ± 7.7 | — | 0.0 ± 0.0 | 0.0 ± 0.0 | 0.0 ± 0.0 | 3 |
| E2 | — | Clean | MAPU | - | 84.8 ± 20.0 | — | 1.1 ± 1.9 | 0.7 ± 1.3 | 0.7 ± 1.3 | 3 |
| A1 | freq | Backdoored | SHOT-IM | - | 84.5 ± 11.8 | **88.0 ± 10.5** | _88.0 ± 10.5_ | 20.8 ± 7.3 | 0.4 ± 0.6 | 3 |
| E3 | freq | Backdoored | None | - | 26.6 ± 14.1 | **83.2 ± 14.9** | _83.2 ± 14.9_ | 9.2 ± 5.5 | 0.0 ± 0.0 | 3 |
| E4 | freq | Backdoored | MAPU | - | 84.0 ± 24.4 | **80.3 ± 1.6** | _80.3 ± 1.6_ | 9.7 ± 6.3 | 3.8 ± 5.6 | 3 |
| E5 | freq | Backdoored | MAPU | Compression | 70.3 ± 46.5 | **68.6 ± 16.3** | _68.6 ± 16.3_ | 7.1 ± 4.2 | 3.8 ± 5.6 | 3 |
| E6 | freq | Backdoored | MAPU | Secure-MAPU | 89.0 ± 19.1 | **58.2 ± 20.7** | _58.2 ± 20.7_ | 4.9 ± 5.9 | 3.4 ± 5.9 | 3 |
| E7 | freq | Backdoored | MAPU | Consistency | 74.6 ± 27.6 | **45.3 ± 35.7** | _45.3 ± 35.7_ | 7.4 ± 6.9 | 3.4 ± 5.9 | 3 |
| E8 | freq | Backdoored | MAPU | Compress+Consistency | 57.5 ± 45.3 | **36.5 ± 17.7** | _36.5 ± 17.7_ | 10.8 ± 9.7 | 9.4 ± 10.3 | 3 |
| E9 | freq | Backdoored | MAPU | FT-SAM | 40.7 ± 14.6 | **81.3 ± 9.3** | _81.3 ± 9.3_ | 20.3 ± 13.6 | 17.8 ± 1.7 | 3 |
| E10 | freq | Backdoored | MAPU | Compression + consistency + KT | 74.6 ± 27.6 | **51.3 ± 22.3** | _51.3 ± 22.3_ | 3.8 ± 5.6 | 3.4 ± 5.9 | 3 |
| A1 | gaussian | Backdoored | SHOT-IM | - | 68.9 ± 15.5 | **99.6 ± 0.6** | 3.8 ± 5.6 | _99.6 ± 0.6_ | 3.8 ± 5.6 | 3 |
| E3 | gaussian | Backdoored | None | - | 8.5 ± 1.3 | **55.7 ± 12.8** | 0.0 ± 0.0 | _55.7 ± 12.8_ | 0.0 ± 0.0 | 3 |
| E4 | gaussian | Backdoored | MAPU | - | 64.4 ± 23.2 | **5.5 ± 6.8** | 0.0 ± 0.0 | _5.5 ± 6.8_ | 0.0 ± 0.0 | 3 |
| E5 | gaussian | Backdoored | MAPU | Compression | 60.3 ± 13.8 | **7.4 ± 6.4** | 3.4 ± 4.9 | _7.4 ± 6.4_ | 3.0 ± 5.2 | 3 |
| E6 | gaussian | Backdoored | MAPU | Secure-MAPU | 71.5 ± 12.8 | **12.0 ± 19.8** | 7.2 ± 12.6 | _12.0 ± 19.8_ | 0.0 ± 0.0 | 3 |
| E7 | gaussian | Backdoored | MAPU | Consistency | 51.8 ± 16.2 | **5.9 ± 6.2** | 0.0 ± 0.0 | _5.9 ± 6.2_ | 0.0 ± 0.0 | 3 |
| E8 | gaussian | Backdoored | MAPU | Compress+Consistency | 36.9 ± 8.3 | **17.2 ± 16.0** | 17.6 ± 16.5 | _17.2 ± 16.0_ | 17.2 ± 16.0 | 3 |
| E9 | gaussian | Backdoored | MAPU | FT-SAM | 41.1 ± 35.7 | **14.5 ± 7.8** | 11.1 ± 8.5 | _14.5 ± 7.8_ | 11.1 ± 8.5 | 3 |
| E10 | gaussian | Backdoored | MAPU | Compression + consistency + KT | 53.8 ± 14.8 | **19.7 ± 2.1** | 0.0 ± 0.0 | _19.7 ± 2.1_ | 0.0 ± 0.0 | 3 |
| A1 | patch | Backdoored | SHOT-IM | - | 76.8 ± 18.8 | **93.7 ± 5.3** | 0.0 ± 0.0 | 0.0 ± 0.0 | _93.7 ± 5.3_ | 3 |
| E3 | patch | Backdoored | None | - | 10.4 ± 3.9 | **86.3 ± 11.0** | 0.0 ± 0.0 | 0.4 ± 0.6 | _86.3 ± 11.0_ | 3 |
| E4 | patch | Backdoored | MAPU | - | 88.5 ± 18.3 | **6.7 ± 5.2** | 0.0 ± 0.0 | 0.4 ± 0.7 | _6.7 ± 5.2_ | 3 |
| E5 | patch | Backdoored | MAPU | Compression | 72.6 ± 24.4 | **26.4 ± 4.2** | 7.6 ± 12.2 | 0.7 ± 1.3 | _26.4 ± 4.2_ | 3 |
| E6 | patch | Backdoored | MAPU | Secure-MAPU | 94.2 ± 10.1 | **30.2 ± 29.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _30.2 ± 29.6_ | 3 |
| E7 | patch | Backdoored | MAPU | Consistency | 80.0 ± 19.2 | **5.6 ± 1.9** | 0.0 ± 0.0 | 0.0 ± 0.0 | _5.6 ± 1.9_ | 3 |
| E8 | patch | Backdoored | MAPU | Compress+Consistency | 61.4 ± 15.4 | **25.1 ± 17.0** | 3.3 ± 4.7 | 4.0 ± 4.4 | _25.1 ± 17.0_ | 3 |
| E9 | patch | Backdoored | MAPU | FT-SAM | 41.8 ± 19.0 | **44.1 ± 12.3** | 13.9 ± 15.0 | 13.9 ± 15.0 | _44.1 ± 12.3_ | 3 |
| E10 | patch | Backdoored | MAPU | Compression + consistency + KT | 84.4 ± 13.6 | **48.9 ± 22.6** | 0.0 ± 0.0 | 0.0 ± 0.0 | _48.9 ± 22.6_ | 3 |

Dataset har · scenario 12->16, 6->23, 7->13, 9->18 · mean ± std across seeds, all values %.

*Attack* is the trigger the source model was poisoned with and *ASR (installed)* is
its attack success rate. The `ctrl:` columns apply every trigger to every model as a
control. E1 and E2 use a clean source model.

Clean MF1 is macro-F1 on the target test split. ASR excludes windows whose true label
is already the target class.
