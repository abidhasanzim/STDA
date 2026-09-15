### E8 with 5-15 Hz removed from the consistency perturbations

Freq ASR is pooled over pairs and seeds for models poisoned with the 10 Hz trigger.
Worst-trigger ASR is the highest seed-mean ASR of the three triggers on a pair,
averaged over pairs. Clean MF1 is pooled over all runs.

| Pairs | Variant | Freq ASR (%) | Mean worst-trigger ASR (%) | Clean MF1 |
|---|---|---|---|---|
| tuning (1) | E8 | 5.1 | 5.1 | 100.0 |
| tuning (1) | E8, 5-15 Hz excluded | 14.7 | 14.7 | 100.0 |
| development (4) | E8 | 15.4 | 16.7 | 68.4 |
| development (4) | E8, 5-15 Hz excluded | 17.8 | 19.2 | 68.3 |
| test (5) | E8 | 6.5 | 13.2 | 86.3 |
| test (5) | E8, 5-15 Hz excluded | 8.6 | 13.7 | 86.3 |
