class UpdaterError(Exception):
    pass


from updater.installer import rollback as rollback, update as update  # noqa: E402
from updater.release import compare_versions as compare_versions, parse_version as parse_version  # noqa: E402
