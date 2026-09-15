"""Streamlit dashboard for auditing a checkpoint and browsing results.

streamlit run dashboard/app.py
"""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from src.eval.report import write_markdown_table  # noqa: E402
from src.eval.schema import load_runs  # noqa: E402
from src.eval.verdict import decide  # noqa: E402
from src.utils.config import load_yaml  # noqa: E402

st.set_page_config(page_title="Secure time-series domain adaptation", page_icon="🔎", layout="wide")

VERDICT_COLOR = {"PASS": "#2e7d32", "WARN": "#ef6c00", "FAIL": "#c62828"}


@st.cache_data(show_spinner=False)
def _run_audit(ckpt: str, device: str, seed: int):
    from src.experiments import audit_checkpoint

    eval_cfg = load_yaml(REPO / "configs/eval/audit.yaml")
    r = audit_checkpoint(
        ckpt,
        exp_id="dashboard",
        model_type="unknown",
        adaptation="none",
        defense="none",
        seed=seed,
        eval_cfg=eval_cfg,
        device=device,
    )
    return r.to_dict(), eval_cfg.get("thresholds")


st.title("🔎 Secure time-series domain adaptation")
st.caption(
    "Backdoor risk auditing for time-series transfer learning and domain adaptation. "
    "Defensive evaluation on public benchmarks only."
)

tab_audit, tab_results, tab_about = st.tabs(["Audit a checkpoint", "Experiment results", "About"])

with tab_audit:
    ckpts = (
        sorted(str(p) for p in (REPO / "checkpoints").glob("*.pt"))
        if (REPO / "checkpoints").exists()
        else []
    )
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        ckpt = st.selectbox("Checkpoint", ckpts) if ckpts else st.text_input("Checkpoint path")
    with col2:
        device = st.selectbox("Device", ["cuda", "cpu"])
    with col3:
        seed = st.number_input("Seed", value=42, step=1)

    if st.button("Run audit", type="primary", disabled=not ckpt):
        with st.spinner("Evaluating against every trigger family…"):
            d, thresholds = _run_audit(ckpt, device, int(seed))

        asr_by = {k: v["asr"] for k, v in d["asr"].items()}
        rate = next((v["clean_target_rate"] for v in d["asr"].values()), None)
        v = decide(asr_by, thresholds, rate)

        st.markdown(
            f"<h2 style='color:{VERDICT_COLOR.get(v.label, '#555')}'>{v.emoji} {v.label}</h2>"
            f"<p>{v.rationale}.</p>",
            unsafe_allow_html=True,
        )
        a, b, c = st.columns(3)
        a.metric("Clean accuracy", f"{d['clean_acc']:.1%}")
        b.metric("Clean macro-F1", f"{d['clean_mf1']:.1%}")
        c.metric("Worst-family ASR", f"{v.worst_asr:.1%}", delta=f"{v.worst_trigger}")

        st.subheader("Attack success rate by trigger family")
        rows = []
        for name, t in d["asr"].items():
            rows.append(
                {
                    "trigger": name,
                    "family": t["family"],
                    "ASR": t["asr"],
                    "CI low": t["asr_ci"][0],
                    "CI high": t["asr_ci"][1],
                    "inclusive ASR": t["asr_inclusive"],
                    "untriggered target rate": t["clean_target_rate"],
                    "lift": t["lift"],
                    "n eligible": t["n_eligible"],
                }
            )
        df = pd.DataFrame(rows).set_index("trigger")
        pct = {c: "{:.1%}" for c in df.columns if c not in ("family", "n eligible")}
        st.dataframe(df.style.format(pct))
        st.bar_chart(df["ASR"])

        st.caption(
            "ASR excludes windows whose true label is already the attacker's target class. "
            "'Untriggered target rate' is the null model: an ASR that only matches it is the "
            "classifier's prior, not an attack — which is what 'lift' shows."
        )

        st.subheader("Most backdoor-sensitive encoder channels")
        from src.defense.sensitivity import layer_scores, rank_channels
        from src.utils.checkpoint import load_ckpt

        m, _, _ = load_ckpt(ckpt)
        scores = layer_scores(m.encoder)
        rk = rank_channels(scores[max(scores)])[:10]
        st.dataframe(pd.DataFrame(rk, columns=["channel", "spectral norm"]).set_index("channel"))

with tab_results:
    runs_path = REPO / "results/runs.jsonl"
    runs = load_runs(runs_path)
    if not runs:
        st.info(f"No runs yet. Run `make reproduce` to populate {runs_path}.")
    else:
        st.write(f"{len(runs)} runs")
        table = write_markdown_table(runs, REPO / "results/table.md")
        st.markdown(table.read_text())
        fig = REPO / "results/tradeoff.png"
        if fig.exists():
            st.subheader("Security/utility tradeoff")
            st.image(str(fig))

with tab_about:
    st.markdown(
        (REPO / "docs/threat_model.md").read_text()
        if (REPO / "docs/threat_model.md").exists()
        else "See `docs/` in the repository."
    )
