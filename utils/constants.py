import os
from dotenv import load_dotenv

load_dotenv()

UPLOAD_DIR_PATH = os.environ.get('UPLOAD_DIR_PATH')
PORT = os.environ.get('PORT')