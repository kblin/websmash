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

# Users with access to the priority queue
VIP_USERS = set()

# Queue configuration
DEFAULT_QUEUE = "jobs:queued"
FAST_QUEUE = 'jobs:minimal'
PRIORITY_QUEUE = 'jobs:priority'
DEVELOPMENT_QUEUE = 'jobs:development'
WAITLIST_PREFIX = 'jobs:waiting'
DOWNLOAD_QUEUE = 'jobs:downloads'

DEFAULT_JOBTYPE = 'epssmash'
DARK_LAUNCH_JOBTYPE = 'epssmash'
LEGACY_JOBTYPE = 'epssmash'


# Percentage of jobs where we activate features we only want to run occasionally
# during dark launches
RARE_TEST_PERCENTAGE = 10

# Percentage of jobs also sent into the development version queue
DARK_LAUNCH_PERCENTAGE = 10
# Jobs transferred to the development version queue get hardcoded to use this
# email address so we can (a) track them (b) they don't confuse the submitter
DARK_LAUNCH_EMAIL = "antismash@example.com"

# End configuration
