from db.config import get_db_connection


def get_onboarding_list():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM onboarding")  # Assume onboarding table exists
    results = cursor.fetchall()

    cursor.close()
    conn.close()
    return results

def create_onboarding_entry(data):
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO onboarding (employee_name, start_date, department)
            VALUES (%s, %s, %s)
        """, (data['employee_name'], data['start_date'], data['department']))
        
        conn.commit()
        return True
    except Exception as e:
        print("DB Error:", e)
        conn.rollback()
        return False
    finally:
        cursor.close()
        conn.close()
