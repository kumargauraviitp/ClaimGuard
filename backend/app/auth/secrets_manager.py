import os
from dotenv import load_dotenv

load_dotenv(override=False)

class SecretsManager:
    """
    Abstracts secret provisioning. In an enterprise system, this would fetch from
    HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault based on the environment.
    """
    @staticmethod
    def get_secret(key: str, default: str = None) -> str:
        # Here we could check os.environ["VAULT_ADDR"] and use hvac if configured.
        # Fallback to environment variables.
        val = os.getenv(key, default)
        if val is None:
            raise ValueError(f"Secret {key} is required but not configured.")
        return val

# Standard settings used across auth modules
SECRET_KEY = SecretsManager.get_secret("JWT_SECRET_KEY", "change_this_to_a_secure_random_string_in_production")
ALGORITHM = SecretsManager.get_secret("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(SecretsManager.get_secret("ACCESS_TOKEN_EXPIRE_MINUTES", "15"))
REFRESH_TOKEN_EXPIRE_DAYS = int(SecretsManager.get_secret("REFRESH_TOKEN_EXPIRE_DAYS", "7"))
