import flet as ft
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import threading

class LegalAssistantApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self.chat = None
        self.user_input = None
        
        self._setup_page()
        self._show_loading_screen()
        self._load_model_in_background()

    def _setup_page(self):
        """Configure the page settings"""
        self.page.title = "Legal Assistant (Phi-3)"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.window_resizable = True
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO

    def _show_loading_screen(self):
        """Display loading screen while model loads"""
        self.loading_container = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=50, height=50),
                    ft.Text("Loading legal assistant...", size=16),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=20,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
        self.page.add(self.loading_container)
        self.page.update()

    def _load_model_in_background(self):
        """Load model in a background thread to prevent UI freezing"""
        threading.Thread(
            target=self._load_model,
            daemon=True
        ).start()

    def _load_model(self):
        """Load the AI model and tokenizer"""
        try:
            model_path = "C:/Program Files/Bob-the-lawyer-model/phi-3-local"
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )
            
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                max_new_tokens=150,
                temperature=0.7,
                do_sample=True,
                top_k=40,
                top_p=0.9,
                torch_dtype=torch.float16
            )
            
            # Switch to chat UI when model is loaded
            self.page.run_thread(self._setup_chat_ui)
            
        except Exception as e:
            self.page.run_thread(lambda: self._show_error(str(e)))

    def _setup_chat_ui(self):
        """Initialize the chat interface"""
        self.page.controls.clear()
        
        # Initialize chat history
        self.chat = ft.Column(
            expand=True,
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            auto_scroll=True,
        )
        
        # Create input controls
        self._create_input_controls()
        
        # Assemble main layout
        self.page.add(
            ft.Column(
                [
                    self._create_header(),
                    ft.Divider(height=20),
                    ft.Container(
                        content=self.chat,
                        expand=True,
                        padding=ft.padding.symmetric(horizontal=10),
                    ),
                    self._create_input_container(),
                ],
                spacing=15,
                expand=True,
            )
        )
        self.page.update()

    def _create_header(self):
        """Create the app header"""
        return ft.Row(
            [
                ft.Icon(ft.icons.GAVEL, size=28, color=ft.colors.GREEN_700),
                ft.Text("Legal Assistant", size=24, weight="bold"),
            ],
            spacing=10,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _create_input_controls(self):
        """Create user input controls"""
        self.user_input = ft.TextField(
            hint_text="Type your legal question here...",
            expand=True,
            min_lines=1,
            max_lines=5,
            autofocus=True,
            border_radius=15,
            filled=True,
            border_color=ft.colors.TRANSPARENT,
            on_submit=self._on_send_message,
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_size=24,
            tooltip="Send message",
            bgcolor=ft.colors.BLUE_500,
            icon_color=ft.colors.WHITE,
            on_click=self._on_send_message,
        )

    def _create_input_container(self):
        """Create container for input controls"""
        return ft.Container(
            ft.Row(
                [
                    self.user_input,
                    ft.Container(self.send_button, border_radius=15),
                ],
                spacing=10,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor=ft.colors.GREY_100,
            padding=ft.padding.symmetric(horizontal=15, vertical=10),
            border_radius=15,
        )

    def _on_send_message(self, e):
        """Handle sending a message"""
        user_message = self.user_input.value.strip()
        if not user_message:
            return
            
        # Add user message to chat
        self._add_user_message(user_message)
        self.user_input.value = ""
        self.page.update()
        
        # Add thinking indicator
        thinking_indicator = self._create_thinking_indicator()
        self.chat.controls.append(thinking_indicator)
        self.page.update()
        
        # Generate response in background thread
        threading.Thread(
            target=self._generate_response,
            args=(user_message, thinking_indicator),
            daemon=True
        ).start()

    def _add_user_message(self, message):
        """Add a user message to the chat"""
        self.chat.controls.append(
            self._create_message(message, is_user=True)
        )

    def _create_message(self, text, is_user=False):
        """Create a chat message bubble"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.PERSON if is_user else ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_600 if is_user else ft.colors.GREEN_600,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("You" if is_user else "Legal Assistant", 
                                   weight="bold", size=14),
                            ft.Container(
                                content=ft.Markdown(
                                    text,
                                    selectable=True,
                                    extension_set="gitHubWeb",
                                    code_theme="atom-one-dark",
                                ),
                                padding=ft.padding.symmetric(horizontal=8, vertical=6),
                            ),
                        ],
                        spacing=6,
                        tight=True,
                        width=self.page.window_width * 0.7,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
                wrap=True,
            ),
            bgcolor=ft.colors.BLUE_50 if is_user else ft.colors.GREEN_50,
            padding=12,
            border_radius=15,
            border=ft.border.all(1, ft.colors.BLUE_100 if is_user else ft.colors.GREEN_100),
            margin=ft.margin.only(left=80) if is_user else ft.margin.only(right=80),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

    def _create_thinking_indicator(self):
        """Create a 'thinking' indicator for the assistant"""
        return ft.Container(
            content=ft.Row(
                controls=[
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN_600,
                    ),
                    ft.Column(
                        controls=[
                            ft.Text("Legal Assistant", weight="bold", size=14),
                            ft.Row(
                                controls=[
                                    ft.ProgressRing(width=16, height=16, stroke_width=2),
                                    ft.Text("Researching your question..."),
                                ],
                                spacing=8,
                            ),
                        ],
                        spacing=6,
                    ),
                ],
                spacing=12,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=ft.colors.GREEN_50,
            padding=12,
            border_radius=15,
            border=ft.border.all(1, ft.colors.GREEN_100),
            margin=ft.margin.only(right=80),
            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
        )

    def _generate_response(self, user_message, thinking_indicator):
        """Generate response from the AI model"""
        try:
            response = self.pipe(
                f"<|user|>\n{user_message}<|end|>\n<|assistant|>",
                max_length=250,
                pad_token_id=self.tokenizer.eos_token_id
            )[0]['generated_text'].split("<|assistant|>")[-1].strip()
            
            # Update UI with response
            self.page.run_thread(
                lambda: self._update_chat_with_response(thinking_indicator, response)
            )
            
        except Exception as ex:
            self.page.run_thread(
                lambda: self._show_error(f"Error generating response: {str(ex)}")
            )

    def _update_chat_with_response(self, thinking_indicator, response):
        """Replace thinking indicator with actual response"""
        self.chat.controls.remove(thinking_indicator)
        self.chat.controls.append(self._create_message(response))
        self.page.update()

    def _show_error(self, error_msg):
        """Display error message"""
        self.page.controls.clear()
        self.page.add(
            ft.Column(
                [
                    ft.Text("Error", size=24, weight="bold", color=ft.colors.RED),
                    ft.Text(error_msg),
                    ft.ElevatedButton(
                        "Retry",
                        on_click=lambda e: self._retry_loading(),
                        icon=ft.icons.REFRESH,
                    )
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        self.page.update()

    def _retry_loading(self):
        """Retry loading the model"""
        self.page.controls.clear()
        self._show_loading_screen()
        self._load_model_in_background()

def main(page: ft.Page):
    """Entry point that creates the app instance"""
    LegalAssistantApp(page)

ft.app(target=main)