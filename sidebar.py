import flet as ft

class ModernNavBar(ft.Container):
    def __init__(self):
        super().__init__(
            alignment=ft.alignment.center,
            padding=10,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            content=ft.Column(
                expand=True,
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.START,
                spacing=5,
                controls=[
                    #self.content(ft.Text("Bob the lawyer", size=16, weight=ft.FontWeight.BOLD)),
                    self.contained_icon(ft.icons.HOME_FILLED, "Home", 1),
                    self.contained_icon(ft.icons.SEARCH, "Search", None),
                    self.contained_icon(ft.icons.DASHBOARD_ROUNDED, "Dashboard", 2),
                    self.contained_icon(ft.icons.BAR_CHART, "Revenue", 3),
                    self.contained_icon(ft.icons.NOTIFICATIONS, "Notifications", None),
                    self.contained_icon(ft.icons.PIE_CHART_ROUNDED, "Analytics", None),
                    self.contained_icon(ft.icons.FAVORITE_ROUNDED, "Likes", None),
                    self.contained_icon(ft.icons.WALLET_ROUNDED, "Wallet", None),
                    ft.Divider(color="black", height=5),
                    self.contained_icon(ft.icons.LOGOUT_ROUNDED, "Logout", None),
                ],
            ),
        )

    def highlight_container(self, e):
        icon_button = e.control.content.controls[0]
        text = e.control.content.controls[1]
        if e.data == "true":
            icon_button.icon_color = "purple300"
            text.color = "purple300"
        else:
            icon_button.icon_color = "black"
            text.color = "black"
        e.control.content.update()

    def contained_icon(self, icon_name, text, data):
        return ft.Container(
            data=data,
            width=180,
            height=45,
            border_radius=10,
            on_hover=self.highlight_container,
            ink=True,
            content=ft.Row(
                controls=[
                    ft.IconButton(
                        icon=icon_name,
                        icon_size=18,
                        icon_color="black",
                        selected=False,
                        style=ft.ButtonStyle(
                            shape={
                                "": ft.RoundedRectangleBorder(radius=7),
                            },
                            overlay_color={"": "transparent"},
                        ),
                    ),
                    ft.Text(
                        value=text,
                        color="black",
                        size=11,
                        opacity=1,
                        animate_opacity=200,
                    ),
                ],
            ),
        )

def render_sidebar():
    return ModernNavBar()
