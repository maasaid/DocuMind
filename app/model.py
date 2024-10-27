from .db import create_connection
from mysql.connector import Error
connection = create_connection()

class User:
    def __init__(self, user_name, email, password):
        self.user_name = user_name
        self.email = email
        self.password = password

        def save_to_db(self):
            
            if connection:
                try:
                    cursor = connection.cursor()
                    query = "INSERT INTO users (user_name, email, password) VALUES (%s, %s, %s)"
                    values = (self.user_name, self.email, self.password)
                    cursor.execute(query, values)
                    connection.commit()
                    print("User saved to database.")
                except Error as e:
                    print(f"The error '{e}' occurred")
                finally:
                    cursor.close()
                    connection.close()