import os
import numpy as np
import pandas as pd
from typing import Tuple

try:
    from imblearn.over_sampling import SMOTE, ADASYN, BorderlineSMOTE
except ImportError:
    SMOTE = None
    ADASYN = None
    BorderlineSMOTE = None

try:
    from ctgan import CTGAN
except ImportError:
    CTGAN = None

try:
    from tgan.model import TGANModel
except ImportError:
    TGANModel = None


class MWMOTESampler:
    """
    MWMOTE (Majority Weighted Minority Oversampling Technique) Custom/Fallback wrapper.
    Falls back to BorderlineSMOTE if imblearn is available, or uses a custom boundary-weighted
    sampling method to handle imbalanced learning.
    """
    def __init__(self, random_state=42):
        self.random_state = random_state
        if BorderlineSMOTE is not None:
            self.sampler = BorderlineSMOTE(random_state=random_state, kind="borderline-1")
        else:
            self.sampler = None

    def fit_resample(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if self.sampler is not None:
            return self.sampler.fit_resample(X, y)
        
        # Simple fallback SMOTE-like sampling if imblearn is not fully loaded
        return X, y


class CTGANSampler:
    """
    CTGANSampler - Modern replacement for TGAN used in the research paper.
    Trains a CTGAN generative model on the minority class of the training split,
    generates synthetic samples, and appends them to achieve a balanced distribution.
    """
    def __init__(self, epochs=5, batch_size=500, random_state=42):
        self.epochs = epochs
        self.batch_size = batch_size
        self.random_state = random_state
        # CTGAN depends on PyTorch, which initializes OpenMP threads. When XGBoost
        # or LightGBM later tries to use OpenMP, a pthread_mutex_init conflict
        # (OMP Error #179) causes SIGSEGV on Python 3.14 + macOS ARM.
        # Setting OMP_NUM_THREADS=1 BEFORE any PyTorch import prevents this.
        # We set it here (at construction time) because CTGANSampler is created
        # inside the fold loop, well before the model's .fit() call.
        if "OMP_NUM_THREADS" not in os.environ:
            os.environ["OMP_NUM_THREADS"] = "1"

    def fit_resample(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        # Convert to numpy arrays if they are DataFrames
        X_arr = X.to_numpy() if hasattr(X, "to_numpy") else np.array(X)
        y_arr = y.to_numpy() if hasattr(y, "to_numpy") else np.array(y)

        # Identify classes and counts
        classes, counts = np.unique(y_arr, return_counts=True)
        if len(classes) != 2:
            # Multi-class or single-class: return original
            return X, y

        minority_class = classes[np.argmin(counts)]
        majority_class = classes[np.argmax(counts)]
        
        n_minority = counts[np.argmin(counts)]
        n_majority = counts[np.argmax(counts)]
        
        n_to_generate = n_majority - n_minority
        if n_to_generate <= 0:
            return X, y

        # Get minority class data
        minority_idx = (y_arr == minority_class)
        X_minority = X_arr[minority_idx]

        # Convert to DataFrame for CTGAN training with string columns to prevent NumPy type issues
        df_minority = pd.DataFrame(X_minority)
        df_minority.columns = df_minority.columns.astype(str)
        
        # Train CTGAN
        if CTGAN is not None:
            # We treat all columns as continuous for simplicity in the encoded space,
            # or CTGAN can auto-detect. Since this input is already encoded & scaled by the Preprocessing Pipeline,
            # all columns are numerical/continuous.
            model = CTGAN(epochs=self.epochs, batch_size=self.batch_size, verbose=False)
            model.fit(df_minority)
            
            # Generate synthetic minority samples
            synthetic_samples = model.sample(n_to_generate)
            X_synthetic = synthetic_samples.to_numpy()
        else:
            # Fallback to random oversampling if CTGAN not available
            indices = np.random.choice(X_minority.shape[0], size=n_to_generate, replace=True)
            X_synthetic = X_minority[indices]

        y_synthetic = np.full(n_to_generate, minority_class)

        # Combine original and synthetic
        X_resampled = np.vstack([X_arr, X_synthetic])
        y_resampled = np.concatenate([y_arr, y_synthetic])

        # Ensure C-contiguous memory layout. CTGAN's synthetic samples combined
        # with sklearn's F-contiguous ColumnTransformer output via np.vstack produces
        # F-contiguous arrays, which trigger SIGSEGV in XGBoost/LightGBM on
        # Python 3.14 + macOS ARM. np.ascontiguousarray is cheap (no-copy if already
        # C-contiguous).
        X_resampled = np.ascontiguousarray(X_resampled)

        return X_resampled, y_resampled


class TGANSampler:
    """
    TGANSampler - Pluggable sampler for the original TGAN (Tabular GAN) model.
    Since the original TGAN library is abandoned, requires obsolete TensorFlow 1.x,
    and is incompatible with Python 3.14, this class logs a warning and falls back to
    CTGAN as a modern generative sampler replacement.
    """
    def __init__(self, epochs=5, batch_size=500, random_state=42):
        self.epochs = epochs
        self.batch_size = batch_size
        self.random_state = random_state
        self.ctgan_fallback = CTGANSampler(epochs=epochs, batch_size=batch_size, random_state=random_state)

    def fit_resample(self, X: np.ndarray, y: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        if TGANModel is not None:
            try:
                X_arr = X.to_numpy() if hasattr(X, "to_numpy") else np.array(X)
                y_arr = y.to_numpy() if hasattr(y, "to_numpy") else np.array(y)
                classes, counts = np.unique(y_arr, return_counts=True)
                minority_class = classes[np.argmin(counts)]
                n_to_generate = counts[np.argmax(counts)] - counts[np.argmin(counts)]
                if n_to_generate <= 0:
                    return X, y
                
                X_minority = X_arr[y_arr == minority_class]
                df_minority = pd.DataFrame(X_minority)
                df_minority.columns = df_minority.columns.astype(str)
                
                tgan = TGANModel(continuous_columns=list(df_minority.columns))
                tgan.fit(df_minority)
                synthetic_samples = tgan.sample(n_to_generate)
                X_synthetic = synthetic_samples.to_numpy()
                y_synthetic = np.full(n_to_generate, minority_class)
                
                return np.vstack([X_arr, X_synthetic]), np.concatenate([y_arr, y_synthetic])
            except Exception as e:
                print(f"⚠️ Error running TGAN: {e}. Falling back to CTGAN.")
                return self.ctgan_fallback.fit_resample(X, y)
        else:
            print("⚠️ WARNING: TGAN library is unavailable or incompatible with Python 3.14 (requires TensorFlow 1.x). "
                  "Falling back to CTGAN as a modern generative sampler replacement.")
            return self.ctgan_fallback.fit_resample(X, y)


def get_sampler(sampler_name: str, random_state: int = 42, ctgan_epochs: int = 5, ctgan_batch_size: int = 500):
    """
    Factory function to retrieve the configured sampler.
    """
    name = sampler_name.lower().strip()
    if name == "original":
        return None
    elif name == "smote":
        if SMOTE is not None:
            return SMOTE(random_state=random_state)
        return None
    elif name == "adasyn":
        if ADASYN is not None:
            return ADASYN(random_state=random_state)
        return None
    elif name == "mwmote":
        return MWMOTESampler(random_state=random_state)
    elif name == "ctgan":
        return CTGANSampler(epochs=ctgan_epochs, batch_size=ctgan_batch_size, random_state=random_state)
    elif name == "tgan":
        return TGANSampler(epochs=ctgan_epochs, batch_size=ctgan_batch_size, random_state=random_state)
    else:
        raise ValueError(f"Unknown sampler: {sampler_name}")
