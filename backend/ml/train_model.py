import os
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib

from feature_extractor import URLFeatureExtractor


def train_phishing_model():
    """
    Train Random Forest model on final merged phishing dataset
    """
    print("Loading dataset...")

    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(current_dir)
    data_dir = os.path.join(backend_dir, "data")

    dataset_path = os.path.join(data_dir, "final_training_dataset.csv")
    model_path = os.path.join(data_dir, "phishing_model.pkl")
    feature_columns_path = os.path.join(data_dir, "feature_columns.pkl")

    print(f"Dataset path: {dataset_path}")

    if not os.path.exists(dataset_path):
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")

    df = pd.read_csv(dataset_path)

    print(f"Total URLs: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    if "url" not in df.columns or "label" not in df.columns:
        raise ValueError("Dataset must contain 'url' and 'label' columns")

    print("Extracting features...")
    extractor = URLFeatureExtractor()

    features_list = []
    labels = []

    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"Processed {idx}/{len(df)} URLs...")

        try:
            url = str(row["url"]).strip()
            label = str(row["label"]).strip().lower()

            if not url or not label:
                continue

            features = extractor.extract_features(url)
            features_list.append(features)
            labels.append(label)
        except Exception:
            continue

    features_df = pd.DataFrame(features_list)

    print(f"\nFeatures extracted: {features_df.shape}")
    print(f"Feature columns count: {len(features_df.columns)}")

    X_train, X_test, y_train, y_test = train_test_split(
        features_df,
        labels,
        test_size=0.2,
        random_state=42,
        stratify=labels if len(set(labels)) > 1 else None
    )

    print(f"\nTraining set: {len(X_train)}")
    print(f"Test set: {len(X_test)}")

    print("\nTraining Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )

    model.fit(X_train, y_train)

    print("\nEvaluating model...")
    y_pred = model.predict(X_test)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"\nAccuracy: {accuracy:.2%}")

    print("\nClassification Report:")
    print(classification_report(y_test, y_pred))

    feature_importance = pd.DataFrame({
        "feature": features_df.columns,
        "importance": model.feature_importances_
    }).sort_values("importance", ascending=False)

    print("\nTop 10 Important Features:")
    print(feature_importance.head(10))

    print("\nSaving model...")
    joblib.dump(model, model_path)
    joblib.dump(features_df.columns.tolist(), feature_columns_path)

    print("\nModel saved successfully!")
    print(f"Model file: {model_path}")
    print(f"Features file: {feature_columns_path}")

    return model, accuracy


if __name__ == "__main__":
    train_phishing_model()