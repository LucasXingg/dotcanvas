from src import service_config


class dot_daemon():

    def __init__(self):
        self.config = service_config.serverc_config()
        self.running = False
        if not self.config.validate():
            print("Config validation failed, exiting.")
            exit(1)