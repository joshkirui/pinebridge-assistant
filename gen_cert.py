import os
import subprocess
import sys

cert_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "certs")
os.makedirs(cert_dir, exist_ok=True)
key_path = os.path.join(cert_dir, "key.pem")
cert_path = os.path.join(cert_dir, "cert.pem")

if os.path.exists(key_path) and os.path.exists(cert_path):
    print("Certificates already exist")
    sys.exit(0)

# Try openssl first
try:
    subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", key_path, "-out", cert_path,
        "-days", "365", "-nodes", "-subj", "/CN=localhost"
    ], check=True, capture_output=True)
    print("Generated with openssl")
    sys.exit(0)
except Exception:
    pass

# Fallback: use Python cryptography library
try:
    from cryptography import x509
    from cryptography.x509.oid import NameOID
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import rsa
    import datetime

    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
    cert = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(issuer)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(datetime.datetime.utcnow())
        .not_valid_after(datetime.datetime.utcnow() + datetime.timedelta(days=365))
        .add_extension(x509.SubjectAlternativeName([x509.DNSName("localhost")]), critical=False)
        .sign(key, hashes.SHA256())
    )
    with open(key_path, "wb") as f:
        f.write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.TraditionalOpenSSL, serialization.NoEncryption()))
    with open(cert_path, "wb") as f:
        f.write(cert.public_bytes(serialization.Encoding.PEM))
    print("Generated with cryptography library")
except ImportError:
    print("ERROR: Need either openssl or 'pip install cryptography'")
