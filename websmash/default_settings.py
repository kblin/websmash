from os import path

# Configuration
DEBUG = True
SECRET_KEY = "development_key"
RESULTS_PATH = path.join(path.dirname(path.dirname(__file__)), 'results')
RESULTS_URL = '/upload'

TAXON = "bacteria"

# Flask-Mail settings
MAIL_SERVER = "mail.example.com"
DEFAULT_MAIL_SENDER = "antismash@example.com"
DEFAULT_RECIPIENTS = ["antismash@example.com"]

# Flask-Redis settings
REDIS_URL = "redis://localhost:6379/0"

OLD_JOB_COUNT = 0

# Job filter settings
MAX_JOBS_PER_USER = 5

# Queue configuration
DEFAULT_QUEUE = "jobs:experimental"
DEVELOPMENT_QUEUE = 'jobs:development'
LEGACY_QUEUE = 'jobs:legacy'
WAITLIST_PREFIX = 'jobs:waiting'
DOWNLOAD_QUEUE = 'jobs:downloads'

# End configuration
