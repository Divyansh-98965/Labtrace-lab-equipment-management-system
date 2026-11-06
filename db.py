import pymysql
from pymysql.cursors import DictCursor
from config import Config

def get_db_connection(use_database=True):
    """
    Establish a connection to MySQL.
    If use_database is False, connects without selecting a database (useful for schema creation).
    """
    params = {
        "host": Config.MYSQL_HOST,
        "port": Config.MYSQL_PORT,
        "user": Config.MYSQL_USER,
        "password": Config.MYSQL_PASSWORD,
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": True
    }
    if use_database:
        params["database"] = Config.MYSQL_DB
        
    return pymysql.connect(**params)

def execute_sql_file(file_path):
    """
    Executes multiple SQL statements from a file (e.g., schema.sql).
    """
    # Connect without specific DB first to ensure DB exists
    conn = get_db_connection(use_database=False)
    try:
        with conn.cursor() as cursor:
            with open(file_path, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Split statements by semicolon while ignoring comments
            statements = []
            current = []
            for line in sql_content.splitlines():
                stripped = line.strip()
                if not stripped or stripped.startswith("--") or stripped.startswith("/*"):
                    continue
                current.append(line)
                if stripped.endswith(";"):
                    statements.append("\n".join(current))
                    current = []
                    
            for stmt in statements:
                stmt_clean = stmt.strip()
                if stmt_clean:
                    cursor.execute(stmt_clean)
        conn.commit()
    finally:
        conn.close()

