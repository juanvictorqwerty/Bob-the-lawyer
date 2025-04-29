import flet as ft
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline
import torch
import threading
import time

class LegalAssistantApp:
    def __init__(self, page: ft.Page):
        self.page = page
        self.model = None
        self.tokenizer = None
        self.pipe = None
        self.chat_history = []  # Track chat history for context
        
        # Initialize UI immediately
        self._setup_page()
        self._show_loading_screen()
        
        # Load model in background
        self._load_model_in_background()

    def _setup_page(self):
        """Configure the page settings with optimized defaults"""
        self.page.title = "Legal Assistant (Phi-3)"
        self.page.theme_mode = ft.ThemeMode.LIGHT
        self.page.window_width = 900
        self.page.window_height = 700
        self.page.window_resizable = True
        self.page.padding = 20
        self.page.scroll = ft.ScrollMode.AUTO
        self.page.horizontal_alignment = ft.CrossAxisAlignment.CENTER

    def _show_loading_screen(self):
        """Display efficient loading screen"""
        self.loading_container = ft.Container(
            content=ft.Column(
                [
                    ft.ProgressRing(width=30, height=30, stroke_width=2),
                    ft.Text("Loading legal assistant...", size=14),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=15,
                tight=True,
            ),
            expand=True,
            alignment=ft.alignment.center,
        )
        self.page.clean()
        self.page.add(self.loading_container)
        self.page.update()

    def _load_model_in_background(self):
        """Load model in background with progress tracking"""
        def loading_progress():
            dots = 0
            while not hasattr(self, 'pipe') or self.pipe is None:
                time.sleep(0.5)
                dots = (dots + 1) % 4
                self.page.run_thread(
                    lambda: self._update_loading_text(f"Loading legal assistant{'.' * dots}")
                )
        
        # Start model loading and progress tracking
        threading.Thread(target=self._load_model, daemon=True).start()
        threading.Thread(target=loading_progress, daemon=True).start()

    def _update_loading_text(self, text):
        """Update loading text efficiently"""
        if hasattr(self, 'loading_container'):
            self.loading_container.content.controls[1].value = text
            self.loading_container.content.update()

    def _load_model(self):
        """Optimized model loading with fallbacks"""
        try:
            model_path = "C:/Program Files/Bob-the-lawyer-model/phi-3-local"
            
            # Load tokenizer first (faster)
            self.tokenizer = AutoTokenizer.from_pretrained(model_path, trust_remote_code=True)
            
            # Determine device with fallback
            device = 0 if torch.cuda.is_available() else -1
            torch_dtype = torch.float16 if device == 0 else torch.float32
            
            # Load model with optimized settings
            self.model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch_dtype,
                low_cpu_mem_usage=True,
                device_map="auto" if device == 0 else None,
            )
            
            # Create pipeline with optimized generation settings
            self.pipe = pipeline(
                "text-generation",
                model=self.model,
                tokenizer=self.tokenizer,
                device=device,
                torch_dtype=torch_dtype,
            )
            
            # Switch to chat UI
            self.page.run_thread(self._setup_chat_ui)

        except Exception as e:
            self.page.run_thread(lambda: self._show_error(str(e)))

    def _setup_chat_ui(self):
        """Initialize optimized chat interface"""
        self.page.clean()
        
        # Chat history with optimized rendering
        self.chat = ft.ListView(
            expand=True,
            spacing=12,
            auto_scroll=True,
        )
        
        # Input controls
        self._create_input_controls()
        
        # Assemble layout
        self.page.add(
            ft.Column(
                [
                    self._create_header(),
                    ft.Divider(height=10),
                    ft.Container(
                        content=self.chat,
                        expand=True,
                        padding=10,
                    ),
                    self._create_input_container(),
                ],
                spacing=10,
                expand=True,
            )
        )
        self.page.update()

    def _create_header(self):
        """Create lightweight header"""
        return ft.Row(
            [
                ft.Icon(ft.icons.GAVEL, size=24, color=ft.colors.GREEN_700),
                ft.Text("Legal Assistant", size=20, weight="bold"),
            ],
            spacing=8,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    def _create_input_controls(self):
        """Create optimized input controls"""
        self.user_input = ft.TextField(
            hint_text="Type your legal question here...",
            expand=True,
            min_lines=1,
            max_lines=3,
            autofocus=True,
            border_radius=10,
            filled=True,
            border_color=ft.colors.TRANSPARENT,
            on_submit=self._on_send_message,
        )
        
        self.send_button = ft.IconButton(
            icon=ft.icons.SEND_ROUNDED,
            icon_size=20,
            tooltip="Send",
            bgcolor=ft.colors.BLUE_500,
            icon_color=ft.colors.WHITE,
            on_click=self._on_send_message,
        )

    def _create_input_container(self):
        """Create lightweight input container"""
        return ft.Container(
            ft.Row(
                [
                    self.user_input,
                    self.send_button,
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.END,
            ),
            bgcolor=ft.colors.GREY_100,
            padding=10,
            border_radius=10,
        )

    def _on_send_message(self, e):
        """Handle message sending efficiently"""
        user_message = self.user_input.value.strip()
        if not user_message:
            return
            
        # Add user message immediately
        self._add_user_message(user_message)
        self.user_input.value = ""
        self.user_input.focus()
        self.page.update()
        
        # Add thinking indicator
        thinking_indicator = self._create_thinking_indicator()
        self.chat.controls.append(thinking_indicator)
        self.page.update()
        
        # Generate response in background
        threading.Thread(
            target=self._generate_response,
            args=(user_message, thinking_indicator),
            daemon=True
        ).start()

    def _add_user_message(self, message):
        """Add user message with optimized rendering"""
        self.chat_history.append({"role": "user", "content": message})
        self.chat.controls.append(
            self._create_message(message, is_user=True)
        )

    def _create_message(self, text, is_user=False):
        """Create optimized message bubble"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.PERSON if is_user else ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.BLUE_600 if is_user else ft.colors.GREEN_600,
                        radius=16,
                    ),
                    ft.Column(
                        [
                            ft.Text("You" if is_user else "Legal Assistant", 
                                   weight="bold", size=12),
                            ft.Markdown(
                                text,
                                selectable=True,
                                extension_set=ft.MarkdownExtensionSet.NONE,  # Lightweight
                            ),
                        ],
                        spacing=4,
                        tight=True,
                    ),
                ],
                spacing=8,
                vertical_alignment=ft.CrossAxisAlignment.START,
            ),
            bgcolor=ft.colors.BLUE_50 if is_user else ft.colors.GREEN_50,
            padding=10,
            border_radius=12,
            margin=ft.margin.only(left=60) if is_user else ft.margin.only(right=60),
        )

    def _create_thinking_indicator(self):
        """Lightweight thinking indicator"""
        return ft.Container(
            content=ft.Row(
                [
                    ft.CircleAvatar(
                        content=ft.Icon(ft.icons.GAVEL),
                        color=ft.colors.WHITE,
                        bgcolor=ft.colors.GREEN_600,
                        radius=16,
                    ),
                    ft.Column(
                        [
                            ft.Text("Legal Assistant", weight="bold", size=12),
                            ft.Row(
                                [
                                    ft.ProgressRing(width=14, height=14, stroke_width=2),
                                    ft.Text("Researching...", size=12),
                                ],
                                spacing=6,
                            ),
                        ],
                        spacing=4,
                    ),
                ],
                spacing=8,
            ),
            bgcolor=ft.colors.GREEN_50,
            padding=10,
            border_radius=12,
            margin=ft.margin.only(right=60),
        )

    def _generate_response(self, user_message, thinking_indicator):
        """Generate response with optimized settings"""
        try:
            # Use chat history for context
            prompt = "\n".join([f"<|{msg['role']}|>\n{msg['content']}<|end|>" 
                              for msg in self.chat_history[-6:]]) + "\n<|assistant|>"
            
            # Generate with optimized parameters
            response = self.pipe(
                prompt,
                max_new_tokens=256,
                temperature=0.7,
                top_p=0.9,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id
            )[0]['generated_text'].split("<|assistant|>")[-1].strip()
            
            # Update UI
            self.page.run_thread(
                lambda: self._update_chat_with_response(thinking_indicator, response)
            )
            
        except Exception as ex:
            self.page.run_thread(
                lambda: self._show_error(f"Error: {str(ex)}")
            )

    def _update_chat_with_response(self, thinking_indicator, response):
        """Efficiently update chat with response"""
        self.chat.controls.remove(thinking_indicator)
        self.chat_history.append({"role": "assistant", "content": response})
        self.chat.controls.append(self._create_message(response))
        self.page.update()

    def _show_error(self, error_msg):
        """Efficient error display"""
        self.page.clean()
        self.page.add(
            ft.Column(
                [
                    ft.Text("Error", size=20, color=ft.colors.RED),
                    ft.Text(error_msg, size=12),
                    ft.FilledButton(
                        "Retry",
                        on_click=lambda e: self._retry_loading(),
                        icon=ft.icons.REFRESH,
                        height=40,
                    )
                ],
                spacing=12,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        self.page.update()

    def _retry_loading(self):
        """Efficient retry"""
        self.page.clean()
        self._show_loading_screen()
        self._load_model_in_background()

def main(page: ft.Page):
    """Optimized app entry point"""
    LegalAssistantApp(page)

if __name__ == "__main__":
    ft.app(target=main)  