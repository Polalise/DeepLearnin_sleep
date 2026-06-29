from pathlib import Path
import argparse
import json

import joblib
import numpy as np
import pandas as pd
import torch
from torch import nn


class PreSleepMLP(nn.Module):
    def __init__(self, input_dim, hidden_dims=(24, 12), dropout=0.40):
        super().__init__()

        layers = []
        current_dim = input_dim

        for hidden_dim in hidden_dims:
            layers.extend(
                [
                    nn.Linear(current_dim, hidden_dim),
                    nn.BatchNorm1d(hidden_dim),
                    nn.ReLU(),
                    nn.Dropout(dropout),
                ]
            )
            current_dim = hidden_dim

        layers.append(nn.Linear(current_dim, 1))
        self.network = nn.Sequential(*layers)

    def forward(self, x):
        return self.network(x).squeeze(-1)


class PreSleepInferencePipeline:
    def __init__(self, project_root=None, manifest_path=None, device="cpu"):
        self.project_root = Path(project_root) if project_root else Path(__file__).resolve().parents[2]
        self.device = torch.device(device)

        if manifest_path is None:
            manifest_path = (
                self.project_root
                / "data"
                / "processed"
                / "pre_sleep_forecasting"
                / "design_c_stage1"
                / "inference_package"
                / "pre_sleep_inference_manifest.json"
            )

        self.manifest_path = Path(manifest_path)
        self.manifest = json.loads(self.manifest_path.read_text(encoding="utf-8"))

        self.raw_features = self.manifest["raw_feature_order"]
        self.removed_features = set(self.manifest["zero_variance_removed_features"])
        self.final_features = self.manifest["final_model_feature_order"]
        self.threshold = float(self.manifest["official_threshold"])

        artifact_paths = self.manifest["artifact_paths"]
        self.imputer = joblib.load(self.project_root / artifact_paths["imputer"])
        self.scaler = joblib.load(self.project_root / artifact_paths["scaler"])

        checkpoint_path = self.project_root / artifact_paths["model_checkpoint"]
        self.checkpoint = torch.load(checkpoint_path, map_location=self.device)

        self.model = PreSleepMLP(
            input_dim=int(self.checkpoint["input_dim"]),
            hidden_dims=tuple(self.checkpoint["hidden_dims"]),
            dropout=float(self.checkpoint["dropout"]),
        ).to(self.device)

        self.model.load_state_dict(self.checkpoint["state_dict"])
        self.model.eval()

        self._validate_contract()

    def _validate_contract(self):
        computed_final = [
            feature for feature in self.raw_features
            if feature not in self.removed_features
        ]

        if computed_final != self.final_features:
            raise ValueError("Feature contract mismatch: computed final features do not match manifest.")

        if len(self.raw_features) != self.imputer.n_features_in_:
            raise ValueError("Raw feature count does not match imputer.")

        if len(self.raw_features) != self.scaler.n_features_in_:
            raise ValueError("Raw feature count does not match scaler.")

        if len(self.final_features) != int(self.checkpoint["input_dim"]):
            raise ValueError("Final feature count does not match model input_dim.")

    def transform_raw_features(self, raw_feature_df):
        missing_columns = [
            feature for feature in self.raw_features
            if feature not in raw_feature_df.columns
        ]

        if missing_columns:
            raise ValueError(f"Missing required raw feature columns: {missing_columns}")

        raw_matrix = raw_feature_df[self.raw_features].copy()
        imputed = self.imputer.transform(raw_matrix)
        scaled = self.scaler.transform(imputed).astype(np.float32)

        keep_mask = np.array([
            feature not in self.removed_features
            for feature in self.raw_features
        ])

        model_matrix = scaled[:, keep_mask]

        if model_matrix.shape[1] != len(self.final_features):
            raise ValueError("Transformed model feature count mismatch.")

        return model_matrix

    def predict_proba(self, raw_feature_df):
        model_matrix = self.transform_raw_features(raw_feature_df)

        with torch.no_grad():
            x = torch.tensor(model_matrix, dtype=torch.float32).to(self.device)
            logits = self.model(x)
            probabilities = torch.sigmoid(logits).cpu().numpy()

        return probabilities

    def predict(self, raw_feature_df, threshold=None):
        if threshold is None:
            threshold = self.threshold

        probabilities = self.predict_proba(raw_feature_df)
        predictions = (probabilities >= threshold).astype(int)

        output = pd.DataFrame(
            {
                "good_sleep_probability": probabilities,
                "good_sleep_pred": predictions,
                "threshold": float(threshold),
            }
        )

        passthrough_columns = [
            column for column in [
                "sleep_episode_id",
                "participant_object_id",
                "sleep_start_datetime",
                "prediction_cutoff_datetime",
            ]
            if column in raw_feature_df.columns
        ]

        if passthrough_columns:
            output = pd.concat(
                [
                    raw_feature_df[passthrough_columns].reset_index(drop=True),
                    output,
                ],
                axis=1,
            )

        return output


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="CSV containing 70 raw Stage 1 inference features.")
    parser.add_argument("--output", required=True, help="Output prediction CSV path.")
    parser.add_argument("--project-root", default=None)
    parser.add_argument("--manifest", default=None)
    parser.add_argument("--threshold", type=float, default=None)
    args = parser.parse_args()

    pipeline = PreSleepInferencePipeline(
        project_root=args.project_root,
        manifest_path=args.manifest,
    )

    input_df = pd.read_csv(args.input, encoding="utf-8-sig")
    prediction_df = pipeline.predict(input_df, threshold=args.threshold)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    prediction_df.to_csv(output_path, index=False, encoding="utf-8-sig")

    print("predictions written:", output_path)
    print("rows:", len(prediction_df))
    print("threshold:", args.threshold if args.threshold is not None else pipeline.threshold)


if __name__ == "__main__":
    main()