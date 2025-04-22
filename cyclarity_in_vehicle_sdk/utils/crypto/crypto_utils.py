from typing import Optional
from cryptography.hazmat.primitives.serialization import load_der_private_key
from cryptography.hazmat.primitives.asymmetric.padding import PKCS1v15
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.dsa import DSAPrivateKey
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from cryptography.hazmat.primitives.asymmetric.ed448 import Ed448PrivateKey
from cyclarity_in_vehicle_sdk.utils.crypto.models import AsymmetricPaddingType, HashingAlgorithm
from cyclarity_sdk.expert_builder.runnable.runnable import ParsableModel

class CryptoUtils(ParsableModel):
    """Utility class for performing cryptographic operations
    """
    def sign_data(self,
            private_key_der: bytes,
            data: bytes,
            hash_alg: Optional[HashingAlgorithm],
            padding: Optional[AsymmetricPaddingType],
            ) -> bytes:
        """Create digital signature

        Args:
            private_key_der (bytes): the private key in DER format
            data (bytes): the data to sign
            hash_alg (Optional[HashingAlgorithm]): the hashing algorithm
            padding (Optional[AsymmetricPaddingType]): the padding type, relevant for RSA type of key

        Raises:
            NotImplementedError: for key types that are yet to be supported

        Returns:
            bytes: the digital signature
        """
        priv_key = load_der_private_key(private_key_der, None)
        if isinstance(priv_key, RSAPrivateKey):
            return self._sign_rsa(priv_key, data, hash_alg, padding)
        elif isinstance(priv_key, DSAPrivateKey):
            return self._sign_dsa(priv_key, data, hash_alg)
        elif isinstance(priv_key, Ed25519PrivateKey):
            return self._sign_ed25519(priv_key, data, hash_alg)
        elif isinstance(priv_key, Ed448PrivateKey):
            return self._sign_ed448(priv_key, data, hash_alg)
        else:
            raise NotImplementedError(f"Key type {type(priv_key)} is not supported ATM")
            
            
    def _sign_rsa(self,
                  priv_key: RSAPrivateKey, 
                  data: bytes,
                  hash_alg: HashingAlgorithm,
                  padding: AsymmetricPaddingType = AsymmetricPaddingType.PKCS1v15,
                  ) -> bytes:
        if padding != AsymmetricPaddingType.PKCS1v15:
            raise NotImplementedError("Currently only PKCS1v15 padding is supported")
        
        return priv_key.sign(data,
                             PKCS1v15(),
                             HashingAlgorithm.enum_to_method(hash_alg))
    
    def _sign_dsa(self,
                  priv_key: DSAPrivateKey, 
                  data: bytes,
                  hash_alg: HashingAlgorithm,
                  ) -> bytes:
        return priv_key.sign(data,
                             HashingAlgorithm.enum_to_method(hash_alg))
    
    def _sign_ed448(self,
                  priv_key: Ed448PrivateKey, 
                  data: bytes,
                  ) -> bytes:
        return priv_key.sign(data)
    
    def _sign_ed25519(self,
                  priv_key: Ed25519PrivateKey, 
                  data: bytes,
                  ) -> bytes:
        return priv_key.sign(data)