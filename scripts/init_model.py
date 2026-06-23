"""Train an initial phishing_model.pkl using the real 31-feature extractor on curated example URLs."""
import os
import sys
import logging
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib
from datetime import datetime

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, PROJECT_DIR)

try:
    from backend.config import config
    MODEL_PATH = config.MODEL_PATH
except (ImportError, AttributeError):
    config = None
    MODEL_PATH = os.path.join(PROJECT_DIR, 'backend', 'phishing_model.pkl')

from backend.utils.feature_extractor import extract_features, FEATURE_NAMES

SAFE_URLS = [
    'https://github.com/opencode-ai/opencode',
    'https://google.com/search?q=test',
    'https://stackoverflow.com/questions/123',
    'https://www.wikipedia.org/wiki/Python',
    'https://docs.python.org/3/library/index.html',
    'https://medium.com/article-title-here',
    'https://www.amazon.com/product-name/dp/123456',
    'https://www.reddit.com/r/programming/',
    'https://www.linkedin.com/in/profile',
    'https://twitter.com/user/status/123456',
    'https://www.youtube.com/watch?v=xyz123',
    'https://www.microsoft.com/en-us/software-download',
    'https://www.apple.com/iphone/',
    'https://www.netflix.com/in/title/123456',
    'https://www.dropbox.com/s/abc123/file.pdf',
    'https://www.instagram.com/p/Cxyz/',
    'https://www.facebook.com/page-name',
    'https://www.w3schools.com/python/default.asp',
    'https://realpython.com/python-kwargs-and-args/',
    'https://www.npmjs.com/package/express',
    'https://pypi.org/project/requests/',
    'https://www.docker.com/products/docker-desktop/',
    'https://code.visualstudio.com/docs/editor/extension-marketplace',
    'https://www.postman.com/downloads/',
    'https://www.mongodb.com/docs/atlas/',
    'https://kubernetes.io/docs/home/',
    'https://www.terraform.io/docs',
    'https://aws.amazon.com/console/',
    'https://console.cloud.google.com/',
    'https://portal.azure.com/',
]

PHISHING_URLS = [
    'http://dghjdgf.com/paypal.co.uk/login',
    'https://secure-paypal-login.xyz/webscr',
    'http://192.168.1.1/login.php?redirect=bank.com',
    'http://free-laptop-giveaway.tk/claim',
    'https://account-verification-microsoft.ml/',
    'http://www.paypal-account-restore.ga/login',
    'https://amazon-secure-center.cf/reset',
    'http://bankofamerica-secure-login.top/verify',
    'http://apple-id-verify.xyz/confirm',
    'https://chase-online-banking.click/login',
    'http://wellsfargo-account-update.link/signin',
    'http://netflix-renewal.ga/payment',
    'https://dropbox-shared-file.xyz/document',
    'http://linkedin-security-check.cf/verify',
    'https://google-account-alert.gq/confirm',
    'http://instagram-verify.cam/login',
    'https://facebook-security.tk/checkpoint',
    'http://adobe-account-recovery.ml/reset',
    'https://ebay-auction-winner.xyz/claim',
    'http://citibank-alert.ga/secure',
    'https://update-payment-info.info/cgi-bin/webscr',
    'http://verify-identity-now.tk/login',
    'https://account-suspended-alert.ml/restore',
    'http://package-tracking-info.cf/delivery',
    'https://tax-refund-pending.xyz/claim',
    'http://win-iphone-14.ga/winner',
    'https://secure-server-login.top/auth',
    'http://dhl-package-alert.ml/track',
    'https://password-expired-alert.gq/reset',
    'http://account-update-required.cam/verify',
]

np.random.seed(42)

all_urls = SAFE_URLS + PHISHING_URLS
y_labels = [0] * len(SAFE_URLS) + [1] * len(PHISHING_URLS)

logger.info(f'Extracting features for {len(all_urls)} curated URLs...')
X = np.array([extract_features(url) for url in all_urls])

n_augmented = 200
logger.info(f'Augmenting with {n_augmented} synthetic noisy samples...')

rng = np.random.RandomState(42)
X_aug = np.zeros((n_augmented, len(FEATURE_NAMES)))
for i in range(n_augmented):
    base = X[rng.randint(0, len(X))]
    noise = rng.normal(0, 0.15, size=base.shape)
    X_aug[i] = np.clip(base + noise * np.abs(base + 1), 0, None)
y_aug = rng.randint(0, 2, size=n_augmented)

X_full = np.vstack([X, X_aug])
y_full = np.hstack([y_labels, y_aug])

model = RandomForestClassifier(
    n_estimators=100, max_depth=15, random_state=42, n_jobs=1
)
model.fit(X_full, y_full)

data = {
    'model': model,
    'feature_names': FEATURE_NAMES,
    'trained_at': datetime.now().isoformat(),
    'train_samples': len(X_full),
}

os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
joblib.dump(data, MODEL_PATH)
logger.info(f'Initial model saved to {MODEL_PATH} ({len(X_full)} samples, {len(FEATURE_NAMES)} features)')
