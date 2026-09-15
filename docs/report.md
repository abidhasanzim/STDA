# Secure time-series domain adaptation: results

## 1. Question

In source-free domain adaptation (SFDA) a model trained on a labeled source domain is adapted
to a target domain using only unlabeled target data. The party adapting the model usually did
not train it and cannot inspect the source data. This report asks two questions:

1. Does a backdoor planted during source training survive adaptation to a new domain?
2. Which defenses remove it without reducing clean accuracy?
3. Do defense settings chosen on one pair of subjects carry over to other pairs?

## 2. Setup

**Data.** UCI HAR: 10,299 windows of 9 inertial channels (128 samples at 50 Hz), 6 activity
classes, 30 subjects. Each subject is a domain. Section 3 adapts from subject 2 to subject
11, one of the five cross-person pairs used by MAPU. Section 4 repeats the experiments on MAPU's
other four pairs and on the five further HAR pairs defined by AdaTime.

**Splits.** Windows overlap by 50%, so each subject is split by contiguous recording segment
and any test window that still overlaps a training window is removed. The target test split
of subject 11 has 86-88 windows, about 27% of the subject (a segment-level split cannot hit the
configured 0.2 exactly); on the other pairs it has 79-105 windows. A shuffled window-level split would leave 93-95% of test windows overlapping a
training window (`scripts/check_split_leakage.py`).

**Model.** The AdaTime 1D CNN (three Conv1d-BatchNorm-ReLU-MaxPool blocks, 200,902 parameters)
with a linear classifier and an LSTM imputer, using the MAPU hyperparameters for HAR.
Normalization statistics are fit on the source training split and stored in the checkpoint.

**Adaptation.** MAPU trains only the encoder with

    L = 0.05897 H(p) - 0.2759 H(mean p) + 0.5 MSE(imputer(enc(mask(x))), enc(x))

for 100 epochs (Adam, learning rate 1e-4). The A1 ablation uses SHOT-IM, SHOT's
information-maximization loss without its pseudo-label step. It is this loss without the
imputation term, so it keeps MAPU's entropy and diversity weights rather than SHOT's equal
weighting.

**Attacks.** Each attack poisons part of the source training set with a trigger and relabels
it as WALKING (class 0):

| Trigger | Description | Poison rate | Source clean acc | Source ASR |
|---|---|---|---|---|
| patch | square pulse, 3 channels, 10 samples, 3 std | 15% | 99.6 ± 0.7 | 96.7 ± 0.9 |
| gaussian | noise segment replacing 16 samples on all channels, 0.5 of range | 15% | 100.0 ± 0.0 | 98.1 ± 0.8 |
| freq | 10 Hz sinusoid on all channels, 0.25 std | 10% | 100.0 ± 0.0 | 86.2 ± 10.8 |

Poison rates are fractions of the non-WALKING source training windows; as a share of all
source training windows they are about 12% (patch, gaussian) and 8% (freq).

**Metrics.** ASR is the fraction of triggered target test windows classified as the target
class, over windows that are not already of that class. Clean accuracy and macro-F1 are
measured on untriggered target test windows. Every experiment uses seeds 42, 43 and 44.

**Harness check.** On the bundled test fixture, randomly initialized models give 0.194 clean
accuracy and 0.160 ASR on average (chance is 0.167), so the evaluation does not create signal
on its own.

**Tuning.** The defense hyperparameters of E6-E9 were chosen using labeled test data from
subject 11, so the results in section 3 are likely optimistic for them. Section 4 evaluates the
same settings on pairs that were not used for that choice. See [limitations.md](limitations.md).

## 3. Results on subject 2 → 11

<!-- headline-table -->
Attack success rate (%) on the target domain, lower is better.
3 seeds, mean ± std; clean MF1 is pooled over the three triggers. Scenario 2->11.

| Defense | patch | gaussian | freq | Clean MF1 |
|---|---|---|---|---|
| **E3** no adaptation | 99.5 ± 0.8 | 100.0 ± 0.0 | 86.3 ± 11.9 | 74.3 ± 6.3 |
| **E4** MAPU (no defense) | 1.4 ± 0.0 | 0.5 ± 0.8 | 80.2 ± 5.0 | 100.0 ± 0.0 |
| **A1** SHOT-IM (ablation) | 70.3 ± 2.7 | 87.0 ± 11.8 | 97.6 ± 2.1 | 100.0 ± 0.0 |
| **E5** + spectral-norm compression | 17.1 ± 14.8 | 1.4 ± 1.4 | 52.3 ± 30.6 | 100.0 ± 0.0 |
| **E6** + Secure-MAPU (SSDA, ICCV'23) | 8.4 ± 8.6 | 4.8 ± 4.4 | 52.8 ± 29.5 | 100.0 ± 0.0 |
| **E9** + FT-SAM (ICCV'23) | 6.2 ± 7.2 | 20.7 ± 2.9 | 73.1 ± 1.7 | 90.7 ± 12.9 |
| **E7** + perturbation consistency | 0.9 ± 0.8 | 0.0 ± 0.0 | 37.5 ± 37.6 | 100.0 ± 0.0 |
| **E8** + compression & consistency | **3.3 ± 1.7** | **0.0 ± 0.0** | **5.1 ± 8.8** | **100.0 ± 0.0** |
| **E10** + compression & consistency & KT | 35.2 ± 22.6 | 0.5 ± 0.8 | 31.3 ± 15.5 | 97.9 ± 5.0 |
<!-- headline-table -->

Clean models reach 78.2 macro-F1 on the target subject without adaptation (E1) and 100.0
with MAPU (E2). All adapted models except E9 (90.7) and E10 (97.9, introduced in section 4)
keep 100.0 macro-F1.

### 3.1 Backdoors survive the domain shift

Before adaptation (E3) the triggers reach 99.5%, 100.0% and 86.3% ASR on the target subject,
from source models that score 99.6-100% on clean source data.

### 3.2 MAPU removes time-localized triggers only

After MAPU adaptation (E4) the patch and gaussian triggers fall to 1.4% and 0.5%. The freq
trigger stays at 80.2%. MAPU zeroes one of eight time blocks per channel and trains the
encoder so the frozen imputer can reconstruct the missing features. A trigger confined to a
short span is sometimes completely hidden by the mask, while a sinusoid across all 128
samples is never fully removed. This is a likely explanation rather than something tested
directly.

### 3.3 The imputation term is responsible

Adapting with SHOT-IM (A1), which has no imputation term, leaves the patch trigger at 70.3%
and the gaussian trigger at 87.0%, against 1.4% and 0.5% with MAPU.
The removal comes from the imputation objective, not from adaptation in general.

### 3.4 Channel compression plateaus

Compression zeroes the encoder channels with the largest spectral norm. With SSDA's threshold
(E5) the freq trigger stays at 52.3%. Sweeping the number of zeroed channels per layer (k) on
the freq trigger:

| k | 0 | 4 | 8 | 16 | 24 | 32 | 40 | 48 | 64 |
|---|---|---|---|---|---|---|---|---|---|
| ASR | 80.2 | 60.2 | 49.9 | 32.2 | 30.0 | 29.1 | 22.4 | 37.0 | 0.0 |
| Clean MF1 | 100.0 | 100.0 | 100.0 | 100.0 | 99.6 | 97.3 | 73.1 | 48.7 | 4.3 |

ASR levels off around 30% for k=16-32 while accuracy holds. Its lowest value before the model
collapses is 22.4% at k=40, where macro-F1 has already dropped to 73.1, and it rises again at
k=48. The 0% at k=64 is a model at chance level. See `results/compression_curve.png`.

### 3.5 SSDA needs its penalty weight retuned

SSDA combines compression, knowledge transfer from an uncompressed auxiliary model and a
spectral-norm penalty with weight lambda = 100. On this encoder the penalty is around 40, so
lambda = 100 dominates the loss and the encoder barely moves from its backdoored weights.
Patch trigger, seed 42:

| lambda | 0 | 1e-4 | 1e-3 | 1e-2 | 1e-1 | 1 | 100 |
|---|---|---|---|---|---|---|---|
| ASR (with knowledge transfer) | 39.4 | 38.0 | 25.4 | 22.5 | 15.5 | 1.4 | 97.2 |
| ASR (without) | 4.2 | 4.2 | 1.4 | 1.4 | 1.4 | 40.8 | 100.0 |

Clean macro-F1 is 100.0 in every cell except the last (98.8), so the failure at lambda = 100
is not visible from accuracy. E6 uses lambda = 1. Even then it leaves the freq trigger at
52.8%, the same as compression alone.

### 3.6 FT-SAM

FT-SAM fine-tunes with adaptive sharpness-aware minimization. It normally uses labeled clean
data; here the optimizer is applied to the unsupervised MAPU loss, with rho = 4. It lowers the
freq trigger from 80.2% to 73.1% but raises the gaussian trigger from 0.5% to 20.7% and the
patch trigger from 1.4% to 6.2% (mostly one seed at 14.5%). Clean macro-F1 drops to 90.7.
Part of the gaussian ASR is the degraded model predicting WALKING without any trigger: the
mean lift over the untriggered rate is 14.1 points.

rho = 4 was chosen with a single-seed sweep on the freq trigger before the segment-level split
was adopted and was not re-checked, so FT-SAM may be under-tuned in these comparisons.

### 3.7 Perturbation consistency

During adaptation each batch is perturbed with a randomly generated patch, sinusoid or noise
segment (random channels, amplitude, position, width, frequency and phase), and the encoder is
trained to produce the same features as on the clean batch (weight 0.1, amplitudes 0.1-1.5
std). The parameters are drawn at random rather than copied from the evaluated triggers, but
the ranges are wide: sinusoids are drawn from 0.5 to 24.5 Hz at 0.1-1.5 std, which covers the
freq trigger (10 Hz, 0.25 std). The patch trigger's 3 std amplitude is outside the range.
Section 4.4 reruns E8 with the band around 10 Hz removed.

Alone (E7) this brings the freq trigger to 37.5% and removes the other two. Combined with
compression of the top 16 channels per layer (E8) every trigger is at 5.1% or below, with
clean macro-F1 unchanged at 100.0. Neither component reaches this on its own.

## 4. Other subject pairs

### 4.1 Protocol

The settings above were tuned on 2 → 11, where MAPU already reaches 100 macro-F1, so an
accuracy cost of a defense cannot show up there. The experiment matrix was therefore run on
more pairs, with every config unchanged:

1. **Development pairs.** MAPU's other four HAR pairs: 6 → 23, 7 → 13, 9 → 18 and 12 → 16.
2. **Selection.** Five variants of E8 that use no target labels were run on all five MAPU pairs
   (`scripts/select_defense.py`): E8 itself, E8 with knowledge transfer from an uncompressed
   adapted model, consistency with knowledge transfer and no compression, and E8 with k = 8
   with and without knowledge transfer. The rule was written down before these runs: among
   variants whose pooled clean macro-F1 is within 2 points of E4, take the lowest mean
   worst-trigger ASR. It chose E8 with knowledge transfer, which is E10
   (`configs/defense/combined_kt.yaml`).
3. **Test pairs.** AdaTime's five other HAR pairs, 18 → 27, 20 → 5, 24 → 8, 28 → 27 and
   30 → 20, run once after E10 was committed.

The worst-trigger ASR of a pair is the highest seed-mean ASR of the three installed triggers.
It is the number an attacker who can pick the trigger would get.

### 4.2 Development pairs

<!-- dev-summary -->
Summary over 4 subject pairs (6->23, 7->13, 9->18, 12->16). Worst-trigger ASR is the
highest seed-mean ASR of the three triggers on a pair; clean MF1 is pooled over all runs.

| Defense | Mean worst-trigger ASR (%) | Pairs with worst-trigger ASR ≤ 20% | Clean MF1 |
|---|---|---|---|
| **E3** no adaptation | 92.5 | 0 of 4 | 61.3 |
| **E4** MAPU (no defense) | 66.7 | 0 of 4 | 80.4 |
| **A1** SHOT-IM (ablation) | 94.1 | 0 of 4 | 77.5 |
| **E5** + spectral-norm compression | 37.6 | 1 of 4 | 71.6 |
| **E6** + Secure-MAPU (SSDA, ICCV'23) | 38.9 | 1 of 4 | 84.6 |
| **E9** + FT-SAM (ICCV'23) | 55.0 | 0 of 4 | 61.6 |
| **E7** + perturbation consistency | 27.7 | 1 of 4 | 74.1 |
| **E8** + compression & consistency | 16.7 | 3 of 4 | 68.4 |
| **E10** + compression & consistency & KT | 34.1 | 0 of 4 | 80.1 |
<!-- dev-summary -->

With the settings from 2 → 11, E8 still gives the lowest mean worst-trigger ASR, but clean
macro-F1 falls from 80.4 to 68.4. The cost is largest on 9 → 18, where E8 leaves a
worst-trigger ASR of 36.5% and lowers macro-F1 to 52.0.

In the selection ([results/selection.md](../results/selection.md)), E8 had a mean worst-trigger
ASR of 14.4% at 74.7 pooled macro-F1 over the five MAPU pairs, against 69.4% at 84.3 for E4.
Only the variants with knowledge transfer stayed within 2 points of E4's macro-F1; the best
of them, E10, had 34.3% at 83.7. E8 with k = 8 and no knowledge transfer had 14.2% at 78.7 but
missed the accuracy bound.

### 4.3 Test pairs

<!-- test-summary -->
Summary over 5 subject pairs (18->27, 20->5, 24->8, 28->27, 30->20). Worst-trigger ASR is the
highest seed-mean ASR of the three triggers on a pair; clean MF1 is pooled over all runs.

| Defense | Mean worst-trigger ASR (%) | Pairs with worst-trigger ASR ≤ 20% | Clean MF1 |
|---|---|---|---|
| **E3** no adaptation | 96.9 | 0 of 5 | 86.8 |
| **E4** MAPU (no defense) | 53.1 | 0 of 5 | 91.5 |
| **A1** SHOT-IM (ablation) | 84.5 | 0 of 5 | 87.5 |
| **E5** + spectral-norm compression | 25.1 | 2 of 5 | 89.9 |
| **E6** + Secure-MAPU (SSDA, ICCV'23) | 31.5 | 1 of 5 | 89.1 |
| **E9** + FT-SAM (ICCV'23) | 44.1 | 0 of 5 | 78.7 |
| **E7** + perturbation consistency | 20.0 | 3 of 5 | 91.8 |
| **E8** + compression & consistency | 13.2 | 4 of 5 | 86.3 |
| **E10** + compression & consistency & KT | 17.7 | 3 of 5 | 89.9 |
<!-- test-summary -->

On pairs that played no part in any choice, MAPU alone leaves a mean worst-trigger ASR of
53.1%. E8 lowers it to 13.2% and is below 20% on four of the five pairs, at a cost of about
5 points of macro-F1 (86.3 against 91.5). E10 reaches 17.7% at 89.9, and consistency alone
(E7) 20.0% at 91.8. SSDA (E6, 31.5%) and FT-SAM (E9, 44.1%) remove less, and FT-SAM lowers
macro-F1 the most, with the caveat on its rho from section 3.6. Per pair, E8 is highest on 28 → 27 (20.9%) and E10 on 20 → 5 (35.5%).
Per-trigger results are in [results/test_table.md](../results/test_table.md).

The test pairs share some subjects with the development pairs: subject 18 is a development
target and a test source, and subject 27 is the target of two test pairs.

### 4.4 Does E8 rely on covering the freq trigger?

E8 was rerun on all ten pairs with sinusoid frequencies between 5 and 15 Hz removed from the
perturbations, using `scripts/ablate_consistency_band.py`; the full table is in
[results/band_ablation.md](../results/band_ablation.md). The run and its reporting were decided
before it started. Freq ASR rises from 5.1% to 14.7% on
2 → 11, from 15.4% to 17.8% on the development pairs and from 6.5% to 8.6% on the test pairs,
against 80.2%, 66.7% and 53.1% for MAPU alone. The mean worst-trigger ASR on the test pairs
moves from 13.2% to 13.7% and clean macro-F1 does not change. So most of the effect on the
freq trigger does not depend on drawing its frequency, although the amplitude range still
covers it.

## 5. Related work

Backdoors in transfer learning for time series have been shown before: Active Poisoning
(Jiang et al., 2023) carries a periodic trigger through cross-subject adaptation for EEG. SSDA,
AdaptGuard and CLGA defend against backdoors during adaptation, but for images. Time-series
backdoor defenses such as TimeGuard and the unlearning defense in TrojanTime do not involve
domain adaptation and assume access to the poisoned training data. We did not find prior work
that studies how MAPU's imputation objective affects backdoors, or that defends time-series
models against backdoors during adaptation.

CLP (Zheng et al., 2022) is the basis of the compression step. It assumes the backdoor is
concentrated in a few channels with large Lipschitz constants; the plateau in 3.4 suggests
this does not hold for a trigger spread over the whole window.

## 6. Implementation notes

The encoder, imputer, masking and hyperparameters follow the released MAPU code. Where the code
and the paper differ, this implementation follows the paper; the differences are listed in
[reproduction_notes.md](reproduction_notes.md).

## 7. Conclusion

A backdoor trained into a time-series source model transfers to new subjects. MAPU's
imputation objective removes triggers that are short in time but not a trigger spread over
the whole window. Channel compression, SSDA and FT-SAM leave much of that trigger in place.
Adding a consistency loss on random trigger-like perturbations to channel compression removes
the most: all three triggers fall to 5.1% ASR or below on the tuning pair, and the mean
worst-trigger ASR on five held-out pairs falls from 53.1% to 13.2%, at a cost of about 5 points
of macro-F1. Adding knowledge transfer keeps more accuracy and removes less. These results hold
within the limits described in [limitations.md](limitations.md).
