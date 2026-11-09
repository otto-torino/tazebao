"""Signatures of the tracking pixel and tracked links embedded in e-mails.

Django 3.1 switched Signer from sha1 to sha256. Newsletters sent before the
upgrade contain sha1 signatures, which must keep working: new links are
signed with the current algorithm, both are accepted when verifying.
"""
from django.core.signing import Signer
from django.utils.crypto import constant_time_compare

LEGACY_ALGORITHM = 'sha1'


def _signature(value, algorithm=None):
    return Signer(algorithm=algorithm).sign(value).rsplit(':', 1)[1]


def sign(value):
    return _signature(value)


def is_valid(value, signature):
    if not signature:
        return False
    return any(
        constant_time_compare(_signature(value, algorithm), signature)
        for algorithm in (None, LEGACY_ALGORITHM)
    )


def open_tracking_value(dispatch_id, subscriber_id):
    return '%s-%s' % (dispatch_id, subscriber_id)


def click_tracking_value(dispatch_id, subscriber_id, url):
    return '%s-%s-%s' % (dispatch_id, subscriber_id, url)
