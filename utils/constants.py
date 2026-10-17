import os
from dotenv import load_dotenv

load_dotenv()

PORT = os.environ.get('PORT')

UPLOAD_DIR_PATH = os.environ.get('UPLOAD_DIR_PATH')
DATA_DIR_PATH = os.environ.get('DATA_DIR_PATH')
SHARED_TEXT_FILENAME = os.environ.get('SHARED_TEXT_FILENAME')
FILES_METADATA_FILENAME = os.environ.get('FILES_METADATA_FILENAME')

DEFAULT_SENDER = "Unknown Device"