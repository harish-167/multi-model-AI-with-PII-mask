To use this docker-compose.yml file, you would need to:
Install psycopg2-binary (pip install psycopg2-binary and add it to requirements.txt).
Change the SQLALCHEMY_DATABASE_URI line in app.py to:
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')

Containerized (with PostgreSQL):
Make sure Docker and Docker Compose are installed.
Make the changes mentioned above to use PostgreSQL (psycopg2-binary, update app.py).
From your project root, run: docker-compose up --build
The first time, this will build the Flask image and pull the Postgres image.
Go to http://localhost:5000. Your app will be running inside a container and