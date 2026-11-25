"""
Umbrella's bundled custom-SaaS test environment.

``app.py`` is a third-party SaaS OAuth 2.0 authorization server ("Acme SaaS")
shaped to be driven through the exact same Red/Blue/Dual-Gate flow as the
bundled testbed. It ships in its vulnerable baseline state and is always
executed through an isolated sandbox copy (see aegis.custom_saas.runner),
never patched in place.
"""

CUSTOM_SAAS_TARGET = "aegis/custom_saas/app.py"
CUSTOM_SAAS_LABEL = "Custom SaaS — Acme Workspace"
CUSTOM_SAAS_CLIENT_ID = "acme-saas-7f3a"
CUSTOM_SAAS_REDIRECT_URI = "https://acme-saas.example.com/oauth/redirect"
CUSTOM_SAAS_SCOPE = "read:workspace"

__all__ = [
    "CUSTOM_SAAS_TARGET",
    "CUSTOM_SAAS_LABEL",
    "CUSTOM_SAAS_CLIENT_ID",
    "CUSTOM_SAAS_REDIRECT_URI",
    "CUSTOM_SAAS_SCOPE",
]
