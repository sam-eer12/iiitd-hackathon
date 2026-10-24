"""Ephemeral signing material for tests only. Never used by the application."""

from datetime import UTC, datetime, timedelta

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID
from lxml import etree
from signxml import XMLSigner

COMPANY = "Example Supplies Private Limited"
GSTIN = "27ABCDE1234F1Z5"


def signing_material():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = x509.Name(
        [
            x509.NameAttribute(
                NameOID.COMMON_NAME, "Test issuer - not a trusted production authority"
            )
        ]
    )
    now = datetime.now(UTC)
    certificate = (
        x509.CertificateBuilder()
        .subject_name(subject)
        .issuer_name(subject)
        .public_key(key.public_key())
        .serial_number(x509.random_serial_number())
        .not_valid_before(now - timedelta(days=1))
        .not_valid_after(now + timedelta(days=365))
        .add_extension(x509.BasicConstraints(ca=True, path_length=None), critical=True)
        .sign(key, hashes.SHA256())
    )
    return key, certificate.public_bytes(serialization.Encoding.PEM)


def signed_gst(
    key,
    certificate: bytes,
    *,
    company=COMPANY,
    gstin=GSTIN,
    issuer="Goods and Services Tax Network",
):
    root = etree.Element("Certificate", type="GSTND", number=gstin)
    issued_by = etree.SubElement(root, "IssuedBy")
    etree.SubElement(issued_by, "Organization", name=issuer)
    issued_to = etree.SubElement(root, "IssuedTo")
    etree.SubElement(issued_to, "Organization", name=company)
    return etree.tostring(XMLSigner().sign(root, key=key, cert=certificate))


def signed_pan(key, certificate: bytes, *, name="Example Person", number="ABCDE1234F", status="A"):
    root = etree.Element("Certificate", type="PANCR", number=number, status=status)
    etree.SubElement(
        etree.SubElement(root, "IssuedBy"), "Organization", name="Income Tax Department"
    )
    etree.SubElement(etree.SubElement(root, "IssuedTo"), "Person", name=name)
    return etree.tostring(XMLSigner().sign(root, key=key, cert=certificate))
