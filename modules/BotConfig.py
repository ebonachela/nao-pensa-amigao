import json

class BotConfig:
    def __init__(self, config_file):
        self.m_config_file = config_file
        self.m_config = []

        with open(self.m_config_file, "r") as jsonfile:
            self.m_config = json.load(jsonfile)

    def getConfig(self, configName):
        return self.m_config[configName]