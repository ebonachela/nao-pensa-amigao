import json
from os.path import exists

class BotConfig:
    def __init__(self, config_file):
        if not exists(config_file):
            with open(config_file, "w") as f:
                f.write('{}')

        self.m_config_file = config_file
        self.m_config = {}

        with open(self.m_config_file, "r") as jsonfile:
            self.m_config = json.load(jsonfile)

    def getConfig(self, configName):
        return self.m_config[configName]
    
    def addCommand(self, serverID, command, url):
        if serverID in self.m_config:
            self.m_config[serverID][command] = url
        else:
            self.m_config[serverID] = {}
            self.m_config[serverID][command] = url
        
        with open(self.m_config_file, "w") as f:
            json_string = json.dumps(self.m_config)
            f.write(json_string)


        