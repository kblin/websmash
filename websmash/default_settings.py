from os import path
############# Configuration #############
DEBUG = True
SECRET_KEY = "development_key"
RESULTS_PATH = path.join(path.dirname(path.dirname(__file__)), 'results')
RESULTS_URL = '/upload'
NCBI_URL = 'http://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi'
NCBI_URL += '?db=protein&email="%s"&tool="antiSMASH"&val="%s"&dopt=gbwithparts'

# Flask-Mail settings
MAIL_SERVER = "smtpserv.uni-tuebingen.de"
DEFAULT_MAIL_SENDER = "kai.blin@biotech.uni-tuebingen.de"
DEFAULT_RECIPIENTS = ["kai.blin@biotech.uni-tuebingen.de"]

# Flask-SQLAlchemy settings
SQLALCHEMY_DATABASE_URI = 'sqlite:///../jobs.db'

# Flask-Downloader settings
DEFAULT_DOWNLOAD_DIR = RESULTS_PATH
#########################################
