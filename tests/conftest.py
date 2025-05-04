import os
from dotenv import load_dotenv
# Load .env and .env.test for test keys BEFORE pytest collects any tests
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env'), override=False)
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '../.env.test'), override=True)
if 'PRIVATE_KEY_PEM' not in os.environ:
    raise RuntimeError('PRIVATE_KEY_PEM not found in environment. Ensure .env.test is present and loaded.')
