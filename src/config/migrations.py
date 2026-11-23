CURRENT_SCHEMA_VERSION = 3


def _migrate_1_to_2(raw):
    raw.pop("poppler_path", None)
    raw.setdefault("check_updates", True)
    return raw


def _migrate_2_to_3(raw):
    raw.setdefault("ui_scale", 1.0)
    return raw


MIGRATIONS = {
    1: _migrate_1_to_2,
    2: _migrate_2_to_3,
}


def migrate(raw):
    raw = dict(raw)
    version = raw.get("schema_version", 1)
    if version > CURRENT_SCHEMA_VERSION:
        raise ValueError(
            "Конфиг создан более новой версией приложения (schema_version {} > {})".format(
                version, CURRENT_SCHEMA_VERSION
            )
        )
    while version < CURRENT_SCHEMA_VERSION:
        raw = MIGRATIONS[version](raw)
        version += 1
    raw["schema_version"] = version
    return raw
