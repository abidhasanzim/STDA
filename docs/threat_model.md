# Threat model

## Setting

A model is trained on labeled source data and then adapted to a target domain using only
unlabeled target data, as in source-free domain adaptation. The party adapting the model
did not train it and has no access to the source data.

| | Source model owner (attacker) | Model user (defender) |
|---|---|---|
| Controls | source data and labels, training, the released checkpoint | unlabeled target data, the adaptation procedure |
| Knows | architecture, task, label set | checkpoint weights and config |
| Does not have | target data | source data, target labels |

## Attack

The attacker adds a trigger to a fraction of the source training windows and relabels them
to a target class. The resulting model performs normally on clean data, so the backdoor is
not visible from accuracy. At test time, inputs containing the trigger are classified as the
target class. Triggers are added to raw sensor signals, before normalization.

## Defender

The defender can inspect the weights, run the model on unlabeled target data and change the
adaptation procedure. They cannot measure accuracy on labeled target data or inspect the
source training set. The defenses in this project need no source data or target labels when
they run, but their hyperparameters were chosen using labeled target test data from the
tuning and development pairs. The test pairs were not used for any choice (see
[limitations.md](limitations.md)).

## Assumptions about the checkpoint

By default the audit uses information stored in the checkpoint: the dataset path, the
normalization statistics and, for backdoored models, the statistics used to build the
trigger. The dataset can be overridden with `--target-data`. A checkpoint with a
misleading config could therefore affect the audit; this is not defended against.

## Out of scope

- Poisoned target data (see Sheng et al., *Protecting Model Adaptation from Trojans in the
  Unlabeled Data*).
- Adaptive attacks designed against these defenses.
- Adversarial examples, model extraction and membership inference.

All experiments use the public UCI HAR dataset and locally trained models. The only network
access in the repository is `scripts/download_har.sh`, which downloads the dataset.
