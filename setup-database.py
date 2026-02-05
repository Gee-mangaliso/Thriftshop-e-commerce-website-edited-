import mysql.connector
import os
import re
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def parse_sql_statements(sql_script):
    """
    Parses an SQL script, correctly isolating DELIMITER blocks.
    It returns a list of executable statements.
    """
    # Pattern to capture everything between DELIMITER statements, including the delimiter command itself,
    # or to capture standard SQL statements (ending with ';').
    # This is simplified because the DDL file does not have DELIMITER commands.

    # 1. Split into blocks based on 'DELIMITER' commands
    # This captures the DELIMITER command itself and the content following it.
    blocks = re.split(r'(DELIMITER\s+[^;]+)', sql_script, flags=re.IGNORECASE)

    current_delimiter = ';'
    statements = []

    for block in blocks:
        if not block.strip():
            continue

        # Check if the block is a DELIMITER command
        delim_match = re.match(r'DELIMITER\s+([^;]+)', block.strip(), re.IGNORECASE)
        if delim_match:
            current_delimiter = delim_match.group(1).strip()
            continue

        # Process the SQL content within the current delimiter context
        # Split the block content by the current delimiter
        sql_parts = block.split(current_delimiter)

        for part in sql_parts:
            statement = part.strip()
            if statement:
                # Append the delimiter to the statement if it's the custom delimiter
                # This ensures the entire Procedure/Trigger block is executed as one unit,
                # as required by the MySQL connector when not using multi=True.
                if current_delimiter != ';':
                    statements.append(statement + current_delimiter)
                else:
                    statements.append(statement + current_delimiter) # Add back ';' for standard statements

        # Reset the delimiter back to ';' if the last block was executed with a custom delimiter
        if current_delimiter != ';':
            current_delimiter = ';'

    # Final cleanup to ensure only statements are returned (remove trailing delimiters in procedures/triggers)
    final_statements = []
    for stmt in statements:
        stmt = stmt.strip()
        # Remove comments
        stmt = re.sub(r'--.*?\n', '', stmt, flags=re.DOTALL)
        stmt = re.sub(r'/\*.*?\*/', '', stmt, flags=re.DOTALL)

        # Simple cleanup: ensure the procedure/trigger block doesn't end with a delimiter twice
        if stmt.endswith('//;'):
            stmt = stmt[:-1]

        # Strip trailing ';' for standard statements, but keep the procedure block intact
        if stmt.endswith(';'):
            final_statements.append(stmt.strip(';'))
        elif stmt.endswith('//'):
            final_statements.append(stmt) # Keep the '//' to mark the end of the procedure block

    return [s for s in final_statements if s] # Filter out empty strings


def execute_sql_file(cursor, filename):
    """Reads an SQL file, parses statements, and executes them one by one."""
    print(f"\n--- Executing {filename} ---")

    with open(filename, 'r') as file:
        sql_script = file.read()

    # The DDL file is simple, so we can split it easily.
    # Procedures/Triggers require special parsing to handle DELIMITER commands.
    if 'ddl' in filename:
        statements = [s.strip() for s in sql_script.split(';') if s.strip()]
    else:
        # Use the dedicated parser for Procs/Triggers
        statements = parse_sql_statements(sql_script)


    for statement in statements:
        if not statement.strip():
            continue

        try:
            # Execute the statement
            cursor.execute(statement)

            # Consume all results to fix "Commands out of sync" (Error 2014)
            while cursor.nextset():
                pass # Keep iterating through result sets

        except mysql.connector.Error as err:
            # Check for known, non-critical errors (e.g., trying to DROP a non-existent object)
            if err.errno in (1050, 1061, 1062, 1091, 1305):
                print(f"Skipping known error ({err.errno}): {err.msg.split(': ')[-1]}")
            else:
                print(f"CRITICAL Error executing statement ({err.errno}): {err}")
                print(f"Statement: {statement.strip()[:100]}...")
                # We will stop here to prevent cascading errors if DDL fails
                if 'ddl' in filename:
                    raise # Re-raise error for critical file (DDL)

def setup_database():
    # Database configuration
    config = {
        'host': os.getenv('DB_HOST', 'localhost'),
        'user': os.getenv('DB_USER', 'root'),
        'password': os.getenv('DB_PASSWORD', '@Khizo14251'),
        'database': os.getenv("DB_NAME",'thriftshop_sa')
       # 'auth_plugin': 'mysql_native_password'
    }

    conn = None
    cursor = None
    try:
        # 1. Connect to MySQL server
        conn = mysql.connector.connect(**config)
        cursor = conn.cursor()

        # 2. Create and use database
        cursor.execute("CREATE DATABASE IF NOT EXISTS thriftshop_sa")
        cursor.execute("USE thriftshop_sa")
        print("Database created and selected successfully!")

        # 3. Execute DDL/DML (Tables, Views, Sample Data, Indexes)
        execute_sql_file(cursor, 'thriftshop_sa_ddl.sql')

        # 4. Execute Stored Procedures
        execute_sql_file(cursor, 'thriftshop_sa_procs.sql')

        # 5. Execute Triggers
        execute_sql_file(cursor, 'thriftshop_sa_triggers.sql')

        # The final commit is crucial after executing all SQL
        conn.commit()
        print("\nSchema, data, procedures, and triggers created successfully!")

    except mysql.connector.Error as err:
        print(f"\nCRITICAL Database connection/setup error: {err}")
    finally:
        if cursor:
            cursor.close()
        if conn:
            conn.close()

def create_upload_directories():
    """Create necessary upload directories"""
    directories = [
        'static/uploads/images',
        'static/uploads/videos',
        'static/uploads/profiles',
        'static/uploads/documents',
        'static/categories'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

if __name__ == "__main__":
    print("Setting up Mzansi Thrift Store database...")
    create_upload_directories()
    setup_database()
    print("Database setup completed!")