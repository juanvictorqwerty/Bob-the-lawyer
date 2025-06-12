import flet as ft  # Flet library for creating the user interface.
import sqlite3      # SQLite library for database operations.

class ModernNavBar(ft.Container):
    """
    A custom Flet Container that acts as a sidebar navigation bar.
    It displays a list of discussions, allows creating new ones, and deleting existing ones.
    """
    def __init__(self, main_app):
        self.main_app = main_app  # Reference to the main app
        self.current_selected = None  # Track currently selected discussion
        self.highest_discussion_num = 0  # Track the highest number used in "discussion_X" table names.
        
        table_names = self.get_database_tables()  # Fetch existing discussion table names from the database.
        self.update_highest_discussion_num(table_names)  # Initialize highest_discussion_num based on existing tables.
        
        super().__init__(
            width=250,  # Fixed width for the sidebar.
            padding=10, # Padding around the content of the sidebar.
            clip_behavior=ft.ClipBehavior.HARD_EDGE, # Defines how content is clipped if it overflows.
            # The main content of the sidebar is a Column.
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                controls=[
                    ft.Container(
                        padding=ft.padding.only(bottom=20),
                        content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD) # Title at the top of the sidebar.
                    ),
                    self.create_discussion_button(),  # Button to create new discussions.
                    *self.create_table_list_items(table_names),  # List items for each existing discussion.
                ],
            ),
        )


    def update_highest_discussion_num(self, table_names):
        """Find the highest discussion number from existing tables"""
        for table in table_names: # Iterate through the list of table names.
            if table.startswith("discussion_"): # Check if the table name follows the "discussion_X" pattern.
                try:
                    num = int(table.split("_")[1])  # Extract the number part.
                    if num > self.highest_discussion_num: # If this number is higher than the current max.
                        self.highest_discussion_num = num # Update the highest number.
                except (IndexError, ValueError): # Handle cases where splitting or conversion fails.
                    continue # Skip to the next table name.

    def create_discussion_button(self):
        """Create the 'Create Discussion' button"""
        return ft.Container(
            padding=ft.padding.symmetric(vertical=10, horizontal=15),
            content=ft.Row(
                controls=[
                    ft.Icon(name=ft.Icons.ADD, size=18),
                    ft.Text("Create a Discussion", size=14), # Text label for the button.
                ],
                spacing=10
            ),
            border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)), # Bottom border for visual separation.
            on_click=self.create_new_discussion # Function to call when the button is clicked.
        )

    def create_new_discussion(self, e):
        """Create a new discussion table in the database"""
        try:
            # Increment the discussion number
            self.highest_discussion_num += 1
            table_name = f"discussion_{self.highest_discussion_num}" # Generate a new unique table name.
            
            conn = sqlite3.connect(self.main_app.get_database_path()) # Connect to the database.
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
            conn.commit() # Save changes to the database.
            conn.close() # Close the database connection.
            
            # Switch to the new discussion
            self.main_app.switch_discussion(table_name) # Make the new discussion active in the main app.
            
            # Refresh the sidebar to show the new table
            self.refresh_sidebar(e.page, table_name) # Update the sidebar UI.

        except Exception as ex: # Catch any errors during the process.
            e.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Error creating discussion: {str(e)}"), 
                    open=True
                )
            )

    def get_database_tables(self):
        """Fetch all table names from the SQLite database, sorted in descending order."""
        try:
            conn = sqlite3.connect(self.main_app.get_database_path()) # Connect to the database.
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';") # SQL query to get all table names.
            tables_data = cursor.fetchall() # Fetch all results.
            conn.close() # Close the connection.
            
            # Filter for tables starting with "discussion_"
            table_names = [
                table[0] for table in tables_data if table[0].startswith("discussion_")
            ]
            # Sort the table names in descending (reverse alphabetical) order
            table_names.sort(reverse=True) # This ensures newer discussions appear at the top.
            return table_names
        except Exception as e: # Handle potential database access errors.
            print(f"Error accessing database: {e}")
            return [] # Return an empty list on error

    def create_table_list_items(self, table_names):
        """Create list items for each table name"""
        items = []
        for table in table_names:
            # Determine if the delete button should be shown (only for "discussion_X" tables).
            show_delete = table.startswith("discussion_") 
            
            items.append(
                ft.Container(
                    padding=ft.padding.symmetric(vertical=10, horizontal=15),
                    content=ft.Row(
                        controls=[
                            ft.Icon(name=ft.Icons.TABLE_ROWS, size=18),
                            ft.Text(
                                table, 
                                size=14,
                                color=ft.Colors.WHITE if table == self.current_selected else None # Highlight if selected.
                            ),
                            # Delete button (only visible on hover and for discussions)
                            ft.IconButton(
                                icon=ft.Icons.DELETE,
                                icon_size=18,
                                icon_color=ft.Colors.RED_400,
                                visible=False,  # Hidden by default
                                data=table,  # Store table name in button data
                                on_click=self.delete_discussion,
                            ) if show_delete else ft.Container(width=0)  # Empty container if not deletable
                        ],
                        spacing=10,
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    ),
                    border=ft.border.only(bottom=ft.BorderSide(1, ft.Colors.GREY_300)), # Bottom border.
                    bgcolor=ft.Colors.BLUE_800 if table == self.current_selected else None, # Background highlight if selected.
                    on_click=lambda e, table=table: self.on_table_click(e, table), # Click handler.
                    on_hover=lambda e, table=table: self.on_discussion_hover(e, table, show_delete), # Hover handler.
                )
            )
        return items

    def on_discussion_hover(self, e, table_name, show_delete):
        """Show/hide delete button on hover (only for discussions)"""
        if show_delete:
            # Find the delete button in the row's controls
            row = e.control.content # The Row control within the hovered Container.
            delete_button = row.controls[-1]  # Last control is the delete button
            
            # Toggle visibility based on hover state
            delete_button.visible = e.data == "true" # Flet sets e.data to "true" on hover-in, "false" on hover-out.
            e.control.update() # Update the UI to reflect visibility change.

    def delete_discussion(self, e, confirm=False):
        """Handle discussion deletion without confirmation dialog"""
        table_name = e.control.data # Get the table name stored in the button's data attribute.
        
        try:
            conn = sqlite3.connect(self.main_app.get_database_path()) # Connect to DB.
            cursor = conn.cursor()
            cursor.execute(f"DROP TABLE {table_name}") # SQL to delete the table.
            conn.commit() # Save changes.
            conn.close() # Close connection.
            
            # If we're currently viewing this discussion, switch to default
            if self.current_selected == table_name:
                self.current_selected = None # Clear the current selection.
                self.main_app.switch_discussion(None) # Tell main_app no discussion is selected.
                self.main_app.clear_chat()  # Clear the chat history
            
            # Refresh sidebar
            self.refresh_sidebar(e.page) # Update the sidebar UI.
            
            self.main_app.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Deleted discussion: {table_name}"), 
                    open=True
                )
            )
        except Exception as ex: # Handle errors during deletion.
            self.main_app.page.show_snack_bar(
                ft.SnackBar(
                    ft.Text(f"Error deleting discussion: {str(ex)}"), 
                    open=True
                )
            )

    def refresh_sidebar(self, page, new_table_name=None):
        """Refresh the sidebar to include the newly created table"""
        # Get the current table names including the new one
        table_names = self.get_database_tables() # Fetch the updated list of tables.
        
        # Update current selection if new table was created
        if new_table_name:
            self.current_selected = new_table_name # Set the new table as the currently selected one.
        
        # Rebuild the controls
        self.content.controls = [
            ft.Container(
                padding=ft.padding.only(bottom=20),
                content=ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)
            ),
            self.create_discussion_button(), # Add the "Create Discussion" button.
            *self.create_table_list_items(table_names), # Add list items for all discussions.
        ]
        
        # Update the page
        page.update()

    def on_table_click(self, e, table_name):
        """Handle table click event - switch to this discussion"""
        # Update the current selection
        self.current_selected = table_name # Mark this table as selected.
        
        # Switch to the selected discussion
        self.main_app.switch_discussion(table_name) # Tell the main app to load this discussion.
        
        # Refresh the sidebar to update the highlight
        self.refresh_sidebar(e.page) # Update the sidebar UI to reflect the selection.
        
        e.page.show_snack_bar(
            ft.SnackBar(
                ft.Text(f"Switched to discussion: {table_name}"), 
                open=True
            )
        )

def render_sidebar(main_app):
    """
    Factory function to create and return an instance of ModernNavBar.
    This is typically called by the main application to instantiate the sidebar.
    """
    return ModernNavBar(main_app)
