import os
import sys
import pandas as pd
import numpy as np
import joblib
import warnings
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix

sys.path.insert(0, os.path.dirname(__file__))

from utils.feature_extractor import extract_features, FEATURE_NAMES

warnings.filterwarnings('ignore')

DATASET_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'phishing_site_urls.csv')
MODEL_OUTPUT_PATH = os.path.join(os.path.dirname(__file__), 'phishing_model.pkl')


def main():
    print('=' * 60)
    print('PhishGuard - Model Training')
    print('=' * 60)

    if not os.path.exists(DATASET_PATH):
        print(f'Error: Dataset not found at {DATASET_PATH}')
        print('Please place phishing_site_urls.csv in the data/ directory')
        return

    print(f'\nLoading dataset from {DATASET_PATH}')
    df = pd.read_csv(DATASET_PATH)

    print(f'\nTotal rows: {len(df)}')
    print(f'Duplicates: {df.duplicated().sum()}')
    df = df.drop_duplicates()
    print(f'After dedup: {len(df)}')

    print(f'\nLabel distribution:')
    print(df['Label'].value_counts())

    df['Label'] = df['Label'].map({'good': 0, 'bad': 1})

    print('\nExtracting features...')
    X = np.array([extract_features(url) for url in df['URL']])
    y = df['Label'].values

    print(f'Feature matrix shape: {X.shape}')

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    print(f'\nTraining samples: {len(X_train)}, Test samples: {len(X_test)}')

    print('\nTraining Random Forest Classifier...')
    model = RandomForestClassifier(
        n_estimators=150,
        max_depth=20,
        min_samples_split=5,
        min_samples_leaf=4,
        n_jobs=-1,
        random_state=42,
        verbose=1
    )
    model.fit(X_train, y_train)

    print('\n' + '=' * 60)
    print('EVALUATION RESULTS')
    print('=' * 60)

    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)
    print(f'\nAccuracy: {accuracy:.4f} ({accuracy * 100:.2f}%)')

    print('\nConfusion Matrix:')
    cm = confusion_matrix(y_test, y_pred)
    print(f'  True Negatives (Safe): {cm[0][0]}')
    print(f'  False Positives:       {cm[0][1]}')
    print(f'  False Negatives:       {cm[1][0]}')
    print(f'  True Positives (Phish): {cm[1][1]}')

    print('\nClassification Report:')
    print(classification_report(y_test, y_pred, target_names=['Good (Safe)', 'Bad (Phishing)']))

    print('\n' + '-' * 60)
    print('Top 15 Most Important Features:')
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    for i in range(min(15, len(FEATURE_NAMES))):
        print(f'  {i+1}. {FEATURE_NAMES[indices[i]]}: {importances[indices[i]]:.4f}')

    model_data = {
        'model': model,
        'feature_names': FEATURE_NAMES
    }

    os.makedirs(os.path.dirname(MODEL_OUTPUT_PATH), exist_ok=True)
    joblib.dump(model_data, MODEL_OUTPUT_PATH)
    print(f'\nModel saved to {MODEL_OUTPUT_PATH}')
    print('\nTraining complete!')


if __name__ == '__main__':
    main()
