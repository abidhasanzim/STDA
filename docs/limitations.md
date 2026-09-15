# Limitations

## What a verdict means

A FAIL shows that at least one tested trigger still controls the model. A PASS only means the
tested triggers do not; it does not show that the model is free of backdoors.

## Attacks

- Three fixed triggers (patch, gaussian segment, 10 Hz sinusoid) with one target class.
  Optimized or sample-specific triggers (TimeTrojan, TSBA, FreqBack), warping triggers and
  all-to-all backdoors are not evaluated.
- The frequency trigger uses a single fixed frequency. FreqBack reports that effective
  frequencies depend on the architecture, so an attacker could likely choose a stronger one.
- No adaptive attacker. An attacker who knows the defenses could spread the trigger over
  low-sensitivity channels or pick a perturbation outside the family used by the consistency
  defense. The defenses would likely be much less effective against such an attack.

## Defenses

- The consistency defense trains against additive or replacement perturbations that are
  short in time or narrowband in frequency. Triggers outside that family are not covered, and
  the evaluated freq trigger (10 Hz, 0.25 std) lies inside the sampled ranges. Removing
  5-15 Hz from the draws changes little on the development and test pairs, but raises freq ASR
  on 2 → 11 from 5.1% to 14.7% (report section 4.4), and the amplitude range still covers the
  trigger.
- The settings of E6-E9 were chosen by looking at ASR and clean accuracy on labeled test data
  from subject 11, for the same trigger families that are reported: the consistency weight and
  amplitude range, the compression strength (k = 16), E6's lambda = 1 and FT-SAM's rho = 4.
  They were first picked on a shuffled window-level split of that subject, before the
  segment-level split was adopted. The consistency weight and amplitude range, the lambda
  sweep and the k sweep were re-run on the reported split; rho was not re-checked.
- E10 was chosen among five variants using labeled test data from the five MAPU pairs. The five
  test pairs were run once, after E10 was fixed, and were not used for any choice. They are
  not fully independent of the development pairs: subject 18 is a development target and a
  test source, and two test pairs share target subject 27.
- There is no held-out trigger. All defenses were chosen and evaluated on the same three
  trigger families.
- The SSDA ablation and the lambda sweep use a single seed.

## Data and evaluation

- One dataset (UCI HAR), ten subject pairs and one backbone. Results may not carry over to
  other sensors, longer sequences, other architectures or other kinds of domain shift.
- Results vary a lot between subject pairs, and pooled numbers hide failures: on 9 → 18, E8
  leaves a worst-trigger ASR of 36.5% and lowers macro-F1 to 52.0.
- Target test splits have 79-105 windows (86-88 for subject 11), of which 66-92 are used for
  ASR. Confidence intervals are wide, and differences of a few points between defenses are
  within noise.
- Within a single subject, activities are easy to separate: on subject 11 a raw-signal
  1-nearest-neighbour classifier scores about 0.95 even on the leakage-free split (0.55 across
  subjects). High clean accuracy on that subject mostly reflects this.
- Only MAPU and SHOT-IM are evaluated. The finding about the imputation loss is specific to
  MAPU.

## Implementation

- Where the released MAPU code differs from the paper, this implementation follows the paper,
  so numbers are not directly comparable with the official code. See
  [reproduction_notes.md](reproduction_notes.md).
- Normalization statistics are fit on the source training split only, unlike AdaTime, which
  normalizes each domain with its own statistics.
- `torch.use_deterministic_algorithms` runs with `warn_only=True`, so some CUDA operations are
  not bit-reproducible. CPU runs are.

## Verdict thresholds

The FAIL (ASR above 50%) and WARN (above 20%) thresholds are defaults, not calibrated values.
They can be changed in `configs/eval/audit.yaml`.
