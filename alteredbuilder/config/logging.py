from logging import Filter, getLogger, LogRecord

logger = getLogger(__name__)


class Ignore403Filter(Filter):
    def filter(self, record: LogRecord) -> bool | LogRecord:
        try:
            logger.warning(record.exc_info[1])
        except TypeError:
            pass
        return record.getMessage().find("Permission denied") == -1