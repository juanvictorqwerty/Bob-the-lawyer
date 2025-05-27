import flet as ft
import sqlite3

class ModernNavBar(ft.Container):
    def __init__(self, main_app):
        self.main_app = main_app  # Reference to the main app
        self.current_selected = "messages"  # Track currently selected discussion
        # Track the highest discussion number
        self.highest_discussion_num = 0
        # Connect to the database and get table names
        table_names = self.get_database_tables()
        # Find the highest existing discussion number
        self.update_highest_discussion_num(table_names)
        
        super().__init__(
            width=250,  # Fixed width of 200px
            padding=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=20),
                        content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)
                    ),
                    self.create_discussion_button(),
                    *self.create_table_list_items(table_names),
                ],
            ),
            border=ft.border.only(right=ft.BorderSide(1, ft.colors.GREY_300)),  # Add right border
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
            # Only show delete button for discussions, not for "messages" table
            show_delete = table.startswith("discussion_") and table != "messages"
            
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=15),
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.icons.TABLE_ROWS, size=18),
                            ft.Text(
                                table, 
                                size=14,
                                color=ft.colors.WHITE if table == self.current_selected else None
                            ),
                            # Delete button (only visible on hover and for discussions)
                            ft.IconButton(
                                icon=ft.icons.DELETE,
                                icon_size=18,
                                icon_color=ft.colors.RED_400,
                                visible=False,  # Hidden by default
                                data=table,  # Store table name in button data
                                on_click=self.delete_discussion,
                            ) if show_delete else ft.Container(width=0)  # Empty container if not deletable
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.colors.GREY_300)),
                    bgcolor=ft.colors.BLUE_800 if table == self.current_selected else None,
                    on_click=lambda e, table=table: self.on_table_click(e, table),
                    on_hover=lambda e, table=table: self.on_discussion_hover(e, table, show_delete),
                )
            )
        return items

    def on_discussion_hover(self, e, table_name, show_delete):
        """Show/hide delete button on hover (only for discussions)"""
        if show_delete:
            # Find the delete button in the row's controls
            row = e.control.content
            delete_button = row.controls[-1]  # Last control is the delete button
            
            # Toggle visibility based on hover state
            delete_button.visible = e.data == "true"
            e.control.update()

    def delete_discussion(self, e, confirm=False):
        """Handle discussion deletion without confirmation dialog"""
        table_name = e.control.data
        
        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {table_name}")
            conn.commit()
            conn.close()
            
            # If we're currently viewing this discussion, switch to default
            if self.current_selected == table_name:
                self.main_app.switch_discussion("messages")
                self.current_selected = "messages"
            
            # Refresh sidebar
            self.refresh_sidebar(e.page)
            
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Deleted discussion: {table_name}"), 
                    open=True
                )
            )
        except Exception as ex:
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Error deleting discussion: {str(ex)}"), 
                    open=True
                )
            )

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
            
            # Switch to the new discussion
            self.main_app.switch_discussion(table_name)
            
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

    def refresh_sidebar(self, page, new_table_name=None):
        """Refresh the sidebar to include the newly created table"""
        # Get the current table names including the new one
        table_names = self.get_database_tables()
        
        # Update current selection if new table was created
        if new_table_name:
            self.current_selected = new_table_name
        
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
        """Handle table click event - switch to this discussion"""
        # Update the current selection
        self.current_selected = table_name
        
        # Switch to the selected discussion
        self.main_app.switch_discussion(table_name)
        
        # Refresh the sidebar to update the highlight
        self.refresh_sidebar(e.page)
        
        e.page.show_snack_bar(
            ft.SnackBar(
                ft.Text(f"Switched to discussion: {table_name}"), 
                open=True
            )
        )

def render_sidebar(main_app):
    return ModernNavBar(main_app)
