import os
import sys
import json
import time
import logging
import numpy as np
import sqlite3
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

try:
    from backend.config import config
except ImportError:
    logger.error("Cannot import config. Run from project root.")
    sys.exit(1)

try:
    from backend.utils.feature_extractor import extract_features, FEATURE_NAMES
except ImportError:
    from utils.feature_extractor import extract_features, FEATURE_NAMES


def load_training_data(db_path, min_samples=50):
    if not os.path.exists(db_path):
        logger.warning(f'Database not found at {db_path}')
        return None, None

    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT url, ml_score, risk_score, rule_flags, ml_result FROM scans ORDER BY id DESC LIMIT 10000"
        ).fetchall()
    except Exception as e:
        logger.error(f'Query failed: {e}')
        conn.close()
        return None, None
    conn.close()

    if len(rows) < min_samples:
        logger.info(f'Only {len(rows)} scans (need {min_samples}), skipping retrain')
        return None, None

    X = []
    y = []
    for row in rows:
        url, ml_score, risk_score, rule_flags, ml_result = row
        features = extract_features(url)
        X.append(features)
        label = 1 if (risk_score > 50 or ml_result == 'phishing') else 0
        y.append(label)

    return np.array(X), np.array(y)


def retrain_model(X, y):
    from sklearn.ensemble import RandomForestClassifier

    logger.info(f'Training on {len(X)} samples...')
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=20,
        random_state=42,
        n_jobs=1,
        class_weight='balanced'
    )
    model.fit(X, y)
    return model


def save_retrained_model(model, output_path, num_samples=0):
    import joblib
    data = {
        'model': model,
        'feature_names': FEATURE_NAMES,
        'trained_at': datetime.now().isoformat(),
        'train_samples': num_samples
    }
    joblib.dump(data, output_path)
    logger.info(f'Model saved to {output_path} with {num_samples} samples')


def main():
    logger.info('=' * 50)
    logger.info('Auto-Retrain Pipeline Started')
    logger.info('=' * 50)

    db_path = config.DATABASE_PATH
    model_path = config.MODEL_PATH
    backup_model_path = model_path.replace('.pkl', '_backup.pkl')

    if os.path.exists(model_path):
        import shutil
        shutil.copy2(model_path, backup_model_path)
        logger.info(f'Backup saved to {backup_model_path}')

    X, y = load_training_data(db_path)
    if X is None or len(X) < 50:
        logger.info('Insufficient data. Pipeline complete — no retrain.')
        return

    model = retrain_model(X, y)
    save_retrained_model(model, model_path, num_samples=len(X))
    logger.info(f'Retrain complete: {len(X)} samples → {model_path}')


if __name__ == '__main__':
    main()
