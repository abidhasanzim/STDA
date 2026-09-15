# Implementation notes

This project re-implements MAPU and SSDA based on their papers and released code
([MAPU_SFDA_TS](https://github.com/mohamedr002/MAPU_SFDA_TS),
[SSDA](https://github.com/ML-Security-Research-LAB/SSDA)).

## MAPU settings for UCI HAR

Values taken from `configs/data_model_configs.py` and `configs/hparams.py` in the MAPU code:

| Setting | Value |
|---|---|
| Encoder | 3 conv blocks, 64/128/128 channels, first kernel 5, stride 1, dropout 0.5 |
| Pooling | `AdaptiveAvgPool1d(1)`; the imputer uses the pre-pool map (128 x 18) |
| Imputer | single-layer LSTM, hidden size 128 |
| Masking | 8 equal time blocks, 1 masked per channel (shared across the batch) |
| Epochs / batch size / weight decay | 100 / 32 / 1e-4 |
| Source learning rate | 1e-3 |
| Adaptation learning rate | 1e-4, StepLR(step_size=50, gamma=0.5) |
| Loss weights | entropy 0.05897, diversity 0.2759, imputation 0.5 |
| Source loss | cross-entropy with label smoothing 0.1 |

The paper text lists 40 epochs, but the released HAR config uses 100. MAPU's adaptation loss is
information maximization plus imputation, with no pseudo-label term. Full SHOT also trains on
pseudo-labels; the A1 ablation uses SHOT-IM, its information-maximization loss alone.

## Differences from the released MAPU code

1. **Imputation gradient during source training.** The paper says the imputation loss does not
   update the encoder. The code detaches only the masked branch, so gradient reaches the encoder
   through the clean features. This implementation detaches both by default
   (`detach_clean_target: true` in `configs/train/source.yaml`).
2. **Imputer input shape.** The released imputer reshapes `(N, 128, 18)` with `view` and uses an
   LSTM without `batch_first`, which mixes the channel, time and batch axes. Here the features
   are transposed and `batch_first=True` is used. `imputer_legacy_view: true` restores the
   original behaviour.
3. **Normalization.** The AdaTime loaders normalize every domain with its own statistics. Here
   statistics come from the source training split and are stored with the model, and
   normalization happens inside the model.
4. **Masking.** Because normalization is inside the model, masking is applied to the raw signal.
   A masked block therefore reaches the encoder as `-mean/std` for its channel instead of 0.

## SSDA

- **Compression.** For each conv layer, every output channel's weight `(C_in, k)` is scored by its
  largest singular value, and channels above `mean + gamma * std` of the layer's scores are
  zeroed (`gamma = 1`). The following BatchNorm parameters are zeroed as well, so the channel
  outputs zero and receives no gradient during adaptation.
- **Spectral penalty.** SSDA replaces the spectral norm with `trace(W^T W)`, citing the bound
  `sigma_max(W) <= trace(W^T W)`. That bound does not hold in general (a matrix with a single
  singular value of 0.5 violates it), and the quantity is a squared Frobenius norm. Both the
  trace version and the exact spectral norm are implemented (`spectral_mode`).
- **Lambda.** SSDA uses lambda = 100. On this encoder that value prevents the defense from
  working (see the report), so experiment E6 uses lambda = 1.

## Evaluation choices

- ASR excludes test windows whose true label is already the target class. The inclusive rate
  and the untriggered target-class rate are reported alongside.
- Clean performance is reported as macro-F1, as in MAPU and AdaTime, together with accuracy.
- Splits are made by contiguous recording segment to avoid overlap between train and test
  windows.
