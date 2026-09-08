from enum import Enum


class SourceType(str, Enum):
    CHRONICLE = "chronicle"
    WIKI = "wiki"
    OFFICIAL_CODEX = "official_codex"
    EPHEMERA = "ephemera"
    UNKNOWN = "unknown"


SOURCE_AUTHORITY = {
    SourceType.OFFICIAL_CODEX: 1.00,
    SourceType.CHRONICLE: 0.85,
    SourceType.WIKI: 0.65,
    SourceType.EPHEMERA: 0.50,
    SourceType.UNKNOWN: 0.40,
}


def get_source_authority(source_type: SourceType | str) -> float:
    """
    Return the configured source authority score.

    Authority is used as a retrieval/ranking preference.
    It must NOT be interpreted as absolute truth.
    """

    if isinstance(source_type, str):
        try:
            source_type = SourceType(source_type)
        except ValueError:
            source_type = SourceType.UNKNOWN

    return SOURCE_AUTHORITY.get(source_type, 0.40)


def infer_source_type(path: str) -> SourceType:
    """
    Infer source category from the corpus directory structure.
    """

    normalized = path.lower().replace("\\", "/")

    if "/chronicles/" in normalized or normalized.startswith("chronicles/"):
        return SourceType.CHRONICLE

    if "/wiki/" in normalized or normalized.startswith("wiki/"):
        return SourceType.WIKI

    if "/codex/" in normalized or normalized.startswith("codex/"):
        return SourceType.OFFICIAL_CODEX

    if "/ephemera/" in normalized or normalized.startswith("ephemera/"):
        return SourceType.EPHEMERA

    return SourceType.UNKNOWN