import joblib
import os
import logging
from ml_model.feature_extractor import URLFeatureExtractor
# from .feature_extractor import URLFeatureExtractor

logger = logging.getLogger(__name__)

class MLPredictor:
    """Machine Learning based URL prediction"""
    
    def __init__(self):
        self.model = None
        self.feature_columns = None
        self.load_model()
    
    def load_model(self):
        try:
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(current_dir)

            model_path = os.path.join(backend_dir, "phishing_model.pkl")
            features_path = os.path.join(backend_dir, "feature_columns.pkl")

            print("Looking for model at:", model_path)

            self.model = joblib.load(model_path)
            self.feature_columns = joblib.load(features_path)

            print(" ML model loaded successfully")

        except Exception as e:
            print(" ML model not found. Train the model first.")
            print("Error:", e)
            self.model = None

    
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