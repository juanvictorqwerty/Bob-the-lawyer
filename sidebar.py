import flet as ft
import sqlite3

class ModernNavBar(ft.Container):
    def __init__(self):
        # Connect to the database and get table names
        table_names = self.get_database_tables()
        
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
                    *self.create_table_list_items(table_names),
                ],
            ),
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

    def on_table_click(self, e, table_name):
        """Handle table click event"""
        print(f"Table clicked: {table_name}")
        # You can add your logic here to show table contents or perform other actions
        e.page.show_snack_bar(ft.SnackBar(ft.Text(f"Selected table: {table_name}"), open=True))

def render_sidebar():
    return ModernNavBar()