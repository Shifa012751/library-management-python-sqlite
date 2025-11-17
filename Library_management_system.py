import sqlite3
from datetime import datetime, timedelta
import os

class LibraryManagementSystem:
    def __init__(self, db_name="library.db"):
        self.db_name = db_name
        self.conn = None
        self.cursor = None
        self.connect_db()
        self.create_tables()
    
    def connect_db(self):
        """Connect to SQLite database"""
        self.conn = sqlite3.connect(self.db_name)
        self.cursor = self.conn.cursor()
        print("Database connected successfully!")
    
    def create_tables(self):
        """Create necessary tables if they don't exist"""
        # Books table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS books (
                book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                isbn TEXT UNIQUE,
                category TEXT,
                quantity INTEGER DEFAULT 1,
                available INTEGER DEFAULT 1,
                added_date TEXT
            )
        ''')
        
        # Members table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS members (
                member_id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE,
                phone TEXT,
                address TEXT,
                join_date TEXT
            )
        ''')
        
        # Transactions table
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS transactions (
                transaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                book_id INTEGER,
                member_id INTEGER,
                issue_date TEXT,
                due_date TEXT,
                return_date TEXT,
                status TEXT,
                FOREIGN KEY (book_id) REFERENCES books(book_id),
                FOREIGN KEY (member_id) REFERENCES members(member_id)
            )
        ''')
        
        self.conn.commit()
        print("Tables created successfully!")
    
    def add_book(self, title, author, isbn, category, quantity=1):
        """Add a new book to the library"""
        try:
            added_date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
                INSERT INTO books (title, author, isbn, category, quantity, available, added_date)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (title, author, isbn, category, quantity, quantity, added_date))
            self.conn.commit()
            print(f"Book '{title}' added successfully!")
            return True
        except sqlite3.IntegrityError:
            print("Error: ISBN already exists!")
            return False
    
    def add_member(self, name, email, phone, address):
        """Add a new member"""
        try:
            join_date = datetime.now().strftime("%Y-%m-%d")
            self.cursor.execute('''
                INSERT INTO members (name, email, phone, address, join_date)
                VALUES (?, ?, ?, ?, ?)
            ''', (name, email, phone, address, join_date))
            self.conn.commit()
            print(f"Member '{name}' added successfully!")
            return True
        except sqlite3.IntegrityError:
            print("Error: Email already exists!")
            return False
    
    def search_books(self, search_term):
        """Search books by title, author, or ISBN"""
        self.cursor.execute('''
            SELECT * FROM books 
            WHERE title LIKE ? OR author LIKE ? OR isbn LIKE ?
        ''', (f'%{search_term}%', f'%{search_term}%', f'%{search_term}%'))
        books = self.cursor.fetchall()
        return books
    
    def display_books(self, books):
        """Display books in formatted way"""
        if not books:
            print("No books found!")
            return
        
        print("\n" + "="*100)
        print(f"{'ID':<5} {'Title':<30} {'Author':<20} {'ISBN':<15} {'Category':<15} {'Available':<10}")
        print("="*100)
        for book in books:
            print(f"{book[0]:<5} {book[1]:<30} {book[2]:<20} {book[3]:<15} {book[4]:<15} {book[6]}/{book[5]}")
        print("="*100)
    
    def issue_book(self, book_id, member_id):
        """Issue a book to a member"""
        # Check if book is available
        self.cursor.execute('SELECT available FROM books WHERE book_id = ?', (book_id,))
        result = self.cursor.fetchone()
        
        if not result or result[0] <= 0:
            print("Book is not available!")
            return False
        
        # Check if member exists
        self.cursor.execute('SELECT member_id FROM members WHERE member_id = ?', (member_id,))
        if not self.cursor.fetchone():
            print("Member not found!")
            return False
        
        # Issue the book
        issue_date = datetime.now().strftime("%Y-%m-%d")
        due_date = (datetime.now() + timedelta(days=14)).strftime("%Y-%m-%d")
        
        self.cursor.execute('''
            INSERT INTO transactions (book_id, member_id, issue_date, due_date, status)
            VALUES (?, ?, ?, ?, 'issued')
        ''', (book_id, member_id, issue_date, due_date))
        
        # Update book availability
        self.cursor.execute('''
            UPDATE books SET available = available - 1 WHERE book_id = ?
        ''', (book_id,))
        
        self.conn.commit()
        print(f"Book issued successfully! Due date: {due_date}")
        return True
    
    def return_book(self, transaction_id):
        """Return a book"""
        # Get transaction details
        self.cursor.execute('''
            SELECT book_id, status FROM transactions WHERE transaction_id = ?
        ''', (transaction_id,))
        result = self.cursor.fetchone()
        
        if not result:
            print("Transaction not found!")
            return False
        
        if result[1] == 'returned':
            print("Book already returned!")
            return False
        
        # Update transaction
        return_date = datetime.now().strftime("%Y-%m-%d")
        self.cursor.execute('''
            UPDATE transactions SET return_date = ?, status = 'returned'
            WHERE transaction_id = ?
        ''', (return_date, transaction_id))
        
        # Update book availability
        self.cursor.execute('''
            UPDATE books SET available = available + 1 WHERE book_id = ?
        ''', (result[0],))
        
        self.conn.commit()
        print("Book returned successfully!")
        return True
    
    def view_all_members(self):
        """View all members"""
        self.cursor.execute('SELECT * FROM members')
        members = self.cursor.fetchall()
        
        if not members:
            print("No members found!")
            return
        
        print("\n" + "="*100)
        print(f"{'ID':<5} {'Name':<25} {'Email':<30} {'Phone':<15} {'Join Date':<12}")
        print("="*100)
        for member in members:
            print(f"{member[0]:<5} {member[1]:<25} {member[2]:<30} {member[3]:<15} {member[5]:<12}")
        print("="*100)
    
    def view_issued_books(self):
        """View all currently issued books"""
        self.cursor.execute('''
            SELECT t.transaction_id, b.title, m.name, t.issue_date, t.due_date
            FROM transactions t
            JOIN books b ON t.book_id = b.book_id
            JOIN members m ON t.member_id = m.member_id
            WHERE t.status = 'issued'
        ''')
        transactions = self.cursor.fetchall()
        
        if not transactions:
            print("No books currently issued!")
            return
        
        print("\n" + "="*100)
        print(f"{'Trans ID':<10} {'Book Title':<35} {'Member':<25} {'Issue Date':<12} {'Due Date':<12}")
        print("="*100)
        for trans in transactions:
            print(f"{trans[0]:<10} {trans[1]:<35} {trans[2]:<25} {trans[3]:<12} {trans[4]:<12}")
        print("="*100)
    
    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()
            print("Database connection closed!")


def main():
    lms = LibraryManagementSystem()
    
    while True:
        print("\n" + "="*50)
        print("    LIBRARY MANAGEMENT SYSTEM")
        print("="*50)
        print("1. Add Book")
        print("2. Add Member")
        print("3. Search Books")
        print("4. Issue Book")
        print("5. Return Book")
        print("6. View All Members")
        print("7. View Issued Books")
        print("8. Exit")
        print("="*50)
        
        choice = input("Enter your choice (1-8): ")
        
        if choice == '1':
            title = input("Enter book title: ")
            author = input("Enter author name: ")
            isbn = input("Enter ISBN: ")
            category = input("Enter category: ")
            quantity = int(input("Enter quantity: "))
            lms.add_book(title, author, isbn, category, quantity)
        
        elif choice == '2':
            name = input("Enter member name: ")
            email = input("Enter email: ")
            phone = input("Enter phone: ")
            address = input("Enter address: ")
            lms.add_member(name, email, phone, address)
        
        elif choice == '3':
            search_term = input("Enter search term (title/author/ISBN): ")
            books = lms.search_books(search_term)
            lms.display_books(books)
        
        elif choice == '4':
            book_id = int(input("Enter book ID: "))
            member_id = int(input("Enter member ID: "))
            lms.issue_book(book_id, member_id)
        
        elif choice == '5':
            transaction_id = int(input("Enter transaction ID: "))
            lms.return_book(transaction_id)
        
        elif choice == '6':
            lms.view_all_members()
        
        elif choice == '7':
            lms.view_issued_books()
        
        elif choice == '8':
            lms.close()
            print("Thank you for using Library Management System!")
            break
        
        else:
            print("Invalid choice! Please try again.")


if __name__ == "__main__":
    main()