import flet as ft
import sqlite3
from datetime import datetime
import os
import base64
import mimetypes
from model_handler import generate_reply
from sidebar import render_sidebar  # Optional sidebar module if you use one

class LawyerChatBotApp:
    def _init_(self, page: ft.Page):
        self.page = page
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.chat = ft.ListView(expand=True, spacing=10, auto_scroll=True)
        self.sidebar = render_sidebar() if 'render_sidebar' in globals() else ft.Container()
        
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
        
        # Attachment button with dropdown menu
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
        
        # Container to show attached files
        self.attachments_container = ft.Container(
            content=ft.Column([], spacing=5),
            visible=False,
            padding=ft.padding.all(10),
            bgcolor=ft.colors.GREY_100,
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
        """Create database and table if they don't exist"""
        self.conn = sqlite3.connect('database.db')
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp DATETIME NOT NULL,
                attachments TEXT,
                attachment_types TEXT
            )
        ''')
        self.conn.commit()

    def take_photo(self, e):
        """Handle camera capture"""
        # Note: Flet's camera support is limited. This will open file picker 
        # which may show camera option on mobile devices
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
        """Handle uploaded file"""
        try:
            # Read file content
            file_path = file.path
            file_name = file.name
            file_size = file.size if hasattr(file, 'size') else os.path.getsize(file_path)
            
            # Check file size (limit to 10MB)
            if file_size > 10 * 1024 * 1024:
                self.show_snack_bar("File too large. Maximum size is 10MB.")
                return
            
            # Determine file type
            mime_type, _ = mimetypes.guess_type(file_path)
            file_extension = os.path.splitext(file_name)[1].lower()
            
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

    def update_attachments_display(self):
        """Update the display of current attachments"""
        if not self.current_attachments:
            self.attachments_container.visible = False
        else:
            self.attachments_container.visible = True
            attachment_controls = []
            
            for i, attachment in enumerate(self.current_attachments):
                # Determine icon based on file type
                if attachment['type'].startswith('image/'):
                    icon = ft.icons.IMAGE
                elif attachment['type'] == 'application/pdf':
                    icon = ft.icons.PICTURE_AS_PDF
                elif 'word' in attachment['type'] or attachment['name'].endswith(('.doc', '.docx')):
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
        if 0 <= index < len(self.current_attachments):
            removed = self.current_attachments.pop(index)
            self.update_attachments_display()
            self.show_snack_bar(f"Removed '{removed['name']}'")

    def show_snack_bar(self, message):
        """Show a snack bar with a message"""
        self.page.show_snack_bar(
            ft.SnackBar(
                content=ft.Text(message),
                action="OK"
            )
        )

    def load_previous_messages(self):
        """Load previous messages from database when app starts"""
        self.cursor.execute('SELECT sender, message, attachments, attachment_types FROM messages ORDER BY timestamp')
        messages = self.cursor.fetchall()
        
        for sender, message, attachments_data, attachment_types in messages:
            if sender == "user":
                self.add_user_message_to_chat(message, attachments_data, attachment_types)
            else:  # bot or system messages
                self.add_bot_message_to_chat(message)
        self.page.update()

    def add_user_message_to_chat(self, message, attachments_data=None, attachment_types=None):
        """Add user message to chat with optional attachments"""
        message_content = [ft.Text(message, selectable=True, size=15, color=ft.colors.BLACK)]
        
        # Add attachment indicators if present
        if attachments_data:
            try:
                import json
                attachments = json.loads(attachments_data)
                types = json.loads(attachment_types) if attachment_types else []
                
                for i, attachment in enumerate(attachments):
                    att_type = types[i] if i < len(types) else "file"
                    if att_type.startswith('image/'):
                        icon = ft.icons.IMAGE
                        label = "Image"
                    elif att_type == 'application/pdf':
                        icon = ft.icons.PICTURE_AS_PDF
                        label = "PDF"
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
            except:
                pass  # Ignore JSON parsing errors for old messages
        
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
        """Store a message in the database with optional attachments"""
        import json
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        attachments_data = None
        attachment_types = None
        
        if attachments:
            # Store only attachment names and types (not the full content for chat display)
            attachment_names = [att['name'] for att in attachments]
            attachment_types_list = [att['type'] for att in attachments]
            attachments_data = json.dumps(attachment_names)
            attachment_types = json.dumps(attachment_types_list)
        
        self.cursor.execute('''
            INSERT INTO messages (sender, message, timestamp, attachments, attachment_types)
            VALUES (?, ?, ?, ?, ?)
        ''', (sender, message, timestamp, attachments_data, attachment_types))
        self.conn.commit()

    def init_ui(self):
        self.page.title = "Bob the Lawyer"
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.padding = 20

        main_column = ft.Column(
            expand=True,
            controls=[
                ft.Text("Chat with Bob", size=24, weight=ft.FontWeight.BOLD),
                ft.Divider(),
                self.chat,
                self.attachments_container,
                ft.Row([self.user_input, self.attachment_button, self.send_button], spacing=10),
            ],
        )

        content = ft.Row(
            controls=[
                self.sidebar,
                ft.Container(width=1, bgcolor=ft.colors.GREY_300),
                main_column,
            ],
            expand=True,
        )

        self.page.add(content)
        self.user_input.focus()

    def send_click(self, e):
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
        self.add_user_message_to_chat(
            question, 
            attachments_data=None if not attachments else str([att['name'] for att in attachments]),
            attachment_types=None if not attachments else str([att['type'] for att in attachments])
        )

        # Show thinking indicator
        thinking = ft.Container(
            ft.Row([
                ft.ProgressRing(width=20, height=20, stroke_width=2),
                ft.Text("Thinking...")
            ], spacing=10),
            alignment=ft.alignment.center_left,
        )
        self.chat.controls.append(thinking)
        
        # Disable inputs
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
                    
            reply = generate_reply(context)
            self.store_message("bot", reply)
        except Exception as err:
            reply = f"⚠ Error: {str(err)}"
            self.store_message("system", f"Error: {str(err)}")

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
        if hasattr(self, 'conn'):
            self.conn.close()


def main(page: ft.Page):
    LawyerChatBotApp(page)

if __name__ == "__main__":
    ft.app(target=main)
