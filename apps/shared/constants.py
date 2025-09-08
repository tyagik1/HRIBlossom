from .models.robot import BlossomRobot
from .models.robot_config import RobotConfig


CONFIG = None  # Will be initialized when needed
BLOSSOM_ROBOT = None  # Will be initialized when needed
SEQUENCE_DIR = "./sequences"

def get_config():
    global CONFIG
    if CONFIG is None:
        CONFIG = RobotConfig().config
    return CONFIG

def get_blossom_robot():
    global BLOSSOM_ROBOT
    if BLOSSOM_ROBOT is None:
        BLOSSOM_ROBOT = BlossomRobot.from_config(get_config())
    return BLOSSOM_ROBOT