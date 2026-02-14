import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix
import joblib
from feature_extractor import URLFeatureExtractor

def train_phishing_model():
    """
    Train Random Forest model on phishing dataset
    """
    print(" Loading dataset...")
    # df = pd.read_csv('url_dataset.csv')
    current_dir = os.path.dirname(os.path.abspath(__file__))
    dataset_path = os.path.join(current_dir, "url_dataset.csv")

    df = pd.read_csv(dataset_path)
    
    print(f"Total URLs: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")
    
    # Extract features for all URLs
    print("🔧 Extracting features...")
    extractor = URLFeatureExtractor()
    
    features_list = []
    labels = []
    
    for idx, row in df.iterrows():
        if idx % 1000 == 0:
            print(f"Processed {idx}/{len(df)} URLs...")
        
        try:
            url = row['url']
            label = row['label']  # Adjust column name based on dataset
            
            features = extractor.extract_features(url)
            features_list.append(features)
            labels.append(label)
        except:
            continue
    
    # Convert to DataFrame
    features_df = pd.DataFrame(features_list)
    
    print(f"\n Features extracted: {features_df.shape}")
    print(f"Feature columns: {features_df.columns.tolist()}")
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        features_df, labels, test_size=0.2, random_state=42
    )
    
    print(f"\n Training set: {len(X_train)}")
    print(f" Test set: {len(X_test)}")
    
    # Train Random Forest
    print("\n Training Random Forest model...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=-1
    )
    
    model.fit(X_train, y_train)
    
    # Evaluate
    print("\n Evaluating model...")
    y_pred = model.predict(X_test)
    
    accuracy = accuracy_score(y_test, y_pred)
    print(f"\n Accuracy: {accuracy:.2%}")
    
    print("\n Classification Report:")
    print(classification_report(y_test, y_pred))
    
    # Feature importance
    feature_importance = pd.DataFrame({
        'feature': features_df.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)
    
    print("\n🔝 Top 10 Important Features:")
    print(feature_importance.head(10))
    
    # Save model
    print("\n Saving model...")
    joblib.dump(model, 'phishing_model.pkl')
    joblib.dump(features_df.columns.tolist(), 'feature_columns.pkl')
    
    print("\n Model saved successfully!")
    print(f"Model file: phishing_model.pkl")
    print(f"Features file: feature_columns.pkl")
    
    return model, accuracy

if __name__ == "__main__":
    train_phishing_model()