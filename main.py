import flet as ft
import sqlite3
from datetime import datetime
import os
import base64
import mimetypes
import json
from model_handler import generate_reply

class LawyerChatBotApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        
        # File picker for documents and images
        self.file_picker = ft.FilePicker(on_result=self.file_picker_result)
        self.page.overlay.append(self.file_picker)
        
        # Camera capture (for mobile/devices with camera)
        self.camera_picker = ft.FilePicker(on_result=self.camera_result)
        self.page.overlay.append(self.camera_picker)
        
        self.user_input = ft.TextField(
            hint_text="Type your legal question...",
            expand=True,
            multiline=True,
            min_lines=1,
            max_lines=5,
            on_submit=self.send_click,
        )
        
        # Attachment button with dropdown menu - FIXED: Updated icon references
        self.attachment_button = ft.PopupMenuButton(
            icon=ft.icons.ATTACH_FILE,
            tooltip="Attach file",
            items=[
                ft.PopupMenuItem(
                    text="Upload Document",
                    icon=ft.icons.DESCRIPTION,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["pdf", "docx", "doc", "txt", "rtf"]
                    )
                ),
                ft.PopupMenuItem(
                    text="Upload Image",
                    icon=ft.icons.IMAGE,
                    on_click=lambda _: self.file_picker.pick_files(
                        allow_multiple=False,
                        allowed_extensions=["jpg", "jpeg", "png", "gif", "bmp", "webp"]
                    )
                ),
                ft.PopupMenuItem(
                    text="Take Photo",
                    icon=ft.icons.CAMERA_ALT,
                    on_click=self.take_photo
                ),
                ft.PopupMenuItem(
                    text="Any File",
                    icon=ft.icons.FOLDER,
                    on_click=lambda _: self.file_picker.pick_files(allow_multiple=False)
                ),
            ]
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND,
            on_click=self.send_click,
            tooltip="Send question",
        )
        
        # Container to show attached files - FIXED: Updated color reference
        self.attachments_container = ft.Container(
            content=ft.Column([], spacing=5),
            visible=False,
            padding=ft.padding.all(10),
            bgcolor="#F5F5F5",  # Using hex color instead of deprecated ft.colors.GREY_100
            border_radius=10,
            margin=ft.margin.only(bottom=10)
        )
        
        # Store current attachments
        self.current_attachments = []
        
        # Initialize database and load previous messages
        self.initialize_database()
        self.load_previous_messages()
        self.init_ui()

    def initialize_database(self):
        """Create database and table if they don't exist - FIXED: Added attachments columns"""
        try:
            self.conn = sqlite3.connect('database.db')
            self.cursor = self.conn.cursor()
            
            # Create messages table with all required columns including attachments
            self.cursor.execute('''
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    attachments TEXT DEFAULT '',
                    attachment_types TEXT DEFAULT ''
                )
            ''')
            
            # Check if attachments columns exist and add them if they don't
            self.cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            if 'attachments' not in columns:
                print("Adding attachments column to database...")
                self.cursor.execute("ALTER TABLE messages ADD COLUMN attachments TEXT DEFAULT ''")
                
            if 'attachment_types' not in columns:
                print("Adding attachment_types column to database...")
                self.cursor.execute("ALTER TABLE messages ADD COLUMN attachment_types TEXT DEFAULT ''")
                
            self.conn.commit()
            print("Database initialized successfully!")
            
        except sqlite3.Error as e:
            print(f"Database error during initialization: {e}")
            # Create a new database if there's an issue
            if hasattr(self, 'conn'):
                self.conn.close()
            self.conn = sqlite3.connect('database_backup.db')
            self.cursor = self.conn.cursor()
            self.cursor.execute('''
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    sender TEXT NOT NULL,
                    message TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    attachments TEXT DEFAULT '',
                    attachment_types TEXT DEFAULT ''
                )
            ''')
            self.conn.commit()

    def take_photo(self, e):
        """Handle camera capture"""
        try:
            self.camera_picker.pick_files(
                allow_multiple=False,
                allowed_extensions=["jpg", "jpeg", "png"]
            )
        except Exception as ex:
            self.show_snack_bar(f"Camera not available: {str(ex)}")

    def camera_result(self, e: ft.FilePickerResultEvent):
        """Handle camera capture result"""
        if e.files:
            self.handle_file_upload(e.files[0], "Camera Photo")

    def file_picker_result(self, e: ft.FilePickerResultEvent):
        """Handle file picker result"""
        if e.files:
            file = e.files[0]
            self.handle_file_upload(file, "Uploaded File")

    def handle_file_upload(self, file, source_type):
        """Handle uploaded file with comprehensive error handling"""
        try:
            file_path = file.path
            file_name = file.name
            file_size = file.size if hasattr(file, 'size') else os.path.getsize(file_path)
            
            # Check file size (limit to 10MB)
            if file_size > 10 * 1024 * 1024:
                self.show_snack_bar("File too large. Maximum size is 10MB.")
                return
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(file_path)
            
            # Read file content as base64 for storage
            with open(file_path, 'rb') as f:
                file_content = base64.b64encode(f.read()).decode('utf-8')
            
            # Create attachment info
            attachment_info = {
                'name': file_name,
                'type': mime_type or 'application/octet-stream',
                'size': file_size,
                'content': file_content,
                'source': source_type
            }
            
            self.current_attachments.append(attachment_info)
            self.update_attachments_display()
            self.show_snack_bar(f"{source_type} '{file_name}' attached successfully!")
            
        except Exception as ex:
            self.show_snack_bar(f"Error uploading file: {str(ex)}")
            print(f"File upload error: {ex}")

    def update_attachments_display(self):
        """Update the display of current attachments"""
        if not self.current_attachments:
            self.attachments_container.visible = False
        else:
            self.attachments_container.visible = True
            attachment_controls = []
            
            for i, attachment in enumerate(self.current_attachments):
                # Determine icon based on file type
                if attachment['type'] and attachment['type'].startswith('image/'):
                    icon = ft.icons.IMAGE
                elif attachment['type'] == 'application/pdf':
                    icon = ft.icons.PICTURE_AS_PDF
                elif attachment['type'] and ('word' in attachment['type'] or 
                     attachment['name'].endswith(('.doc', '.docx'))):
                    icon = ft.icons.DESCRIPTION
                else:
                    icon = ft.icons.ATTACH_FILE
                
                # Format file size
                size_mb = attachment['size'] / (1024 * 1024)
                size_str = f"{size_mb:.2f} MB" if size_mb >= 1 else f"{attachment['size'] / 1024:.0f} KB"
                
                attachment_control = ft.Container(
                    content=ft.Row([
                        ft.Icon(icon, size=20),
                        ft.Column([
                            ft.Text(attachment['name'], size=12, weight=ft.FontWeight.BOLD),
                            ft.Text(f"{attachment['source']} • {size_str}", size=10, color=ft.colors.GREY_600)
                        ], spacing=2, expand=True),
                        ft.IconButton(
                            ft.icons.CLOSE,
                            tooltip="Remove attachment",
                            icon_size=16,
                            on_click=lambda e, idx=i: self.remove_attachment(idx)
                        )
                    ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    padding=ft.padding.all(5),
                    border=ft.border.all(1, ft.colors.GREY_300),
                    border_radius=5,
                    bgcolor=ft.colors.WHITE
                )
                attachment_controls.append(attachment_control)
            
            self.attachments_container.content = ft.Column(attachment_controls, spacing=5)
        
        self.page.update()

    def remove_attachment(self, index):
        """Remove an attachment"""
        try:
            if 0 <= index < len(self.current_attachments):
                removed = self.current_attachments.pop(index)
                self.update_attachments_display()
                self.show_snack_bar(f"Removed '{removed['name']}'")
        except Exception as e:
            print(f"Error removing attachment: {e}")

    def show_snack_bar(self, message):
        """Show a snack bar with a message"""
        try:
            self.page.show_snack_bar(
                ft.SnackBar(
                    content=ft.Text(message),
                    action="OK"
                )
            )
        except Exception as e:
            print(f"Error showing snack bar: {e}")

    def load_previous_messages(self):
        """Load previous messages from database - FIXED: Handle missing columns"""
        try:
            # Check what columns exist in the messages table
            self.cursor.execute("PRAGMA table_info(messages)")
            columns = [column[1] for column in self.cursor.fetchall()]
            
            # Build query based on available columns
            if 'attachments' in columns and 'attachment_types' in columns:
                query = 'SELECT sender, message, attachments, attachment_types FROM messages ORDER BY timestamp'
                self.cursor.execute(query)
                messages = self.cursor.fetchall()
                
                for sender, message, attachments_data, attachment_types in messages:
                    if sender == "user":
                        self.add_user_message_to_chat(message, attachments_data, attachment_types)
                    else:
                        self.add_bot_message_to_chat(message)
            else:
                # Fallback for older database format
                query = 'SELECT sender, message FROM messages ORDER BY timestamp'
                self.cursor.execute(query)
                messages = self.cursor.fetchall()
                
                for sender, message in messages:
                    if sender == "user":
                        self.add_user_message_to_chat(message)
                    else:
                        self.add_bot_message_to_chat(message)
            
            self.page.update()
            print(f"Loaded {len(messages)} previous messages")
            
        except sqlite3.OperationalError as e:
            print(f"Database error while loading messages: {e}")
        except Exception as e:
            print(f"Unexpected error loading messages: {e}")

    def add_user_message_to_chat(self, message, attachments_data=None, attachment_types=None):
        """Add user message to chat with optional attachments"""
        message_content = [ft.Text(message, selectable=True, size=15, color=ft.colors.BLACK)]
        
        # Add attachment indicators if present
        if attachments_data and attachments_data.strip():
            try:
                # Handle different attachment data formats
                if isinstance(attachments_data, str):
                    if attachments_data.startswith('['):
                        # JSON list format
                        attachments = json.loads(attachments_data)
                    elif attachments_data.startswith("['"):
                        # String representation of list
                        attachments = eval(attachments_data)
                    else:
                        # Single attachment
                        attachments = [attachments_data]
                else:
                    attachments = attachments_data
                
                # Parse attachment types
                types = []
                if attachment_types and attachment_types.strip():
                    if isinstance(attachment_types, str):
                        if attachment_types.startswith('['):
                            types = json.loads(attachment_types)
                        elif attachment_types.startswith("['"):
                            types = eval(attachment_types)
                        else:
                            types = [attachment_types]
                    else:
                        types = attachment_types
                
                # Create attachment display elements
                for i, attachment in enumerate(attachments):
                    att_type = types[i] if i < len(types) else "file"
                    
                    if att_type.startswith('image/'):
                        icon = ft.icons.IMAGE
                        label = "Image"
                    elif att_type == 'application/pdf':
                        icon = ft.icons.PICTURE_AS_PDF
                        label = "PDF"
                    elif 'word' in att_type:
                        icon = ft.icons.DESCRIPTION
                        label = "Document"
                    else:
                        icon = ft.icons.ATTACH_FILE
                        label = "File"
                    
                    message_content.append(
                        ft.Container(
                            content=ft.Row([
                                ft.Icon(icon, size=16),
                                ft.Text(f"{label}: {attachment}", size=12, color=ft.colors.BLUE_800)
                            ], spacing=5),
                            padding=ft.padding.all(5),
                            bgcolor=ft.colors.BLUE_50,
                            border_radius=5,
                            margin=ft.margin.only(top=5)
                        )
                    )
            except Exception as e:
                print(f"Error processing attachments in message display: {e}")
        
        # Add message to chat
        self.chat.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Column(message_content, tight=True),
                    alignment=ft.alignment.center_right,
                    bgcolor=ft.colors.BLUE_100,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    border_radius=ft.border_radius.only(
                        top_left=16, top_right=16, bottom_left=16, bottom_right=4
                    ),
                    margin=ft.margin.only(bottom=6),
                    shadow=ft.BoxShadow(
                        spread_radius=0.5, blur_radius=3,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                        offset=ft.Offset(0, 1.5)
                    ),
                )
            ], alignment=ft.MainAxisAlignment.END)
        )

    def add_bot_message_to_chat(self, message):
        """Add bot message to chat"""
        self.chat.controls.append(
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Text("BOB:", size=15, weight=ft.FontWeight.BOLD, color=ft.colors.BLUE_800),
                        ft.Text(message, selectable=True, size=15, color=ft.colors.BLACK)
                    ], spacing=4, tight=True),
                    alignment=ft.alignment.center_left,
                    bgcolor=ft.colors.GREEN_100,
                    padding=ft.padding.symmetric(horizontal=14, vertical=10),
                    border_radius=ft.border_radius.only(
                        top_left=16, top_right=16, bottom_left=4, bottom_right=16
                    ),
                    margin=ft.margin.only(bottom=6),
                    shadow=ft.BoxShadow(
                        spread_radius=0.5, blur_radius=3,
                        color=ft.colors.with_opacity(0.1, ft.colors.BLACK),
                        offset=ft.Offset(0, 1.5)
                    ),
                )
            ], alignment=ft.MainAxisAlignment.START)
        )

    def store_message(self, sender, message, attachments=None):
        """Store a message in the database with comprehensive error handling"""
        try:
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            attachments_data = ""
            attachment_types = ""
            
            if attachments:
                # Store attachment names and types
                attachment_names = [att['name'] for att in attachments]
                attachment_types_list = [att['type'] for att in attachments]
                attachments_data = json.dumps(attachment_names)
                attachment_types = json.dumps(attachment_types_list)
            
            # Try to insert with all columns
            self.cursor.execute('''
                INSERT INTO messages (sender, message, timestamp, attachments, attachment_types)
                VALUES (?, ?, ?, ?, ?)
            ''', (sender, message, timestamp, attachments_data, attachment_types))
            self.conn.commit()
            
        except sqlite3.OperationalError as e:
            print(f"Error storing message with attachments: {e}")
            # Fallback: try storing without attachment columns
            try:
                self.cursor.execute('''
                    INSERT INTO messages (sender, message, timestamp)
                    VALUES (?, ?, ?)
                ''', (sender, message, timestamp))
                self.conn.commit()
                print("Message stored without attachments data")
            except Exception as e2:
                print(f"Could not store message at all: {e2}")
        except Exception as e:
            print(f"Unexpected error storing message: {e}")

    def init_ui(self):
        """Initialize the user interface"""
        self.page.title = "Bob the Lawyer"
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.padding = 20

        # Main chat area
        main_column = ft.Column(
            expand=True,
            controls=[
                ft.Container(
                    content=ft.Text("Chat with Bob", size=24, weight=ft.FontWeight.BOLD),
                    alignment=ft.alignment.center,
                    padding=ft.padding.only(bottom=10)
                ),
                ft.Divider(),
                self.chat,
                self.attachments_container,
                ft.Row([
                    self.user_input, 
                    self.attachment_button, 
                    self.send_button
                ], spacing=10),
            ],
        )

        # Add main content to page
        self.page.add(main_column)
        self.user_input.focus()

    def send_click(self, e):
        """Handle send button click or enter key press"""
        question = self.user_input.value.strip()
        attachments = self.current_attachments.copy()
        
        if not question and not attachments:
            return

        # If no text but has attachments, provide default message
        if not question and attachments:
            question = "Please analyze the attached file(s)."

        # Store user message in database
        self.store_message("user", question, attachments if attachments else None)

        # Add to chat display
        if attachments:
            attachment_names = json.dumps([att['name'] for att in attachments])
            attachment_types = json.dumps([att['type'] for att in attachments])
            self.add_user_message_to_chat(question, attachment_names, attachment_types)
        else:
            self.add_user_message_to_chat(question)

        # Show thinking indicator
        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Bob is thinking...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
            margin=ft.margin.only(left=10)
        )
        self.chat.controls.append(thinking)
        
        # Disable inputs while processing
        self.user_input.disabled = True
        self.send_button.disabled = True
        self.attachment_button.disabled = True
        self.page.update()

        try:
            # Prepare context with attachments for the AI model
            context = question
            if attachments:
                context += "\n\nAttached files:\n"
                for att in attachments:
                    context += f"- {att['name']} ({att['type']}, {att['size']} bytes)\n"
                    # You can add file content analysis here based on file type
                    
            # Generate reply using the model
            reply = generate_reply(context)
            self.store_message("bot", reply)
            
        except Exception as err:
            reply = f"⚠ Error generating response: {str(err)}"
            self.store_message("system", f"Error: {str(err)}")
            print(f"Error generating reply: {err}")

        # Remove thinking indicator and add reply
        self.chat.controls.remove(thinking)
        self.add_bot_message_to_chat(reply)

        # Clear inputs and re-enable
        self.user_input.value = ""
        self.current_attachments = []
        self.update_attachments_display()
        self.user_input.disabled = False
        self.send_button.disabled = False
        self.attachment_button.disabled = False
        self.page.update()
        self.user_input.focus()

    def _del_(self):
        """Close database connection when the app is closed"""
        try:
            if hasattr(self, 'conn'):
                self.conn.close()
                print("Database connection closed")
        except Exception as e:
            print(f"Error closing database: {e}")


def main(page: ft.Page):
    """Main function to create and run the app"""
    try:
        LawyerChatBotApp(page)
    except Exception as e:
        print(f"Error starting app: {e}")
        page.add(ft.Text(f"Error starting application: {str(e)}"))


if __name__ == "__main__":
    ft.app(target=main)
