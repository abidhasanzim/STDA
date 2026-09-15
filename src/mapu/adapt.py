"""Target adaptation with MAPU, or SHOT-IM as an ablation.

Only the encoder is trained; the classifier and imputer stay frozen and target labels are
never used. The loss is information maximization plus, for MAPU, the temporal imputation
MSE. Defenses plug in through pseudo-labels, extra loss terms, step hooks and SAM.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from pathlib import Path
from typing import Any

import torch
from torch import nn
from torch.optim.lr_scheduler import StepLR

from src.data.loaders import DomainBundle, build_loaders
from src.defense.consistency import build_perturbation, consistency_loss
from src.defense.sam import build_sam, disable_running_stats, enable_running_stats
from src.mapu.losses import information_maximization
from src.mapu.masking import make_masker, random_spectral_mask
from src.models.imputer import build_imputer
from src.utils.checkpoint import load_ckpt, save_ckpt
from src.utils.config import apply_overrides, config_hash, flatten, load_config, load_yaml
from src.utils.seed import set_seed
from src.utils.tracking import start_run


def resolve_device(name: str) -> torch.device:
    if name == "cuda" and not torch.cuda.is_available():
        return torch.device("cpu")
    return torch.device(name)


@torch.no_grad()
def _acc_mf1(model: nn.Module, loader, device) -> tuple[float, float]:
    from src.eval.clean_acc import clean_accuracy

    r = clean_accuracy(model, loader, device)
    return r.accuracy, r.macro_f1


def adapt(
    ckpt_path: str | Path,
    cfg: dict[str, Any],
    out_path: str | Path | None = None,
    pseudo_labels: torch.Tensor | None = None,
    pseudo_label_ref: torch.Tensor | None = None,
    on_step_end: Callable[[nn.Module], None] | None = None,
    extra_loss: Callable[[nn.Module], torch.Tensor] | None = None,
    epoch_probe: Callable[[nn.Module], dict[str, float]] | None = None,
    tag: str = "",
) -> tuple[Path, dict[str, float]]:
    """Adapt a source checkpoint to the target domain.

    Args:
        pseudo_labels: optional labels for a cross-entropy term, indexed by target-train
            position.
        pseudo_label_ref: target-train windows the pseudo-labels were computed on; checked
            against this function's split.
        on_step_end: called after each optimizer step.
        extra_loss: called each step to add a regularizer.
    """
    train_cfg = {k: v for k, v in cfg.items() if k not in ("data", "model", "attack", "defense")}
    seed = int(train_cfg.get("seed", 42))
    set_seed(seed)
    device = resolve_device(str(train_cfg.get("device", "cuda")))
    method = str(train_cfg.get("method", "mapu")).lower()

    model, ckpt_cfg, scaler = load_ckpt(ckpt_path, map_location=device)
    model.to(device)
    data_cfg = dict(cfg.get("data") or ckpt_cfg["data"])
    data_cfg["batch_size"] = int(train_cfg.get("batch_size", data_cfg.get("batch_size", 32)))
    data_cfg["seed"] = seed
    bundle: DomainBundle = build_loaders(data_cfg, target_train_index=pseudo_labels is not None)

    if pseudo_labels is not None:
        n_train = len(bundle.target_train.dataset)
        if len(pseudo_labels) != n_train:
            raise ValueError(
                f"got {len(pseudo_labels)} pseudo-labels for {n_train} target-train windows"
            )
        if pseudo_label_ref is not None:
            mine = bundle.target_train_ordered.dataset.X
            ref = pseudo_label_ref.cpu()
            if mine.shape != ref.shape or not torch.equal(mine, ref):
                raise RuntimeError(
                    "pseudo-labels were computed on a different target-train split than the "
                    "one being adapted; they would be misaligned"
                )

    imputer = build_imputer(ckpt_cfg.get("model", {})).to(device)
    imp_state = torch.load(ckpt_path, map_location=device, weights_only=False).get("imputer")
    if imp_state is not None:
        imputer.load_state_dict(imp_state)
    elif method == "mapu":
        raise ValueError(f"{ckpt_path} carries no imputer; MAPU adaptation needs one")
    model.attach_imputer(imputer)

    # Freeze everything except the encoder.
    for p in model.classifier.parameters():
        p.requires_grad = False
    for p in imputer.parameters():
        p.requires_grad = False

    enc_params = [p for p in model.encoder.parameters() if p.requires_grad]
    lr = float(train_cfg.get("learning_rate", 1e-4))
    wd = float(train_cfg.get("weight_decay", 1e-4))

    # SAM is enabled when sam_rho > 0.
    sam_rho = float(train_cfg.get("sam_rho", 0.0))
    use_sam = sam_rho > 0
    if use_sam:
        opt = build_sam(
            enc_params,
            rho=sam_rho,
            lr=lr,
            weight_decay=wd,
            adaptive=bool(train_cfg.get("sam_adaptive", True)),
            base=str(train_cfg.get("sam_base", "adam")),
        )
    else:
        opt = torch.optim.Adam(enc_params, lr=lr, weight_decay=wd)
    sched = StepLR(
        opt.base_optimizer if use_sam else opt,
        step_size=int(train_cfg.get("step_size", 50)),
        gamma=float(train_cfg.get("lr_decay", 0.5)),
    )
    mse = nn.MSELoss()
    ce = nn.CrossEntropyLoss()

    epochs = int(train_cfg.get("epochs", 100))
    num_splits = int(train_cfg.get("num_splits", 8))
    num_masked = int(train_cfg.get("num_masked", 1))
    ent_wt = float(train_cfg.get("ent_loss_wt", 0.05897))
    im_wt = float(train_cfg.get("im", 0.2759))
    tov_wt = float(train_cfg.get("tov_wt", 0.5))
    kt_wt = float(train_cfg.get("kt_wt", 1.0))

    # Optional masking domain for the imputation task and spectral consistency weight.
    mask_domain = str(train_cfg.get("mask_domain", "time"))
    num_bands = int(train_cfg.get("num_bands", 8))
    num_masked_bands = int(train_cfg.get("num_masked_bands", 1))
    spec_consistency_wt = float(train_cfg.get("spec_consistency_wt", 0.0))

    # Perturbation consistency defense (src/defense/consistency.py).
    consistency_wt = float(train_cfg.get("consistency_wt", 0.0))
    perturb = None
    if consistency_wt > 0:
        perturb = build_perturbation(
            {
                "fs": float(data_cfg.get("sample_rate_hz", 50.0)),
                "amp_range": tuple(train_cfg.get("cons_amp_range", (0.5, 4.0))),
                "width_range": tuple(train_cfg.get("cons_width_range", (0.05, 0.30))),
                "families": tuple(
                    train_cfg.get("cons_families", ("patch", "sinusoid", "noise_segment"))
                ),
                "freq_exclude": train_cfg.get("cons_freq_exclude"),
            },
            channel_std=torch.as_tensor(scaler["std"]),
        )
    masker = make_masker(
        mask_domain,
        num_splits=num_splits,
        num_masked=num_masked,
        num_bands=num_bands,
        num_masked_bands=num_masked_bands,
    )

    name = Path(
        out_path
        or Path(train_cfg.get("out_dir", "checkpoints"))
        / f"adapted_{tag or method}_{data_cfg.get('name', 'ds')}_"
        f"s{data_cfg['source_subject']}t{data_cfg['target_subject']}_seed{seed}.pt"
    )

    scen = f"{data_cfg['source_subject']}->{data_cfg['target_subject']}"
    run_name = f"adapt[{tag or method}] {scen} seed{seed}"
    gen = torch.Generator(device=device).manual_seed(seed + 1)
    with start_run(str(train_cfg.get("mlflow_experiment", "sfda-audit")), run_name) as run:
        run.log_params(flatten({"data": data_cfg, "train": train_cfg}))
        run.set_tags(
            {
                "stage": "adapt",
                "method": method,
                "config_hash": config_hash(cfg),
                "source_ckpt": str(ckpt_path),
            }
        )

        if method != "none":
            for epoch in range(1, epochs + 1):
                model.train()
                # cuDNN needs the LSTM in train mode for backward, even with frozen weights.
                imputer.train()
                agg = dict.fromkeys(["im", "tov", "kt", "reg", "cons", "spec", "n"], 0.0)
                for batch in bundle.target_train:
                    if pseudo_labels is not None:
                        x, _y, idx = batch
                    else:
                        (x, _y), idx = batch, None
                    x = x.to(device)
                    nb = x.shape[0]

                    # Bind loop variables so the closure uses this iteration's values.
                    def _objective(x=x, idx=idx, nb=nb, agg=agg, record=False):
                        """The full adaptation loss. SAM calls this twice per step."""
                        flat, seq = model.encode(x)
                        logits = model.classifier(flat)
                        im_loss, _ = information_maximization(logits, ent_wt, im_wt)
                        total = im_loss
                        if record:
                            agg["im"] += float(im_loss) * nb

                        if method == "mapu":
                            seq_masked = model.encode(masker(x, gen))[1]
                            tov = mse(imputer(seq_masked), seq)
                            total = total + tov_wt * tov
                            if record:
                                agg["tov"] += float(tov) * nb

                        if perturb is not None:
                            cons, _ = consistency_loss(
                                model,
                                x,
                                seq,
                                logits,
                                perturb,
                                generator=gen,
                                feature_weight=float(train_cfg.get("cons_feature_wt", 1.0)),
                                prediction_weight=float(train_cfg.get("cons_pred_wt", 1.0)),
                            )
                            total = total + consistency_wt * cons
                            if record:
                                agg["cons"] += float(cons) * nb

                        if spec_consistency_wt > 0:
                            x_band, _ = random_spectral_mask(
                                x, num_bands, num_masked_bands, generator=gen
                            )
                            sc = mse(model.encode(x_band)[1], seq)
                            total = total + spec_consistency_wt * sc
                            if record:
                                agg["spec"] += float(sc) * nb

                        if pseudo_labels is not None:
                            kt = ce(logits, pseudo_labels[idx].to(device))
                            total = total + kt_wt * kt
                            if record:
                                agg["kt"] += float(kt) * nb

                        if extra_loss is not None:
                            reg = extra_loss(model)
                            total = total + reg
                            if record:
                                agg["reg"] += float(reg) * nb
                        return total

                    if use_sam:
                        # SAM: step to w + eps, then update with the gradient measured there.
                        opt.zero_grad(set_to_none=True)
                        _objective(record=True).backward()
                        opt.first_step(zero_grad=True)
                        disable_running_stats(model)
                        _objective().backward()
                        enable_running_stats(model)
                        opt.second_step(zero_grad=True)
                    else:
                        opt.zero_grad(set_to_none=True)
                        _objective(record=True).backward()
                        opt.step()

                    if on_step_end is not None:
                        on_step_end(model)
                    agg["n"] += nb

                sched.step()
                n = max(agg["n"], 1)
                acc, mf1 = _acc_mf1(model, bundle.target_test, device)
                metrics = {
                    "im_loss": agg["im"] / n,
                    "tov_loss": agg["tov"] / n,
                    "kt_loss": agg["kt"] / n,
                    "reg_loss": agg["reg"] / n,
                    "consistency_loss": agg["cons"] / n,
                    "spec_consistency_loss": agg["spec"] / n,
                    "target_test_acc": acc,
                    "target_test_mf1": mf1,
                    "lr": opt.param_groups[0]["lr"],
                    "sam_rho": sam_rho,
                }
                if epoch_probe is not None:
                    metrics.update(epoch_probe(model))
                run.log_metrics(metrics, step=epoch)
                if epoch % int(train_cfg.get("log_every", 20)) == 0 or epoch in (1, epochs):
                    print(
                        f"[adapt:{tag or method}] epoch {epoch:3d}/{epochs}  "
                        f"im {metrics['im_loss']:+.4f}  "
                        f"tov {metrics['tov_loss']:.4f}  tgt_acc {acc:.4f}  tgt_mf1 {mf1:.4f}"
                    )

        acc, mf1 = _acc_mf1(model, bundle.target_test, device)
        final = {"target_test_acc": acc, "target_test_mf1": mf1}
        full_cfg = {**ckpt_cfg, "adapt": train_cfg, "data": data_cfg}
        save_ckpt(
            name,
            model.cpu(),
            full_cfg,
            scaler,
            imputer=imputer.cpu(),
            notes=f"adapted:{tag or method}",
        )
        model.to(device)
        run.log_metrics(final)
        run.set_tags({"checkpoint": str(name)})

    print(json.dumps({"checkpoint": str(name), **final}, indent=2))
    return name, final


@torch.no_grad()
def collect_pseudo_labels(model: nn.Module, loader, device) -> torch.Tensor:
    """Hard predictions over a non-shuffled target-train loader."""
    model.eval()
    out = []
    for x, _ in loader:
        out.append(model(x.to(device)).argmax(1).cpu())
    return torch.cat(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ckpt", type=Path, required=True)
    ap.add_argument("--config", type=Path, default=Path("configs/train/mapu.yaml"))
    ap.add_argument("--method", type=str, default=None, choices=["mapu", "shot", "none"])
    ap.add_argument("--defense", type=Path, default=None, help="defense config yaml")
    ap.add_argument("--out", type=Path, default=None)
    ap.add_argument("--tag", type=str, default="")
    ap.add_argument("--set", nargs="*", default=None)
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.method:
        cfg["method"] = args.method
    if args.defense:
        cfg["defense"] = load_yaml(args.defense)
    cfg = apply_overrides(cfg, args.set)

    if cfg.get("defense"):
        from src.defense.secure_mapu import secure_adapt

        secure_adapt(args.ckpt, cfg, out_path=args.out, tag=args.tag or "secure")
    else:
        adapt(args.ckpt, cfg, out_path=args.out, tag=args.tag)


if __name__ == "__main__":
    main()
