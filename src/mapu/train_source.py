"""Train a source model and its temporal imputer, optionally on poisoned data.

Each batch runs a classification loss for the encoder and classifier and an imputation
loss for the imputer. By default the imputation loss does not reach the encoder
(detach_clean_target=True), as described in the MAPU paper.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import torch
from torch import nn

from src.attack import build_trigger
from src.attack.poison import make_poison_fn
from src.data.loaders import DomainBundle, build_loaders
from src.mapu.losses import CrossEntropyLabelSmooth
from src.mapu.masking import random_mask
from src.models.imputer import build_imputer
from src.models.model import build_model
from src.utils.checkpoint import save_ckpt
from src.utils.config import apply_overrides, config_hash, flatten, load_config, load_yaml
from src.utils.seed import set_seed
from src.utils.tracking import start_run


def resolve_device(name: str) -> torch.device:
    if name == "cuda" and not torch.cuda.is_available():
        print("[train_source] cuda requested but unavailable; falling back to cpu")
        return torch.device("cpu")
    return torch.device(name)


@torch.no_grad()
def evaluate_acc(model: nn.Module, loader, device: torch.device) -> float:
    model.eval()
    correct = total = 0
    for x, y in loader:
        pred = model(x.to(device)).argmax(1).cpu()
        correct += int((pred == y).sum())
        total += int(y.numel())
    return correct / max(total, 1)


def train_source(
    cfg: dict[str, Any],
    out_path: str | Path | None = None,
    tag: str | None = None,
) -> tuple[Path, dict[str, float]]:
    train_cfg = {k: v for k, v in cfg.items() if k not in ("data", "model", "attack", "defense")}
    seed = int(train_cfg.get("seed", 42))
    set_seed(seed)
    device = resolve_device(str(train_cfg.get("device", "cuda")))

    data_cfg = dict(cfg["data"])
    data_cfg["batch_size"] = int(train_cfg.get("batch_size", data_cfg.get("batch_size", 32)))
    data_cfg["seed"] = seed
    model_cfg = dict(cfg["model"])

    attack_cfg = cfg.get("attack")
    poison_fn = None
    trigger = None
    if attack_cfg:
        # Build the trigger from the clean source statistics and record them, because the
        # scaler saved with the model is fit on the poisoned data and differs slightly.
        clean_bundle = build_loaders(data_cfg)
        std = torch.as_tensor(clean_bundle.scaler["std"])
        attack_cfg = {**attack_cfg, "channel_std": [float(v) for v in std]}
        trigger = build_trigger(attack_cfg, channel_std=std)
        poison_fn = make_poison_fn(
            trigger,
            int(attack_cfg["target_class"]),
            float(attack_cfg["poison_rate"]),
            seed=int(attack_cfg.get("seed", seed)),
        )
    tag = tag or ("bd" if attack_cfg else "clean")

    bundle: DomainBundle = build_loaders(data_cfg, poison_fn=poison_fn)
    poison_report = poison_fn.state["report"].as_dict() if poison_fn else None
    if poison_report:
        print(
            f"[train_source] poisoned {poison_report['n_poisoned']}/{poison_report['n_total']} "
            f"source-train windows -> class {poison_report['target_class']}"
        )

    model = build_model(model_cfg, data_cfg).to(device)
    model.set_scaler(bundle.scaler)
    imputer = build_imputer(model_cfg).to(device)
    model.attach_imputer(imputer)

    lr = float(train_cfg.get("pre_learning_rate", train_cfg.get("lr", 1e-3)))
    wd = float(train_cfg.get("weight_decay", train_cfg.get("wd", 1e-4)))
    epochs = int(train_cfg.get("epochs", 100))
    num_splits = int(train_cfg.get("num_splits", 8))
    num_masked = int(train_cfg.get("num_masked", 1))
    detach_clean = bool(train_cfg.get("detach_clean_target", True))

    main_params = list(model.encoder.parameters()) + list(model.classifier.parameters())
    opt_main = torch.optim.Adam(main_params, lr=lr, weight_decay=wd)
    opt_imp = torch.optim.Adam(imputer.parameters(), lr=lr, weight_decay=wd)
    criterion = CrossEntropyLabelSmooth(
        bundle.n_classes, epsilon=float(train_cfg.get("label_smoothing", 0.1))
    )
    mse = nn.MSELoss()

    src_subj = data_cfg["source_subject"]
    name = Path(
        out_path
        or Path(train_cfg.get("out_dir", "checkpoints"))
        / f"source_{tag}_{data_cfg.get('name', 'ds')}_s{src_subj}_seed{seed}.pt"
    )

    scen = f"{src_subj}->{data_cfg['target_subject']}"
    run_name = f"train_source[{tag}] {data_cfg.get('name')} {scen} seed{seed}"
    with start_run(str(train_cfg.get("mlflow_experiment", "sfda-audit")), run_name) as run:
        run.log_params(flatten({"data": data_cfg, "model": model_cfg, "train": train_cfg}))
        run.set_tags({"stage": "train_source", "source_kind": tag, "config_hash": config_hash(cfg)})
        if attack_cfg:
            run.log_params(flatten({"attack": attack_cfg}))

        log_every = int(train_cfg.get("log_every", 20))
        gen = torch.Generator(device=device).manual_seed(seed)
        for epoch in range(1, epochs + 1):
            model.train()
            imputer.train()
            agg = {"cls": 0.0, "imp": 0.0, "acc": 0.0, "n": 0.0}
            for x, y in bundle.source_train:
                x, y = x.to(device), y.to(device)

                opt_main.zero_grad(set_to_none=True)
                opt_imp.zero_grad(set_to_none=True)

                flat, seq_clean = model.encode(x)
                logits = model.classifier(flat)
                cls_loss = criterion(logits, y)

                # Imputation: the masked branch is always detached; detaching the clean target
                # keeps the imputation loss away from the encoder.
                x_masked, _ = random_mask(x, num_splits, num_masked, generator=gen)
                seq_masked = model.encode(x_masked)[1].detach()
                target = seq_clean.detach() if detach_clean else seq_clean
                imp_loss = mse(imputer(seq_masked), target)

                (cls_loss + imp_loss).backward()
                opt_main.step()
                opt_imp.step()

                agg["cls"] += float(cls_loss) * y.numel()
                agg["imp"] += float(imp_loss) * y.numel()
                agg["acc"] += float((logits.argmax(1) == y).sum())
                agg["n"] += y.numel()

            n = max(agg["n"], 1)
            metrics = {
                "cls_loss": agg["cls"] / n,
                "imp_loss": agg["imp"] / n,
                "train_acc": agg["acc"] / n,
                "source_test_acc": evaluate_acc(model, bundle.source_test, device),
            }
            run.log_metrics(metrics, step=epoch)
            if epoch % log_every == 0 or epoch in (1, epochs):
                print(
                    f"[train_source] epoch {epoch:3d}/{epochs}  cls {metrics['cls_loss']:.4f}  "
                    f"imp {metrics['imp_loss']:.4f}  train_acc {metrics['train_acc']:.4f}  "
                    f"src_test_acc {metrics['source_test_acc']:.4f}"
                )

        final = {
            "source_test_acc": evaluate_acc(model, bundle.source_test, device),
            "source_train_acc": evaluate_acc(model, bundle.source_train, device),
        }
        # Attack success rate on the source domain.
        if trigger is not None:
            from src.eval.asr import attack_success_rate

            r = attack_success_rate(
                model, bundle.source_test, trigger, int(attack_cfg["target_class"]), device
            )
            final["source_asr"] = r.asr
            final["source_clean_target_rate"] = r.clean_target_rate

        full_cfg = {
            "data": data_cfg,
            "model": model_cfg,
            "train": train_cfg,
            "attack": attack_cfg,
            "source_kind": tag,
            "poison_report": poison_report,
        }
        save_ckpt(
            name,
            model.cpu(),
            full_cfg,
            bundle.scaler,
            imputer=imputer.cpu(),
            notes=f"source_kind={tag}",
        )
        run.log_metrics(final)
        run.set_tags({"checkpoint": str(name)})
        run.log_artifact(name)

    print(json.dumps({"checkpoint": str(name), **final}, indent=2))
    return name, final


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", type=Path, default=Path("configs/train/source.yaml"))
    ap.add_argument(
        "--attack",
        type=Path,
        default=None,
        help="attack config (e.g. configs/attack/patch.yaml); omit to train a clean source model",
    )
    ap.add_argument("--out", type=Path, default=None, help="checkpoint path override")
    ap.add_argument("--tag", type=str, default=None, help="checkpoint name tag (default clean/bd)")
    ap.add_argument("--set", nargs="*", default=None, help="dotted overrides, e.g. epochs=10")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.attack:
        cfg["attack"] = load_yaml(args.attack)
        cfg["attack"]["_source"] = str(args.attack)
    cfg = apply_overrides(cfg, args.set)
    train_source(cfg, out_path=args.out, tag=args.tag)


if __name__ == "__main__":
    main()
