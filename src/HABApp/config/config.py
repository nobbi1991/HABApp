from easyconfig import create_app_config

from HABApp.config.models import ApplicationConfig

HABAPP_CONFIG: ApplicationConfig = create_app_config(ApplicationConfig())
