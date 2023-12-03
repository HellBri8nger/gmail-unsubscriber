from datetime import datetime


class Logger:
    logger_status = False
    log = None

    @staticmethod
    def create_log():
        Logger.log = open(f'{datetime.now().strftime("%Y%m%d_%H%M%S")}.log', 'w', encoding='utf-8')
        Logger.logger_status = True

    @staticmethod
    def close_log():
        if Logger.log:
            Logger.log.close()

    @staticmethod
    def log_writer(value):
        if Logger.logger_status:
            Logger.log.write(value)
            Logger.log.flush()
