import flet as ft
import asyncio
from typing import Callable, Optional

class ModernNavBar(ft.Container):
    def _init_(self, on_navigation: Optional[Callable] = None):
        self.active_index = 1  # Default to Chat
        self.on_navigation = on_navigation
        
        super()._init_(
            alignment=ft.alignment.center,
            padding=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            bgcolor=ft.colors.GREY_50,
            border=ft.border.all(1, ft.colors.GREY_200),
            border_radius=15,
            shadow=ft.BoxShadow(
                spread_radius=1,
                blur_radius=10,
                color=ft.colors.GREY_300,
                offset=ft.Offset(0, 2),
            ),
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.START,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=5,
                controls=[
                    # Header
                    ft.Container(
                        padding=ft.padding.only(bottom=15, top=5),
                        content=ft.Column(
                            controls=[
                                ft.Text(
                                    "Bob the Lawyer", 
                                    size=18, 
                                    weight=ft.FontWeight.BOLD,
                                    color="purple700"
                                ),
                                ft.Text(
                                    "AI Legal Assistant", 
                                    size=12, 
                                    color="grey600",
                                    italic=True
                                ),
                            ]
                        )
                    ),
                    
                    # Main navigation
                    ft.Container(
                        content=ft.Text("MAIN", size=10, weight=ft.FontWeight.BOLD, color="grey500"),
                        padding=ft.padding.only(left=10, top=10, bottom=5)
                    ),
                    self.contained_icon(ft.icons.CHAT_BUBBLE, "Chat", 1),
                    self.contained_icon(ft.icons.HISTORY, "Chat History", 2),
                    
                    # Document handling
                    ft.Container(
                        content=ft.Text("DOCUMENTS", size=10, weight=ft.FontWeight.BOLD, color="grey500"),
                        padding=ft.padding.only(left=10, top=15, bottom=5)
                    ),
                    self.contained_icon(ft.icons.UPLOAD_FILE, "Upload Files", 3),
                    self.contained_icon(ft.icons.DESCRIPTION, "My Documents", 4),
                    self.contained_icon(ft.icons.PDF_BOX, "PDF Viewer", 5),
                    
                    # Image and camera
                    ft.Container(
                        content=ft.Text("CAPTURE", size=10, weight=ft.FontWeight.BOLD, color="grey500"),
                        padding=ft.padding.only(left=10, top=15, bottom=5)
                    ),
                    self.contained_icon(ft.icons.CAMERA_ALT, "Scan Document", 6),
                    self.contained_icon(ft.icons.PHOTO_LIBRARY, "Image Gallery", 7),
                    self.contained_icon(ft.icons.SCANNER, "OCR Scanner", 8),
                    
                    # Tools and settings
                    ft.Container(
                        content=ft.Text("TOOLS", size=10, weight=ft.FontWeight.BOLD, color="grey500"),
                        padding=ft.padding.only(left=10, top=15, bottom=5)
                    ),
                    self.contained_icon(ft.icons.ANALYTICS, "Document Analytics", 9),
                    self.contained_icon(ft.icons.SEARCH, "Legal Search", 10),
                    self.contained_icon(ft.icons.BOOKMARK, "Legal Resources", 11),
                    
                    # Spacer to push bottom items down
                    ft.Container(expand=True),
                    
                    # Bottom section
                    ft.Divider(color="grey300", height=1),
                    self.contained_icon(ft.icons.SETTINGS, "Settings", 12),
                    self.contained_icon(ft.icons.HELP_OUTLINE, "Help & Support", 13),
                    self.contained_icon(ft.icons.LOGOUT_ROUNDED, "Logout", 14),
                ],
            ),
        )

    def highlight_container(self, e):
        """Handle hover effects"""
        icon_button = e.control.content.controls[0]
        text = e.control.content.controls[1]
        
        # Don't change color if this is the active item
        if e.control.data == self.active_index:
            return
            
        if e.data == "true":
            e.control.bgcolor = "purple50"
            icon_button.icon_color = "purple400"
            text.color = "purple400"
        else:
            e.control.bgcolor = "transparent"
            icon_button.icon_color = "black"
            text.color = "black"
        e.control.update()

    def handle_navigation(self, e):
        """Handle navigation clicks"""
        old_active = self.active_index
        new_active = e.control.data
        
        if new_active is None:
            return
            
        # Update active state
        self.active_index = new_active
        
        # Update all navigation items
        self.update_navigation_states()
        
        # Call the navigation callback
        if self.on_navigation:
            self.on_navigation(new_active, old_active)

    def update_navigation_states(self):
        """Update visual states of all navigation items"""
        def update_item(container):
            if hasattr(container, 'data') and container.data is not None:
                is_active = container.data == self.active_index
                icon_button = container.content.controls[0]
                text = container.content.controls[1]
                
                if is_active:
                    container.bgcolor = "purple100"
                    icon_button.icon_color = "purple700"
                    text.color = "purple700"
                    text.weight = ft.FontWeight.BOLD
                else:
                    container.bgcolor = "transparent"
                    icon_button.icon_color = "black"
                    text.color = "black"
                    text.weight = ft.FontWeight.NORMAL
                container.update()
        
        # Recursively update all containers
        def traverse_controls(controls):
            for control in controls:
                if isinstance(control, ft.Container) and hasattr(control, 'data'):
                    update_item(control)
                elif hasattr(control, 'controls'):
                    traverse_controls(control.controls)
                elif hasattr(control, 'content') and hasattr(control.content, 'controls'):
                    traverse_controls(control.content.controls)
        
        traverse_controls([self])

    def contained_icon(self, icon_name, text, data):
        """Create a navigation item with icon and text"""
        is_active = data == self.active_index
        
        container = ft.Container(
            data=data,
            width=200,
            height=45,
            border_radius=10,
            bgcolor="purple100" if is_active else "transparent",
            on_hover=self.highlight_container,
            on_click=self.handle_navigation,
            ink=True,
            animate=ft.animation.Animation(200, "easeInOut"),
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=icon_name,
                        icon_size=18,
                        icon_color="purple700" if is_active else "black",
                        selected=False,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=7),
                            overlay_color="transparent",
                        ),
                    ),
                    ft.Text(
                        value=text,
                        color="purple700" if is_active else "black",
                        size=12,
                        weight=ft.FontWeight.BOLD if is_active else ft.FontWeight.NORMAL,
                        opacity=1,
                        animate_opacity=200,
                    ),
                ],
            ),
        )
        return container

    def set_active_page(self, page_index: int):
        """Programmatically set the active page"""
        self.active_index = page_index
        self.update_navigation_states()

class FileUploadHandler:
    """Handle different types of file uploads"""
    
    @staticmethod
    def create_file_picker(on_result: Callable):
        """Create file picker for document uploads"""
        return ft.FilePicker(
            on_result=on_result,
        )
    
    @staticmethod
    def create_camera_capture():
        """Create camera capture interface"""
        return ft.Container(
            content=ft.Column(
                controls=[
                    ft.Text("Camera Capture", size=20, weight=ft.FontWeight.BOLD),
                    ft.Container(
                        width=400,
                        height=300,
                        bgcolor="grey200",
                        border_radius=10,
                        content=ft.Column(
                            alignment=ft.MainAxisAlignment.CENTER,
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            controls=[
                                ft.Icon(ft.icons.CAMERA_ALT, size=60, color="grey600"),
                                ft.Text("Camera feed will appear here", color="grey600"),
                            ]
                        )
                    ),
                    ft.Row(
                        alignment=ft.MainAxisAlignment.CENTER,
                        controls=[
                            ft.ElevatedButton(
                                "Capture",
                                icon=ft.icons.CAMERA,
                                on_click=lambda e: print("Capture clicked")
                            ),
                            ft.ElevatedButton(
                                "Upload Image",
                                icon=ft.icons.UPLOAD,
                                on_click=lambda e: print("Upload clicked")
                            ),
                        ]
                    )
                ]
            ),
            padding=20
        )

def render_sidebar(on_navigation: Optional[Callable] = None):
    """Render the enhanced sidebar with file and camera support"""
    return ModernNavBar(on_navigation=on_navigation)

# Example navigation handler
def handle_navigation(page_index: int, previous_index: int):
    """Example navigation handler"""
    navigation_map = {
        1: "Chat",
        2: "Chat History", 
        3: "Upload Files",
        4: "My Documents",
        5: "PDF Viewer",
        6: "Scan Document",
        7: "Image Gallery",
        8: "OCR Scanner",
        9: "Document Analytics",
        10: "Legal Search",
        11: "Legal Resources",
        12: "Settings",
        13: "Help & Support",
        14: "Logout"
    }
    
    print(f"Navigated from '{navigation_map.get(previous_index, 'Unknown')}' to '{navigation_map.get(page_index, 'Unknown')}'")

# Example usage in main app
def create_main_layout(page: ft.Page):
    """Create the main application layout"""
    
    # File picker for document uploads
    file_picker = FileUploadHandler.create_file_picker(
        on_result=lambda e: print(f"Files selected: {[f.name for f in e.files] if e.files else 'None'}")
    )
    
    # Add file picker to page overlay
    page.overlay.append(file_picker)
    
    # Create sidebar with navigation handler
    sidebar = render_sidebar(on_navigation=handle_navigation)
    
    # Main content area that changes based on navigation
    main_content = ft.Container(
        expand=True,
        padding=20,
        content=ft.Column(
            controls=[
                ft.Text("Legal AI Assistant", size=24, weight=ft.FontWeight.BOLD),
                ft.Text("Select an option from the sidebar to get started", size=16, color="grey600"),
                
                # Quick action buttons
                ft.Row(
                    spacing=10,
                    controls=[
                        ft.ElevatedButton(
                            "Upload Document",
                            icon=ft.icons.UPLOAD_FILE,
                            on_click=lambda e: file_picker.pick_files(
                                allow_multiple=True,
                                allowed_extensions=["pdf", "docx", "txt", "jpg", "png"]
                            )
                        ),
                        ft.ElevatedButton(
                            "Scan Document",
                            icon=ft.icons.CAMERA_ALT,
                            on_click=lambda e: print("Camera capture")
                        ),
                        ft.ElevatedButton(
                            "Start Chat",
                            icon=ft.icons.CHAT,
                            on_click=lambda e: print("Start chat")
                        ),
                    ]
                ),
                
                # Camera capture interface (can be shown/hidden based on navigation)
                FileUploadHandler.create_camera_capture(),
            ]
        )
    )
    
    # Layout with sidebar and main content
    return ft.Row(
        controls=[
            ft.Container(
                width=220,
                content=sidebar,
                padding=ft.padding.only(right=10)
            ),
            ft.VerticalDivider(width=1, color="grey300"),
            main_content,
        ],
        expand=True,
    )

# Example main function
def main(page: ft.Page):
    page.title = "Bob the Lawyer - AI Legal Assistant"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.spacing = 0
    
    # Set up the main layout
    layout = create_main_layout(page)
    page.add(layout)
    
    page.update()

# Uncomment to run
# ft.app(target=main)
