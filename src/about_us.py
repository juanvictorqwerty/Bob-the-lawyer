import flet as ft

def _create_member_card(image_src: str, name: str, role: str, is_dark: bool) -> ft.Card:
    
    return ft.Card(
        color=ft.Colors.GREY_800 if is_dark else ft.colors.WHITE,
        content=ft.Container(
            padding=20,
            content=ft.Column(
                [
                    ft.Image(
                        src=image_src,
                        width=200,
                        height=200,
                        fit=ft.ImageFit.COVER,
                        border_radius=ft.border_radius.all(50),
                    ),
                    ft.Text(name, size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER),
                    ft.Text(role, size=14, text_align=ft.TextAlign.CENTER, italic=True),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=10,
            )
        ),
        width=250,
        elevation=4,
    )

def create_about_us_view(main_app):
    
    is_dark = main_app.page.theme_mode == ft.ThemeMode.DARK

    members_data = [
        {"image": "McBright.jpeg", "name": "PIABEZIH McBright", "role": "Created the API"},
        {"image": "Armel.jpeg", "name": "Armel ANDELA", "role": "Was responsible for the multi-chatting, themes and the website"},
        {"image": "Royce.jpeg", "name": "Royce Stephane MASSIA", "role": "Product owner,was in charge of the design and the Web searching functionality"},
        {"image": "Rejoice.jpeg", "name": "TENGHU Rejoice TEMBUG", "role": "Was in charge of the document import and analysis functionality"},
        {"image": "MIKe.jpg", "name": "MIKE Juan Victor", "role": "Scrum Master was responsible for the finetuning and general fixes"},
    ]

    member_cards = [_create_member_card(m["image"], m["name"], m["role"], is_dark) for m in members_data]

    group_card = ft.Card(
        color=ft.colors.GREY_800 if is_dark else ft.colors.WHITE,
        elevation=4,
        content=ft.Container(
            padding=15,
            content=ft.Column(
                [
                    ft.Text("The team behind Bob the lawyer", theme_style=ft.TextThemeStyle.HEADLINE_SMALL, text_align=ft.TextAlign.CENTER),
                    ft.Image(
                        src="group10.jpeg",
                        fit=ft.ImageFit.CONTAIN,  # Ensures the whole image is visible without cropping
                        border_radius=ft.border_radius.all(8),
                    )
                ],
                spacing=10,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
    )

    about_us_view = ft.Column(
        [
            ft.Row(
                [
                    ft.IconButton(
                        icon=ft.icons.ARROW_BACK,
                        on_click=lambda _: main_app.go_back_to_main(),
                        tooltip="Back to Chat"
                    ),
                    ft.Text("About Our Team", theme_style=ft.TextThemeStyle.HEADLINE_MEDIUM),
                ],
                alignment=ft.MainAxisAlignment.START,
            ),
            group_card, # Add the group card at the top
            ft.Divider(),
            ft.Row(
                controls=member_cards,
                alignment=ft.MainAxisAlignment.CENTER,
                wrap=True,
                spacing=20,
                run_spacing=20,
            )
        ],
        expand=True,
        scroll=ft.ScrollMode.AUTO,
        spacing=20,
    )
    
    return about_us_view