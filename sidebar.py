import flet as ft
import sqlite3

class ModernNavBar(ft.Container):
    def __init__(self):
        # Track the highest discussion number
        self.highest_discussion_num = 0
        # Connect to the database and get table names
        table_names = self.get_database_tables()
        # Find the highest existing discussion number
        self.update_highest_discussion_num(table_names)
        
        super().__init__(
            alignment=ft.alignment.center,
            padding=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=5,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=20),
                        content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)
                    ),
                    # Add the "Create Discussion" button
                    self.create_discussion_button(),
                    *self.create_table_list_items(table_names),
                ],
            ),
        )

    def update_highest_discussion_num(self, table_names):
        """Find the highest discussion number from existing tables"""
        for table in table_names:
            if table.startswith("discussion_"):
                try:
                    num = int(table.split("_")[1])
                    if num > self.highest_discussion_num:
                        self.highest_discussion_num = num
                except (IndexError, ValueError):
                    continue

    def create_discussion_button(self):
        """Create the 'Create Discussion' button"""
        return ft.Container(
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            content=ft.Row(
                controls=[
                    ft.Icon(name=ft.icons.ADD, size=18),
                    ft.Text("Create a Discussion", size=14),
                ],
                spacing=10
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_300)),
            on_click=self.create_new_discussion
        )

    def get_database_tables(self):
        """Fetch all table names from the SQLite database"""
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            return [table[0] for table in tables]
        except Exception as e:
            print(f"Error accessing database: {e}")
            return ["No tables found"]

    def create_table_list_items(self, table_names):
        """Create list items for each table name"""
        items = []
        for table in table_names:
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=15),
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.icons.TABLE_ROWS, size=18),
                            ft.Text(table, size=14),
                        ],
                        spacing=10
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_300)),
                    on_click=lambda e, table=table: self.on_table_click(e, table)
                )
            )
        return items

    def create_new_discussion(self, e):
        """Create a new discussion table in the database"""
        try:
            # Increment the discussion number
            self.highest_discussion_num += 1
            table_name = f"discussion_{self.highest_discussion_num}"
            
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            
            # Create a new table with some basic structure
            cursor.execute(f"""
                CREATE TABLE {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    message TEXT,
                    sender TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            conn.close()
            
            # Refresh the sidebar to show the new table
            self.refresh_sidebar(e.page, table_name)
            
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Created new discussion: {table_name}"), 
                    open=True
                )
            )
        except Exception as e:
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Error creating discussion: {str(e)}"), 
                    open=True
                )
            )

    def refresh_sidebar(self, page, new_table_name):
        """Refresh the sidebar to include the newly created table"""
        # Get the current table names including the new one
        table_names = self.get_database_tables()
        
        # Rebuild the controls
        self.content.controls = [
            ft.Container(
                padding=ft.padding.only(bottom=20),
                content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)
            ),
            self.create_discussion_button(),
            *self.create_table_list_items(table_names),
        ]
        
        # Update the page
        page.update()

    def on_table_click(self, e, table_name):
        """Handle table click event"""
        print(f"Table clicked: {table_name}")
        # You can add your logic here to show table contents or perform other actions
        e.page.show_snack_bar(ft.SnackBar(ft.Text(f"Selected table: {table_name}"), open=True))

def render_sidebar():
    return ModernNavBar()