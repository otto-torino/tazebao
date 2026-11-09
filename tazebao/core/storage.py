from django.contrib.staticfiles.storage import ManifestStaticFilesStorage


class StaticStorage(ManifestStaticFilesStorage):
    """Hashed static files, without rewriting "sourceMappingURL" comments.

    Since Django 4 the manifest storage also hashes source map references, and
    fails when a file is missing: several vendor libraries point to source maps
    they do not ship. Only CSS url() and @import are processed.
    """

    patterns = (
        (
            '*.css',
            (
                r"""(?P<matched>url\(['"]{0,1}\s*(?P<url>.*?)["']{0,1}\))""",
                (
                    r"""(?P<matched>@import\s*["']\s*(?P<url>.*?)["'])""",
                    """@import url("%(url)s")""",
                ),
            ),
        ),
    )
