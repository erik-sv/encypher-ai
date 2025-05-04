from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

priv = ed25519.Ed25519PrivateKey.generate()
pub = priv.public_key()

priv_pem = priv.private_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PrivateFormat.PKCS8,
    encryption_algorithm=serialization.NoEncryption()
).decode()

pub_pem = pub.public_bytes(
    encoding=serialization.Encoding.PEM,
    format=serialization.PublicFormat.SubjectPublicKeyInfo
).decode()

with open('.env.test', 'w') as f:
    f.write(f'PRIVATE_KEY_PEM="""{priv_pem}"""\n')
    f.write(f'PUBLIC_KEY_PEM="""{pub_pem}"""\n')

print('Test keys written to .env.test')
