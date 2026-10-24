"""Validate issuer signatures and bind the signed certificate to its declared holder."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import UTC, datetime

from cryptography import x509
from lxml import etree
from signxml import SignatureConfiguration, XMLVerifier


class CertificateCheckError(ValueError):
    """A document cannot be given a verified badge."""


def normalized_name(value: object) -> str:
    if not isinstance(value, str):
        return ""
    return "".join(c for c in unicodedata.normalize("NFKC", value).casefold() if c.isalnum())


@dataclass(frozen=True)
class IssuedCertificate:
    issuer: str
    sha256: str
    valid_until: datetime | None


def _child(element, name: str):
    return next(
        (
            child
            for child in element
            if isinstance(child.tag, str) and etree.QName(child).localname == name
        ),
        None,
    )


def verify_issued_certificate(
    content: bytes,
    trusted_certificate: bytes,
    kind: str,
    subject_name: str,
    document_number: str,
    now: datetime,
) -> IssuedCertificate:
    if len(content) > 2 * 1024 * 1024 or not content or b"\x00" in content:
        raise CertificateCheckError("The issuer document has an unsupported size or encoding.")
    if re.search(rb"<!\s*(DOCTYPE|ENTITY)\b", content, re.IGNORECASE):
        raise CertificateCheckError("The issuer document contains an unsupported XML declaration.")
    try:
        signer = x509.load_pem_x509_certificate(trusted_certificate)
        if not signer.not_valid_before_utc <= now <= signer.not_valid_after_utc:
            raise CertificateCheckError("The configured issuer signing certificate needs renewal.")
        parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
        result = XMLVerifier().verify(
            content,
            x509_cert=trusted_certificate,
            parser=parser,
            expect_config=SignatureConfiguration(
                require_x509=True, location="./", expect_references=1
            ),
        )
        root = result.signed_xml
        # Read only the verified payload, never unsigned siblings or wrapper data.
        if etree.QName(root).localname != "Certificate":
            raise CertificateCheckError("The signed payload is not an issuer certificate.")
        expected_type = "GSTND" if kind == "gst" else "PANCR"
        if root.get("type") != expected_type:
            raise CertificateCheckError("The issuer document is a different certificate type.")
        if root.get("number", "").strip().upper() != document_number:
            raise CertificateCheckError(
                "The issuer document number does not match your declaration."
            )
        issued_to = _child(root, "IssuedTo")
        holder = (
            _child(issued_to, "Organization" if kind == "gst" else "Person")
            if issued_to is not None
            else None
        )
        if holder is None or normalized_name(holder.get("name", "")) != normalized_name(
            subject_name
        ):
            raise CertificateCheckError(
                "The certificate holder does not match the saved profile name."
            )
        issued_by = _child(root, "IssuedBy")
        organization = _child(issued_by, "Organization") if issued_by is not None else None
        issuer = organization.get("name", "") if organization is not None else ""
        allowed_issuer = "goodsandservicestaxnetwork" if kind == "gst" else "incometaxdepartment"
        if normalized_name(issuer) != allowed_issuer:
            raise CertificateCheckError(
                "The document issuer does not match the expected authority."
            )
        if kind == "pan" and root.get("status") not in {"A", "Active"}:
            raise CertificateCheckError(
                "The issuer PAN document does not confirm an active record."
            )
        if root.get("status", "").strip().casefold() in {
            "cancelled",
            "revoked",
            "expired",
            "inactive",
            "i",
            "c",
        }:
            raise CertificateCheckError("The issuer document is no longer valid.")
        expiry = root.get("validToDate") or root.get("expiryDate")
        valid_until = None
        if expiry:
            for pattern in ("%d-%m-%Y", "%d/%m/%Y", "%Y-%m-%d"):
                try:
                    valid_until = datetime.strptime(expiry, pattern).replace(
                        tzinfo=UTC, hour=23, minute=59, second=59
                    )
                    break
                except ValueError:
                    continue
            if valid_until is None or valid_until <= now:
                raise CertificateCheckError("The document expiry is unresolved or has passed.")
        return IssuedCertificate(
            issuer=issuer, sha256=hashlib.sha256(content).hexdigest(), valid_until=valid_until
        )
    except CertificateCheckError:
        raise
    except Exception:
        # Never disclose XML, private identifiers, or signer material in public errors.
        raise CertificateCheckError(
            "The issuer document signature could not be verified."
        ) from None


def verify_gst_registration(data: dict, subject_name: str, gstin: str) -> None:
    record = data.get("data")
    if data.get("status_cd") != "1" or not isinstance(record, dict):
        raise CertificateCheckError("The GST registry could not confirm this registration.")
    if record.get("gstin") != gstin or normalized_name(record.get("lgnm", "")) != normalized_name(
        subject_name
    ):
        raise CertificateCheckError("The GST registry holder does not match this profile.")
    if record.get("sts") != "Active":
        raise CertificateCheckError("The GST registration is not active in the issuer registry.")
