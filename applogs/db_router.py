# coding=utf-8;


class LogsDBRouter():

    LOG_APP_NAME = 'applogs'
    LOG_APP_DB_ALIAS = 'applogs'

    def is_log_app(self, obj):
        return obj._meta.app_label == self.LOG_APP_NAME

    def db_for_read(self, model, **hints):
        if self.is_log_app(model):
            return self.LOG_APP_DB_ALIAS
        return None

    def db_for_write(self, model, **hints):
        if self.is_log_app(model):
            return self.LOG_APP_DB_ALIAS
        return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        if app_label == self.LOG_APP_NAME:
            return db == self.LOG_APP_DB_ALIAS
        return None
