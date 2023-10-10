from os import getenv

from dotenv import load_dotenv

load_dotenv()

LAMBDA_URL = getenv("LAMBDA_URL")
