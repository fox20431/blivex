import configparser

config = configparser.ConfigParser()
config.read('config')
room_id = int(config['DEFAULT']['room_id'])
