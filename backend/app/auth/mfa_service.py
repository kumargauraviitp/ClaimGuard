import pyotp
import qrcode
import io
import base64
from typing import Tuple

class MFAService:
    @staticmethod
    def generate_secret() -> str:
        return pyotp.random_base32()
        
    @staticmethod
    def get_provisioning_uri(secret: str, email: str, issuer_name: str = "InsuranceFraudPlatform") -> str:
        return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=issuer_name)
        
    @staticmethod
    def verify_totp(secret: str, code: str) -> bool:
        totp = pyotp.TOTP(secret)
        return totp.verify(code)

    @staticmethod
    def generate_qr_code_base64(provisioning_uri: str) -> str:
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(provisioning_uri)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        buffered = io.BytesIO()
        img.save(buffered, format="PNG")
        img_str = base64.b64encode(buffered.getvalue()).decode()
        return img_str
