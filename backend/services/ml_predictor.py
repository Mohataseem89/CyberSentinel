import joblib
import os
import logging
from ml.feature_extractor import URLFeatureExtractor
# from .feature_extractor import URLFeatureExtractor

logger = logging.getLogger(__name__)

class MLPredictor:
    """Machine Learning based URL prediction"""
    def reload_model(self):
        """Reload model from disk after retraining"""
        try:
            print("[ML] Reloading model from disk...")
            self.load_model()
            print("[ML] Model reloaded successfully")
            return True
        except Exception as e:
            print("[ML] Reload failed:", e)
            self.model = None
            self.feature_columns = None
            return False
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.load_model()
    
    def load_model(self):
        try:
            BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            DATA_DIR = os.path.join(BASE_DIR, "data")

            MODEL_PATH = os.path.join(DATA_DIR, "phishing_model.pkl")
            FEATURE_COLUMNS_PATH = os.path.join(DATA_DIR, "feature_columns.pkl")

            print(f"Looking for model at: {MODEL_PATH}")
            print(f"Looking for feature columns at: {FEATURE_COLUMNS_PATH}")

            self.model = joblib.load(MODEL_PATH)
            self.feature_columns = joblib.load(FEATURE_COLUMNS_PATH)

            print("ML model loaded successfully")

        except Exception as e:
            print("ML model not found. Train the model first.")
            print("Error:", e)
            self.model = None
            self.feature_columns = None




            

    
    def predict(self, url):
        """
        Predict if URL is phishing using ML model
        Returns: dict with prediction and confidence
        """
        if not self.model:
            logger.warning("ML model not available")
            return {
                "score": 50,
                "prediction": "unknown",
                "confidence": 0.0,
                "message": "ML model not trained yet"
            }
        
        try:
            # Extract features
            extractor = URLFeatureExtractor()
            features = extractor.extract_features(url)
            
            # Convert to DataFrame with correct column order
            import pandas as pd
            features_df = pd.DataFrame([features])
            
            # Ensure all required features are present
            for col in self.feature_columns:
                if col not in features_df.columns:
                    features_df[col] = 0
            
            # Select only the columns used during training
            features_df = features_df[self.feature_columns]
            
            # Predict
            prediction = self.model.predict(features_df)[0]
            probabilities = self.model.predict_proba(features_df)[0]
            
            # Get confidence score
            confidence = max(probabilities)
            
            # calculate threat score (0-100, higher = more dangerous)
            if prediction == 1:  # Phishing
                threat_score = confidence * 100
            else:  # Legitimate
                threat_score = (1 - confidence) * 100
            
            result = {
                "score": threat_score,
                "prediction": "phishing" if prediction == 1 else "legitimate",
                "confidence": confidence,
                "probabilities": {
                    "legitimate": probabilities[0],
                    "phishing": probabilities[1]
                },
                "message": f"ML prediction: {threat_score:.1f}% threat level"
            }
            
            logger.info(f"ML prediction for {url}: {result['prediction']} ({confidence:.2%})")
            
            return result
            
        except Exception as e:
            logger.error(f"ML prediction error: {str(e)}")
            return {
                "score": 50,
                "prediction": "error",
                "confidence": 0.0,
                "message": f"Prediction failed: {str(e)}"
            }

# global predictor instance
predictor = MLPredictor()