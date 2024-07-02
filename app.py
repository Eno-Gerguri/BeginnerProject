import os
from flask import Flask, request, jsonify
import psycopg2
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To, Content


def load_env_vars(env_file):
    with open(env_file, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#'):
                key, value = line.strip().split('=', 1)
                os.environ[key] = value


load_env_vars("secrets.env")
DATABASE = {
    "host": os.getenv("DB_HOST"),
    "database": os.getenv("DB_NAME"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD")
}

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
FROM_EMAIL = os.getenv("FROM_EMAIL")
TO_EMAIL = os.getenv("TO_EMAIL")

app = Flask(__name__)


def send_email(email_content):
    message = Mail(
        Email(FROM_EMAIL),
        To(TO_EMAIL),
        "Database Updated",
        Content("text/plain", email_content)
    )
    message_json = message.get()
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.client.mail.send.post(request_body=message_json)
        print(response.status_code)
        print(response.body)
        print(response.headers)
    except Exception as e:
        print(e)


def get_db_connection():
    conn = psycopg2.connect(
        host=DATABASE["host"],
        database=DATABASE["database"],
        user=DATABASE["user"],
        password=DATABASE["password"]
    )
    return conn


def init_db():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "CREATE TABLE IF NOT EXISTS records (id SERIAL PRIMARY KEY, name TEXT NOT NULL, value TEXT NOT NULL)"
    )
    conn.commit()
    cur.close()
    conn.close()


@app.route("/add", methods=["POST"])
def add_record():
    data = request.get_json()
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO records (name, value) VALUES (%s, %s)", (data["name"], data["value"])
    )
    conn.commit()
    cur.close()
    conn.close()
    send_email(f"Record added: {data}")
    return "Record added", 201


@app.route("/records", methods=["GET"])
def get_records():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM records")
    records = cur.fetchall()
    cur.close()
    conn.close()
    return jsonify(records)


@app.route("/thisshouldreturnhello")
def hello():
    return "Hello, World!"


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=80)

