import psycopg2
import sqlalchemy
import google.auth
import google.auth.transport.requests
from sqlalchemy import URL

from common.Logger import Logger


class GetConnection:
    def __init__(self, config):
        self.iam_token = None
        self.postgres_connection_string = None
        self.credentials = None
        self.engine = None
        self.connection = None
        self.db_password = None
        self.db_user = None
        self.db_name = None
        self.db_instance = None
        self.enable_iam_auth = True
        self.config = config
        self.logger = Logger().get_logger()
        self.host = None

    def _get_iam_token(self):
        # Get the default application credentials
        self.credentials, project = google.auth.default()
        # Generate an OAuth 2.0 token for the IAM-based authentication
        self.credentials.refresh(google.auth.transport.requests.Request())
        self.iam_token = self.credentials.token

    def _get_connection(self):
        config = self.config
        self.db_instance = config.get_config("cloudsql", "instance")
        self.db_name = config.get_config("cloudsql", "database")
        self.db_user = config.get_config("cloudsql", "user")
        self.host = config.get_config("cloudsql", "host_ip")
        self.logger.info(f"Connecting to database instance - {self.db_instance}")

        self._get_iam_token()
        self.connection = URL.create(
            drivername="postgresql+psycopg2",
            username=self.db_user,
            host=self.host,
            port="5432",
            database=self.db_name,
            password=self.iam_token,
            query={"sslmode": "prefer"}
        )
        return self.connection

    def get_engine(self):
        self.logger.info("Creating SQLAlchemy Engine")
        self.engine = sqlalchemy.create_engine(
                url=self._get_connection(),
                echo=True,
                pool_size=100,  # Number of connections to maintain in the pool
                max_overflow=5,  # Number of connections to create beyond pool_size
                pool_timeout=30,  # Timeout for waiting to acquire a connection
                pool_recycle=1800,  # Recycle connections after a certain number of seconds
            )
        return self.engine

    def _get_connection_string(self):
        self.postgres_connection_string = f"postgresql+psycopg2://{self.db_user}:{self.iam_token}@{self.host}/{self.db_name}?sslmode=prefer"
        return self.postgres_connection_string
