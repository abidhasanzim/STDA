### Defense selection on the development pairs

Pairs 12->16, 2->11, 6->23, 7->13, 9->18; 3 triggers x 3 seeds each. Worst-trigger ASR is the highest seed-mean ASR
of the three installed triggers on a pair, averaged over pairs. Clean MF1 is pooled.

| Variant | Mean worst-trigger ASR | Clean MF1 | 12->16 | 2->11 | 6->23 | 7->13 | 9->18 |
|---|---|---|---|---|---|---|---|
| E4 (MAPU, no defense) | 69.4 | 84.3 | 63.9 | 80.2 | 37.8 | 84.9 | 80.3 |
| compress+consistency | 14.4 | 74.7 | 15.1 | 5.1 | 14.7 | 0.4 | 36.5 |
| compress+consistency+kt (selected) | 34.3 | 83.7 | 36.3 | 35.2 | 23.2 | 25.7 | 51.3 |
| consistency+kt | 56.9 | 83.5 | 67.5 | 55.7 | 30.1 | 54.6 | 76.3 |
| compress8+consistency | 14.2 | 78.7 | 12.3 | 16.4 | 10.0 | 4.7 | 27.6 |
| compress8+consistency+kt | 40.7 | 83.5 | 44.3 | 44.7 | 19.0 | 33.1 | 62.6 |

Selected by the rule in scripts/select_defense.py (within 2 points of E4's clean MF1): `compress+consistency+kt`.
