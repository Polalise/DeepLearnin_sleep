# Codex Rules

## 0. Deep Learning Project Refocus Rules

Last updated: 2026-06-29

- This project must be treated as a deep learning project.
- Traditional machine-learning models are allowed only as baseline/reference models.
- The current traditional ML baseline is:

```text
wearable_only + Logistic Regression
```

- The following models/results must not be described as deep learning results:
  - DummyClassifier
  - Logistic Regression
  - Logistic Regression + PCA
  - Random Forest
  - GridSearchCV tuning for Logistic Regression or Random Forest
- PCA is allowed as exploratory preprocessing analysis for feature structure, variance, correlation, and feature-family inspection.
- PCA should not be treated as a required deep learning input step unless the user explicitly asks for a PCA-based experiment.
- The main deep learning path should start from daily participant-level data before PCA:

```text
data/processed/modeling_dataset_missing_handled.csv
data/processed/modeling_dataset_encoded.csv
```

- Deep learning sequence datasets should follow this path:

```text
participant-date daily table
-> sort by participant and date
-> build rolling windows, such as 7/14/30 days
-> create X with shape samples x time_steps x features
-> create y from good_sleep_label
-> keep participant-aware train/validation/test split
```

- Deep learning models to prioritize:
  - MLP baseline on daily tabular features
  - SimpleRNN
  - LSTM
  - GRU
  - BiLSTM
  - 1D CNN on rolling windows
  - Transformer encoder only if data volume is sufficient
- Future reports must clearly separate:
  - preprocessing completed
  - exploratory PCA completed
  - traditional ML baseline completed
  - deep learning data preparation completed
  - deep learning modeling not yet completed
- When continuing in a new conversation, first read:
  - `Codex.Rule.md`
  - latest `log/YYYY-MM-DD.md`
  - `notebooks/02_pipeline_from_scripts_summary.ipynb`
- If files are created or modified, append the change to the matching daily log.

## 1. Encoding Rules

- All Python scripts, notebooks, markdown reports, and logs must be written as UTF-8.
- When Python reads or writes project text files, use `encoding="utf-8"` unless a specific file format requires otherwise.
- For CSV outputs opened by spreadsheet tools, `utf-8-sig` is acceptable.
- Do not write notebooks or Python files using CP949, EUC-KR, or terminal-default encodings.
- If Korean text is used in notebooks or reports, verify that the saved file does not contain mojibake or replacement text such as repeated `?` characters.
- If encoding damage is found, rewrite the affected section in clean UTF-8 text before continuing.

## 2. Work Log Rules

- Whenever Codex creates or modifies files, append the work details to the matching daily log file unless the user explicitly asks not to.
- Daily log file format:

```text
log/YYYY-MM-DD.md
```

- Logs should include at least:
  - created or modified files
  - reason for the work
  - major changes
  - commands or validation results, if any

## 3. Data Source Rules

- For LifeSnaps analysis, prefer checking the restored MongoDB/BSON source over relying only on CSV files when source structure matters.
- Default MongoDB connection information:

```text
mongodb://localhost:27017
Database: rais_anonymized
```

- Do not load the entire `fitbit` collection into pandas at once if it is too large.
- First inspect document structure by `type`, then filter to the needed `type` values before loading.

## 4. Commenting Rules

- When the user asks for code, include comments around data loading, preprocessing, and model-training steps.
- Comments should explain why a step is done, not merely repeat what the code says.
- The same standard applies to Python scripts and Jupyter notebooks.
- Keep comments readable and UTF-8 encoded.

## 5. Data Preservation And Preprocessing Rules

- Treat files under `data/raw/` as source-like data and do not modify them directly.
- Store first-stage MongoDB extraction outputs under `data/raw/`.
- Store filtered, missing-handled, labeled, feature-engineered, or model-ready outputs under `data/processed/`.
- File names should make the purpose clear, for example:

```text
data/processed/sleep_target_table.csv
data/processed/sleep_features_with_stress_hrv.csv
```

- Before starting new preprocessing work, clarify the target output file for that step.
- Document target definition, feature inclusion/exclusion, missing-value rules, and leakage risks in reports.

## 6. Report Rules

- After major analysis stages, create or update summary documents under `reports/`.
- Useful report examples:

```text
reports/eda_summary.md
reports/preprocessing_summary.md
reports/model_baseline_summary.md
reports/deep_learning_model_comparison_report.md
```

- Reports should include, when relevant:
  - data source
  - input files
  - output files
  - preprocessing rules
  - target definition
  - feature list or feature-family summary
  - train/validation/test split method
  - evaluation metrics
  - main results
  - limitations
- When reporting numeric results, state which file or split they were computed from.
- If stress-related features are used, explicitly mention possible sleep/recovery leakage.

## 7. Modeling Rules

- The default split must be participant-aware.
- Do not use random row-level splits as the default because rows from the same participant are correlated.
- Traditional ML models are allowed only as baseline/reference models.
- Deep learning model comparisons should use the saved rolling sequence tensors unless a different experiment is explicitly requested.
- Primary model-selection metric should default to balanced accuracy unless the user changes the target objective.
- Secondary metrics should include ROC AUC, average precision, F1, precision, recall, and confusion matrix.
- Use validation-first model selection, then evaluate the selected candidate once on the held-out test split.

## 8. Notebook And Script Operation Rules

- Early exploration and distribution checks may be done in notebooks.
- Deterministic preprocessing and modeling logic should be moved into reproducible scripts when it becomes stable.
- Scripts should be rerunnable from the same inputs to the same output paths.
- If a notebook or important script is created or modified, update:
  - `log/YYYY-MM-DD.md`
  - `notebooks/02_pipeline_from_scripts_summary.ipynb`, when it affects the pipeline summary
