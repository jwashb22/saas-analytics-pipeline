from etl import get_db_connection

def main():
    print("Testing database connection...")
    print("-" * 60)

    db = get_db_connection()
    
    if db.test_connection():
        print("\n Database setup successful")
        print("\nChecking existing tables...")

        try:
            count = db.get_table_count('dim_date')
            print(f"  dim_date: {count} rows")
        except Exception as e:
            print(f" Could not query dim_date: {e}")
    else:
        print("\n Database connection failed. Check your .env file.")

    db.close()

if __name__ == "__main__":
    main()