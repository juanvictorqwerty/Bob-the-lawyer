import flet as ft  # Flet library for creating the user interface.
import sqlite3      # SQLite library for database operations.
from datetime import datetime  # For handling timestamps.
from model_handler import generate_reply  # Function to interact with the AI model.
from sidebar import render_sidebar  # Function to render the sidebar UI component.
import os           # For operating system interactions, like file paths.
import platform     # For detecting the operating system to set appropriate paths.
import requests     # For making HTTP requests, used here for web search.

# Import file processing libraries
import pypdf  # Library for reading PDF files.
from docx import Document  # Library for reading DOCX files (Microsoft Word).
from pptx import Presentation  # Library for reading PPTX files (Microsoft PowerPoint).
import openpyxl  # Library for reading XLSX and XLS files (Microsoft Excel).


class LawyerChatBotApp:
    """
    Main class for the Lawyer Chat Bot application.
    Manages the UI, database interactions, chat logic, and file handling.
    """
    def __init__(self, page: ft.Page):
        self.page = page  # The Flet page object, representing the main window/view.
        self.page.theme_mode = ft.ThemeMode.LIGHT  # Default to light theme
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)  # UI element to display chat messages.
        self.current_discussion = None  # Stores the name of the currently active discussion table.
        
        # Theme toggle button
        self.theme_toggle = ft.IconButton(
            icon=ft.Icons.DARK_MODE,  # Icon for the theme toggle button.
            on_click=self.toggle_theme,  # Function to call when the button is clicked.
            tooltip="Toggle dark/light mode",  # Tooltip text for the button.
        )
        
        # Initialize file picker
        self.file_picker = ft.FilePicker(
            on_result=self.handle_file_upload,  # Function to call when files are picked.
        )
        self.page.overlay.append(self.file_picker)  # Add file picker to the page's overlay (required by Flet).
        self.sidebar = render_sidebar(self) if 'render_sidebar' in globals() else ft.Container() # Renders the sidebar if available.
        
        # Input controls
        self.user_input = ft.TextField(
            hint_text="Type your legal question or upload documents...",  # Placeholder text.
            expand=True,  # Allow the text field to expand.
            multiline=True,  # Allow multiple lines of input.
            min_lines=1,     # Minimum number of lines.
            max_lines=5,     # Maximum number of lines.
        )
        self.send_button = ft.IconButton(
            icon=ft.Icons.SEND,  # Icon for the send button.
            on_click=self.send_click,  # Function to call on click.
            tooltip="Send question",   # Tooltip text.
        )
        self.upload_button = ft.IconButton(
            icon=ft.Icons.UPLOAD_FILE,  # Icon for the upload button.
            on_click=self.upload_files,   # Function to call on click.
            tooltip="Upload documents",   # Tooltip text.
        )
        self.search_button = ft.IconButton(
            icon=ft.Icons.SEARCH,  # Icon for the search button.
            on_click=self.web_search_click,  # Function to call on click.
            tooltip="Search the web",        # Tooltip text.
        )
        self.current_files = []  # List to store information about currently uploaded files for a single query.
        
        # Initialize database and load previous messages
        self.initialize_database()  # Sets up the database connection.
        self.init_ui()              # Sets up the main user interface layout.
        self.update_theme_colors()  # Set initial theme colors
        self.switch_discussion(self.current_discussion) # Set initial state for inputs (disables them if no discussion).

    def init_ui(self):
        """Initializes the main user interface layout of the application."""
        self.page.title = "Bob the lawyer"  # Set the window title.
        self.page.window_width = 900        # Set the initial window width.
        self.page.window_height = 700       # Set the initial window height.
        self.page.padding = 20              # Set padding around the page content.

        # Header with title and theme toggle
        header = ft.Row(
            controls=[
                ft.Text("Chat", size=24, weight=ft.FontWeight.BOLD),  # Main title for the chat area.
                self.theme_toggle,  # Theme toggle button.
            ],
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,  # Align items with space between them.
        )

        # Main column for the chat interface (header, chat view, input row)
        main_column = ft.Column(
            expand=True,  # Allow the column to expand and fill available space.
            controls=[
                header,  # Add the header row.
                ft.Divider(color=ft.Colors.GREY_600 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_300), # A visual separator.
                self.chat,  # The chat message list view.
                ft.Row(
                    [
                        self.upload_button,  # Upload button.
                        self.user_input,     # User text input field.
                        self.search_button,  # Web search button.
                        self.send_button,    # Send message button.
                    ],
                    spacing=5,  # Spacing between controls in the input row.
                    alignment=ft.MainAxisAlignment.START,  # Align controls to the start of the row.
                ),
            ],
        )

        # Main content layout: sidebar and the main chat column, separated by a vertical line.
        content = ft.Row(
            controls=[
                self.sidebar,  # The sidebar for discussions.
                ft.Container(width=1, bgcolor=ft.Colors.GREY_600 if self.page.theme_mode == ft.ThemeMode.DARK else ft.Colors.GREY_300), # Vertical separator.
                main_column,  # The main chat area.
            ],
            expand=True,  # Allow this row to expand.
        )

        self.page.add(content)  # Add the main content layout to the page.
        self.user_input.focus() # Set focus to the user input field on startup.

    def initialize_database(self):
        """Connect to the database and set up the cursor."""
        self.conn = sqlite3.connect(self.get_database_path())
        self.cursor = self.conn.cursor()
        

    def _create_table_if_not_exists(self, table_name):
        """Creates a specific table if it doesn't already exist.
            This uses the standard schema for discussion tables.
            This method MUST be called from the main thread (UI thread)
            as it accesses the database connection.
        """ # Note: This method is intended to be called from the UI thread.
        if not table_name: # Avoid issues with empty table names
            print("Error: Attempted to create a table with no name.")
            return
        try:
            self.cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS "{table_name}" (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME NOT NULL
            )
        ''')
            
        except sqlite3.Error as e:
            print(f"Error creating table {table_name}: {e}")

    def get_database_path(self):
        """Get the appropriate database path based on the OS."""
        system = platform.system()  # Get the current operating system name.
        if system == "Windows":  # For Windows.
            app_data_dir = os.path.join(os.environ['LOCALAPPDATA'], "BobTheLawyer")  # Use Local AppData.
        elif system == "Darwin":  # For macOS.
            app_data_dir = os.path.expanduser("~/Library/Application Support/BobTheLawyer")  # Use Application Support.
        else:  # For Linux and other Unix-like systems.
            app_data_dir = os.path.expanduser("~/.bobthelawyer")  # Use a hidden directory in the user's home.

        # Create the directory if it doesn't exist
        os.makedirs(app_data_dir, exist_ok=True)  # Ensure the directory exists.

        db_path = os.path.join(app_data_dir, "database.db")  # Path to the database file.
        return db_path

    # Removed the original load_previous_messages

    def load_previous_messages(self, table_to_load: str):
        """Load previous messages from the specified discussion table.
        This method must be called from the main thread.
        """
        self.clear_chat()  # Clear existing messages from the UI.

        if table_to_load:  # Only proceed if a table name is provided.
            try:
                self.cursor.execute(
                    f'SELECT sender, message FROM "{table_to_load}" ORDER BY timestamp' # Fetch messages ordered by time.
                )
                messages = self.cursor.fetchall()  # Get all fetched messages.

                for sender, message_content in messages: # Renamed for clarity
                    if sender == "user":  # If the sender is the user.
                        self.chat.controls.append(self.create_user_message(message_content))  # Add user message UI.
                    elif sender == "file":  # If the message represents a file.
                        # Parse file_name and content_preview from message_content
                        # Expected format from store_message: f"{file_name}: {content_preview}"
                        parts = message_content.split(": ", 1)  # Split the stored message.
                        if len(parts) == 2:  # If parsing is successful.
                            file_name, content_preview = parts  # Extract file name and preview.
                            self.chat.controls.append(self.create_file_message(file_name, content_preview)) # Add file message UI.
                        else: # If parsing fails.
                            # Fallback if parsing fails, render as a bot message
                            self.chat.controls.append(self.create_bot_message(f"File (error displaying): {message_content}")) # Show error.
                    elif sender == "bot" or sender == "system": # Explicitly handle bot and system messages
                        self.chat.controls.append(self.create_bot_message(message_content)) # Add bot/system message UI.
                    else: # Fallback for any other unexpected sender type
                        self.chat.controls.append(self.create_bot_message(f"Unknown ({sender}): {message_content}")) # Show as unknown.
                self.page.update()  # Update the UI to display loaded messages.
            except sqlite3.OperationalError as e:  # Handle cases like table not found.
                print(f"Error loading messages from table '{table_to_load}': {str(e)}")
                self.chat.controls.append(
                    self.create_bot_message(f"⚠️ Error loading discussion '{table_to_load}': {str(e)}") # Show error in chat.
                )
                self.page.update() # Update UI.

    def clear_chat(self):
        """Clear the current chat display"""
        self.chat.controls.clear()
        self.current_files = []
        self.page.update()

    def switch_discussion(self, table_name):
        """Switch to a different discussion table or handle no active discussion."""
        self.current_discussion = table_name  # Update the currently active discussion. Can be None.

        if table_name is None:  # If no discussion is selected (e.g., on startup or after deleting current).
            self.clear_chat()  # Clear the chat UI.
            # Add a placeholder message to the chat
            self.chat.controls.append( # Display a message prompting user to select/create a discussion.
                ft.Container(
                    content=ft.Text(
                        "Select or create a discussion from the sidebar to begin.",
                        italic=True,
                        opacity=0.6,
                        text_align=ft.TextAlign.CENTER
                    ),
                    alignment=ft.alignment.center,
                    padding=20
                )
            )
            # Disable input controls as there's no active discussion.
            self.user_input.disabled = True 
            self.send_button.disabled = True 
            self.upload_button.disabled = True 
            self.search_button.disabled = True 
        else: # If a discussion is selected.
            self.load_previous_messages(table_name)  # This calls clear_chat() internally
            # Enable input controls.
            self.user_input.disabled = False 
            self.send_button.disabled = False 
            self.upload_button.disabled = False 
            self.search_button.disabled = False 
        self.page.update() # Update the UI to reflect changes.

    def create_user_message(self, message):
        """Creates a Flet UI container for a user's message."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK  # Check current theme for styling.
        # Calculate width based on message length but cap at 600
        text_width = min(600, len(message) * 8 + 100) # Dynamically adjust width, with a max.
        return ft.Row(
            controls=[
                ft.Container(expand=True),  # This pushes the message container to the right
                ft.Container(
                    content=ft.Text(
                        value=message,
                        selectable=True,
                        size=15,
                        color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK, # Text color based on theme.
                    ),
                    alignment=ft.alignment.center_right, # Align text to the right within the container.
                    bgcolor=ft.Colors.BLUE_800 if is_dark else ft.Colors.BLUE_100, # Background color based on theme.
                    padding=ft.padding.symmetric(horizontal=14, vertical=10), # Padding inside the message bubble.
                    border_radius=ft.border_radius.only(
                        top_left=16,
                        top_right=16,
                        bottom_left=16,
                        bottom_right=4,
                    ),
                    margin=ft.margin.only(bottom=6),
                    shadow=ft.BoxShadow( # Add a subtle shadow for depth.
                        spread_radius=0.5,
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 1.5),
                    ),
                    width=text_width, # Apply the calculated width
                )
            ],
            alignment=ft.MainAxisAlignment.END,  # Align the entire row (message bubble) to the right.
            expand=True, # Allow the row to expand.
        )

    def create_bot_message(self, message):
        """Creates a Flet UI container for a bot's message."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK # Check current theme for styling.
        # Calculate width based on message length but cap at 600
        text_width = min(600, len(message) * 8 + 100) # Dynamically adjust width, with a max.
        return ft.Row(
            controls=[
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "BOB:",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.BLUE_200 if is_dark else ft.Colors.BLUE_800, # "BOB:" label color.
                            ),
                            ft.Container(
                                content=ft.Text(
                                    message,
                                    selectable=True,
                                    size=15,
                                    color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK, # Message text color.
                                ),
                            )
                        ],
                        spacing=4, # Spacing between "BOB:" and the message.
                        tight=True, # Reduce extra spacing in the column.
                        scroll=ft.ScrollMode.AUTO, # Allow scrolling if content overflows.
                    ),
                    alignment=ft.alignment.center_left, # Align content to the left.
                    bgcolor=ft.Colors.GREEN_800 if is_dark else ft.Colors.GREEN_100, # Background color.
                    padding=ft.padding.symmetric(horizontal=14, vertical=10), # Padding.
                    border_radius=ft.border_radius.only( # Rounded corners for bubble effect.
                        top_left=16,
                        top_right=16,
                        bottom_left=4,
                        bottom_right=16,
                    ),
                    margin=ft.margin.only(bottom=6),
                    shadow=ft.BoxShadow(
                        spread_radius=0.5, # Shadow for depth.
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 1.5),
                    ),
                    width=text_width,  # Use the calculated width
                )
            ],
            alignment=ft.MainAxisAlignment.START, # Align the row (message bubble) to the left.
            vertical_alignment=ft.CrossAxisAlignment.START, # Align content to the top of the row.
            expand=True, # Allow row to expand.
            scroll=ft.ScrollMode.AUTO, # Allow scrolling if content overflows.
        )
    def create_file_message(self, file_name, content_preview):
        """Creates a Flet UI container to display information about an uploaded file."""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK # Check current theme.
        # Calculate width based on message length but cap at 600
        text_width = min(600, (len(file_name) + len(content_preview)) * 6 + 100) # Dynamic width.
        return ft.Row(
            [
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text(
                                f"📄 {file_name}",
                                size=15,
                                weight=ft.FontWeight.BOLD,
                                color=ft.Colors.WHITE if is_dark else ft.Colors.BLUE_800, # File name color.
                            ),
                            ft.Text(
                                content_preview,
                                selectable=True,
                                size=12,
                                color=ft.Colors.WHITE if is_dark else ft.Colors.BLACK, # Preview text color.
                            )
                        ],
                        spacing=4, # Spacing.
                        tight=True, # Reduce extra spacing.
                    ),
                    alignment=ft.alignment.center_right, # Align to right (like user messages).
                    bgcolor=ft.Colors.BLUE_800 if is_dark else ft.Colors.BLUE_100, # Background color.
                    padding=ft.padding.symmetric(horizontal=14, vertical=10), # Padding.
                    border_radius=ft.border_radius.only( # Rounded corners.
                        top_left=16,
                        top_right=16,
                        bottom_left=16,
                        bottom_right=4,
                    ),
                    margin=ft.margin.only(bottom=6),
                    shadow=ft.BoxShadow( # Shadow.
                        spread_radius=0.5,
                        blur_radius=3,
                        color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK),
                        offset=ft.Offset(0, 1.5),
                    ),
                    width=text_width, # Apply calculated width.
                )
            ],
            alignment=ft.MainAxisAlignment.END, # Align the row to the right.
        )

    def store_message(self, sender, message):
        """Store a message in the database"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        try:
            self.cursor.execute(f'''
                INSERT INTO "{self.current_discussion}" (sender, message, timestamp)
                VALUES (?, ?, ?)
            ''', (sender, message, timestamp)) # Use placeholders to prevent SQL injection.
            self.conn.commit() # Commit the transaction.
        except sqlite3.OperationalError as e: # Typically "no such table"
            print(f"Error storing message (table '{self.current_discussion}' might not exist): {str(e)}")
            # Try to create the table if it doesn't exist
            self._create_table_if_not_exists(self.current_discussion)
            # Retry storing the message (within the same thread after table creation)
            try:
                self.cursor.execute(f'''
                    INSERT INTO "{self.current_discussion}" (sender, message, timestamp)
                    VALUES (?, ?, ?)
                ''', (sender, message, timestamp))
                self.conn.commit()
            except sqlite3.Error as e_retry:
                print(f"Retry failed for storing message: {e_retry}")


    def upload_files(self, e):
        """Opens the file picker dialog to allow the user to select files."""
        self.file_picker.pick_files(
            allowed_extensions=[
                "pdf", "docx", "pptx", "xls", "xlsx", 
            ],
        )
        
    def handle_file_upload(self, e: ft.FilePickerResultEvent):
        """Processes files selected by the user through the file picker."""
        if not e.files: # If no files were selected.
            return
            
        for uploaded_file in e.files: # Iterate through each selected file.
            file_path = uploaded_file.path  # Path to the uploaded file.
            file_name = uploaded_file.name  # Name of the uploaded file.
            file_ext = os.path.splitext(file_name)[1].lower() # File extension.
            
            try:
                # Extract text based on file extension.
                if file_ext == '.pdf': 
                    text = self.extract_text_from_pdf(file_path)
                elif file_ext == '.docx':
                    text = self.extract_text_from_docx(file_path)
                elif file_ext == '.pptx':
                    text = self.extract_text_from_pptx(file_path)
                elif file_ext in ('.xls', '.xlsx'):
                    text = self.extract_text_from_excel(file_path)
                else:
                    text = f"Unsupported file type: {file_ext}"
                
                # Store file content
                self.current_files.append({
                    "name": file_name,
                    "path": file_path,
                    "content": text
                }) # Add file info and content to a temporary list for the current query.
                
                # Generate 4-line preview for display and storage
                original_lines = text.splitlines() # Split content into lines.
                num_original_lines = len(original_lines) # Count lines.

                if num_original_lines > 4: # If more than 4 lines.
                    # If more than 4 lines, show the first 3 and append "..." on a new line (total 4 lines for preview)
                    preview_lines_to_show = original_lines[:3] # Take first 3 lines.
                    preview = "\n".join(preview_lines_to_show) + "\n..."
                else:
                    # If 4 or fewer lines, show all of them.
                    preview = "\n".join(original_lines)

                # Show file preview in chat
                self.chat.controls.append(
                    self.create_file_message(file_name, preview)) # Display file info in chat.
                
                # Store upload action and file preview in database
                self.store_message("user", f"Uploaded document: {file_name}") # Log user action.
                self.store_message("file", f"{file_name}: {preview}") # Use the generated 4-line preview
                
            except Exception as ex: # Handle errors during file processing.
                error_msg = f"Error processing {file_name}: {str(ex)}"
                self.chat.controls.append(
                    self.create_bot_message(error_msg)) # Show error in chat.
                    
        self.page.update() # Update UI.

    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extracts all text from a PDF file."""
        text = []
        with open(file_path, 'rb') as file: # Open in binary read mode.
            reader = pypdf.PdfReader(file) # Create a PDF reader object.
            for page in reader.pages: # Iterate through each page.
                text.append(page.extract_text()) # Extract text from the page.
        return "\n".join(text)

    def extract_text_from_docx(self, file_path: str) -> str:
        """Extracts all text from a DOCX file."""
        doc = Document(file_path) # Open the DOCX document.
        return "\n".join([para.text for para in doc.paragraphs]) # Join text from all paragraphs.

    def extract_text_from_pptx(self, file_path: str) -> str:
        """Extracts text from all shapes in all slides of a PPTX file."""
        prs = Presentation(file_path) # Open the PowerPoint presentation.
        text = []
        for slide in prs.slides: # Iterate through each slide.
            for shape in slide.shapes: # Iterate through each shape on the slide.
                if hasattr(shape, "text"): # If the shape contains text.
                    text.append(shape.text) # Append the text.
        return "\n".join(text)

    def extract_text_from_excel(self, file_path: str) -> str:
        """Extract text from all cells in all sheets of an Excel file."""
        workbook = openpyxl.load_workbook(file_path, data_only=True) # data_only=True to get cell values, not formulas
        all_text = []
        for sheet_name in workbook.sheetnames: # Iterate through each sheet.
            sheet = workbook[sheet_name] # Get the sheet object.
            sheet_text = []
            for row in sheet.iter_rows(): # Iterate through each row.
                for cell in row: # Iterate through each cell in the row.
                    if cell.value is not None: # If the cell has a value.
                        sheet_text.append(str(cell.value)) # Append the cell value as string.
            if sheet_text: # Add sheet name if it has content
                all_text.append(f"--- Sheet: {sheet_name} ---\n" + "\n".join(sheet_text)) # Add sheet content with a header.
        return "\n\n".join(all_text)


    def web_search_click(self, e):
        """Handle web search button click"""
        query = self.user_input.value.strip() # Get the query from the input field.
        if not query:
            return

        if not self.current_discussion:
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Please select or create a discussion first."), open=True)
            )
            return

        # Store and display query
        self.store_message("user", f"WEB SEARCH: {query}") # Log the search query.
        self.chat.controls.append(self.create_user_message(f"🔍 Searching: {query}")) # Display search action in chat.
        
        # Show loading indicator while searching.
        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Searching the web...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        self.chat.controls.append(thinking)
        # Disable input fields during search.
        self.user_input.disabled = True
        self.send_button.disabled = True
        self.upload_button.disabled = True
        self.search_button.disabled = True
        self.page.update()

        try:
            # Perform search with direct API key
            api_key = "c993fe8beec5d447b42da49cec429aab6460e9170118ba6eb56473f574705105" # SerpApi API key.
            params = {
                "q": query,
                "engine": "google",
                "api_key": api_key,
                "num": 3
            }
            
            response = requests.get("https://serpapi.com/search", params=params, timeout=10) # Make the API request.
            response.raise_for_status()  # Raise an exception for bad status codes (4xx or 5xx).
            results = response.json() # Parse the JSON response.
            
            if "organic_results" in results: # Check if organic search results are present.
                output = ["🌐 Web Results:"]
                for idx, res in enumerate(results["organic_results"][:3], 1): # Format top 3 results.
                    output.append(f"{idx}. {res.get('title', 'No title')}\n   {res.get('snippet', 'No description')}\n   {res.get('link', 'No URL')}\n")
                result = "\n".join(output)
            else:
                result = "🔍 No results found"
            
            self.store_message("bot", result) # Store the search results.
            self.chat.controls.remove(thinking) # Remove loading indicator.
            self.chat.controls.append(self.create_bot_message(result)) # Display results in chat.
            
        except Exception as err: # Handle any errors during the search process.
            error_msg = f"⚠️ Search failed: {str(err)}"
            self.store_message("system", error_msg) # Log the error.
            self.chat.controls.remove(thinking) # Remove loading indicator.
            self.chat.controls.append(self.create_bot_message(error_msg)) # Display error in chat.
            
        # Reset input fields and buttons.
        self.user_input.value = ""
        self.user_input.disabled = False
        self.send_button.disabled = False
        self.upload_button.disabled = False
        self.search_button.disabled = False
        self.theme_toggle.disabled = False  
        self.page.update()

    def toggle_theme(self, e):
        """Toggle between light and dark theme"""
        self.page.theme_mode = (
            ft.ThemeMode.DARK # Switch to dark if current is light.
            if self.page.theme_mode == ft.ThemeMode.LIGHT
            else ft.ThemeMode.LIGHT # Switch to light if current is dark.
        )
        self.theme_toggle.icon = (
            ft.Icons.LIGHT_MODE # Set icon to light mode if theme is dark.
            if self.page.theme_mode == ft.ThemeMode.DARK
            else ft.Icons.DARK_MODE # Set icon to dark mode if theme is light.
        )
        self.update_theme_colors() # Apply color changes to UI elements.
        # Re-render the chat messages with the new theme
        if self.current_discussion:  # Check if a discussion is active
            self.load_previous_messages(self.current_discussion) # Reload messages to apply new theme styles.
        self.page.update() # Update the page.


    def update_theme_colors(self):
        """Update all color references based on current theme"""
        is_dark = self.page.theme_mode == ft.ThemeMode.DARK
        
        # Update page colors
        self.page.bgcolor = ft.Colors.GREY_900 if is_dark else ft.Colors.GREY_50
        
        # Update input field
        self.user_input.color = ft.Colors.WHITE if is_dark else ft.Colors.BLACK
        self.user_input.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.GREY_500 if is_dark else ft.Colors.GREY_200)
        self.user_input.border_color = ft.Colors.GREY_600 if is_dark else ft.Colors.GREY_300
        
        # Update buttons
        self.send_button.Icon_color = ft.Colors.WHITE if is_dark else ft.Colors.BLUE_700
        self.upload_button.Icon_color = ft.Colors.WHITE if is_dark else ft.Colors.BLUE_700
        self.theme_toggle.Icon_color = ft.Colors.WHITE if is_dark else ft.Colors.BLUE_700
        self.search_button.Icon_color = ft.Colors.WHITE if is_dark else ft.Colors.BLUE_700   

    def send_click(self, e):
        """Handles the click event of the send button."""
        question = self.user_input.value.strip() # Get user input.
        if not question and not self.current_files: # If no text and no files, do nothing.
            return
        
        if not self.current_discussion: # If no discussion is active, show a snackbar.
            self.page.show_snack_bar(
                ft.SnackBar(content=ft.Text("Please select or create a discussion first."), open=True)
            )
            return

        # If there are files, include them in the context
        context = ""
        if self.current_files: # If files have been uploaded for this query.
            context = "\n\n[Attached Files Context]\n"
            for file in self.current_files: # Append content of each file to the context.
                context += f"\nFile: {file['name']}\nContent:\n{file['content'][:1000]}\n"
            self.current_files = []  # Clear the list of current files after they are used.

        if question: # If there is a text question.
            full_question = question + context
            self.store_message("user", question) # Store the user's text question.
            self.chat.controls.append(self.create_user_message(question)) # Display user's question.
        else: # If only files were uploaded without a specific question.
            full_question = "Please analyze these documents:" + context
            self.store_message("user", "Uploaded documents for analysis") # Store a generic message.

        if context and not question: # If only files were uploaded, add a message indicating this.
            self.chat.controls.append(self.create_bot_message("Received documents for analysis"))

        # Show "Thinking..." indicator.
        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Thinking...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        self.chat.controls.append(thinking)
        # Disable inputs while processing.
        self.user_input.disabled = True
        self.send_button.disabled = True
        self.upload_button.disabled = True
        self.search_button.disabled = True
        self.theme_toggle.disabled = True # Disable before page update
        self.page.update()

        try:
            reply = generate_reply(full_question) # Get reply from the AI model.
            self.store_message("bot", reply) # Store bot's reply.
        except Exception as err: # Handle errors from the model.
            reply = f"⚠️ Error: {str(err)}"
            self.store_message("system", f"Error: {str(err)}") # Log system error.

        self.chat.controls.remove(thinking) # Remove "Thinking..." indicator.
        self.chat.controls.append(self.create_bot_message(reply)) # Display bot's reply.

        # Re-enable inputs.
        self.user_input.value = ""
        self.user_input.disabled = False
        self.send_button.disabled = False
        self.upload_button.disabled = False
        self.theme_toggle.disabled = False
        self.search_button.disabled = False
        self.page.update() # Update UI.
        self.user_input.focus() # Set focus back to input field.


    def __del__(self):
        """Close database connection when the app is closed"""
        if hasattr(self, 'conn'): # Check if connection object exists.
            self.conn.close() # Close the database connection.


def main(page: ft.Page):
    """Main function to start the Flet application."""
    LawyerChatBotApp(page) # Create an instance of the app.

ft.app(target=main)
