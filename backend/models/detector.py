import os
import logging
import numpy as np
import joblib

logger = logging.getLogger(__name__)


class PhishingDetector:
    def __init__(self, model_path):
        self.model_path = model_path
        self.model = None
        self.feature_names = None
        self.load_model()

    def load_model(self):
        if not os.path.exists(self.model_path):
            logger.warning(f'Model not found at {self.model_path}')
            self.model = None
            return

        try:
            data = joblib.load(self.model_path)
            self.model = data['model']
            if hasattr(self.model, 'n_jobs'):
                self.model.n_jobs = 1
                logger.info('Set model n_jobs=1 for Windows compatibility')
            self.feature_names = data.get('feature_names')
            logger.info(f'Model loaded from {self.model_path}')
        except Exception as e:
            logger.error(f'Failed to load model: {e}')
            self.model = None

    def is_loaded(self):
        return self.model is not None

    def predict(self, features):
        if not self.is_loaded():
            return None, 'Model not loaded'

        features_array = np.array([features])
        proba = self.model.predict_proba(features_array)[0]
        pred = self.model.predict(features_array)[0]

        phishing_prob = round(float(proba[1]) * 100, 1)
        safe_prob = round(float(proba[0]) * 100, 1)
        label = 'phishing' if pred == 1 else 'safe'

        return {
            'prediction': label,
            'phishing_probability': phishing_prob,
            'safe_probability': safe_prob
        }, None
