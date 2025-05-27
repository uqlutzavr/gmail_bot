import os
import logging
from logging.handlers import RotatingFileHandler
from dotenv import load_dotenv
import datetime
import json

load_dotenv()


def debug_mode_to_bool():
    debug_mode = os.getenv("DEBUG_MODE").capitalize()
    return True if debug_mode == "True" else False


def setup_logging():
    log_directory = "logs"
    if not os.path.exists(log_directory):
        os.makedirs(log_directory)

    time = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file_path = os.path.join(log_directory, f"gmail_bot_{time}.log")

    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
    console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')

    file_handler = RotatingFileHandler(
        log_file_path,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )

    file_handler.setFormatter(file_formatter)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(console_formatter)

    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    debug_mode = debug_mode_to_bool()
    if debug_mode:
        root_logger.setLevel(logging.DEBUG)
        file_handler.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    else:
        root_logger.setLevel(logging.INFO)
        file_handler.setLevel(logging.INFO)
        console_handler.setLevel(logging.INFO)
    return root_logger


logger = setup_logging()


def clean_json_string(value: str):
    return value.strip().strip("'").strip('"')


class GmailBotConfig:
    def __init__(self):
        self.slack_webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        self.debug_mode = debug_mode_to_bool()
        self.scopes = ["https://www.googleapis.com/auth/gmail.readonly"]

        logger.debug(f"SLACK_WEB_HOOK: {'set' if self.slack_webhook_url else 'not set'}")
        if not all([self.slack_webhook_url]):
            logger.error("Missing required environment variables")
            raise ValueError("SLACK_WEBHOOK_URL must be set")
