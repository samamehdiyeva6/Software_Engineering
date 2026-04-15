import flet as ft

from database import (
    authenticate_user,
    create_project,
    create_user,
    delete_project,
    get_project_for_owner,
    get_projects_for_user,
    init_db,
    is_valid_email_format,
    update_project,
)

ft.icons = ft.Icons

PRIMARY = "#3B82F6"
PRIMARY_DARK = "#2563EB"
BG = "#F6F8FB"
CARD = "#FFFFFF"
TEXT = "#0F172A"
MUTED = "#64748B"
BORDER = "#E2E8F0"
SUCCESS = "#16A34A"
WARNING = "#F59E0B"
DANGER = "#EF4444"
INFO = "#38BDF8"
CENTER = ft.alignment.Alignment(0, 0)
CENTER_LEFT = ft.alignment.Alignment(-1, 0)
CENTER_RIGHT = ft.alignment.Alignment(1, 0)

AUTH_LABEL_STYLE = ft.TextStyle(size=14, weight=ft.FontWeight.W_600, color=TEXT)
AUTH_HINT_STYLE = ft.TextStyle(size=14, color=MUTED)


# ─── SnackBar helper ────────────────────────────────────────────────────────
def show_snack(page, message: str, kind: str = "info"):
    """kind: 'success' | 'error' | 'warning' | 'info'"""
    color_map = {
        "success": SUCCESS,
        "error": DANGER,
        "warning": WARNING,
        "info": PRIMARY,
    }
    icon_map = {
        "success": ft.Icons.CHECK_CIRCLE_OUTLINE,
        "error": ft.Icons.ERROR_OUTLINE,
        "warning": ft.Icons.WARNING_AMBER_OUTLINED,
        "info": ft.Icons.INFO_OUTLINE,
    }
    bgcolor = color_map.get(kind, PRIMARY)
    icon = icon_map.get(kind, ft.Icons.INFO_OUTLINE)

    snack = ft.SnackBar(
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(icon, color="white", size=18),
                ft.Text(message, color="white", size=13),
            ],
        ),
        bgcolor=bgcolor,
        duration=3000,
        show_close_icon=True,
        close_icon_color="white",
    )
    page.overlay.append(snack)
    snack.open = True
    page.update()


# ─── BottomSheet helper ──────────────────────────────────────────────────────
def show_bottom_sheet(page, title: str, content_controls: list, on_close=None):
    """Display a modal bottom sheet with given content."""

    bs = ft.BottomSheet(
        open=True,
        content=ft.Container(
            padding=ft.padding.only(left=24, right=24, top=8, bottom=32),
            bgcolor=CARD,
            content=ft.Column(
                tight=True,
                spacing=16,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text(title, size=16, weight=ft.FontWeight.W_700, color=TEXT),
                            ft.IconButton(
                                icon=ft.Icons.CLOSE,
                                icon_color=MUTED,
                                icon_size=18,
                                on_click=lambda e: _close_bs(page, bs, on_close),
                            ),
                        ],
                    ),
                    ft.Divider(height=1, color=BORDER),
                    *content_controls,
                ],
            ),
        ),
    )

    page.overlay.append(bs)
    page.update()
    return bs


def _close_bs(page, bs, on_close=None):
    bs.open = False
    page.update()
    if on_close:
        on_close()


def auth_text_field(**kwargs):
    defaults = {
        "height": 52,
        "text_size": 15,
        "border_radius": 10,
        "border_color": BORDER,
        "focused_border_color": PRIMARY,
        "label_style": AUTH_LABEL_STYLE,
        "hint_style": AUTH_HINT_STYLE,
        "content_padding": ft.padding.symmetric(horizontal=14, vertical=12),
    }
    defaults.update(kwargs)
    return ft.TextField(**defaults)


def session_user(page):
    store = page.session.store
    name = store.get("user_name") or "User"
    role_key = store.get("user_role") or "customer"
    role_label = "Freelance Worker" if role_key == "worker" else "Customer"
    return (name, role_label)


def set_session_from_user(page, row: dict) -> None:
    s = page.session.store
    s.set("user_id", row["id"])
    s.set("user_email", row["email"])
    s.set("user_name", row["full_name"])
    s.set("user_role", row["role"])


def _logout_session(page):
    page.session.store.clear()
    page.go("/")


PUBLIC_ROUTES = frozenset({"/", "/register"})


def route_query_int(page, key: str = "id") -> int | None:
    import urllib.parse
    if not page.route or "?" not in page.route:
        return None
    try:
        qs = urllib.parse.parse_qs(urllib.parse.urlparse(page.route).query)
        v = qs.get(key)
        if not v or not v[0].strip():
            return None
        return int(v[0].strip())
    except (ValueError, TypeError):
        return None


def _confirm_delete_project(page, project_id: int, user_id: int):
    def close_dlg(_):
        dlg.open = False
        page.update()

    def do_delete(_):
        ok, msg = delete_project(project_id, user_id)
        dlg.open = False
        page.update()
        if ok:
            if page.route and page.route.startswith("/projects"):
                router(page)
            else:
                page.go("/projects")
        else:
            snack = ft.SnackBar(ft.Text(msg or "Could not delete project."), bgcolor=DANGER)
            page.overlay.append(snack)
            snack.open = True
            page.update()

    dlg = ft.AlertDialog(
        modal=True,
        title=ft.Text("Delete project?"),
        content=ft.Text("This will remove the project and related draft records. This cannot be undone."),
        actions=[
            ft.TextButton("Cancel", on_click=close_dlg),
            ft.TextButton("Delete", on_click=do_delete, style=ft.ButtonStyle(color=DANGER)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def pill(text, color=PRIMARY, bg="#E8F0FF"):
    return ft.Container(
        content=ft.Text(text, size=11, color=color, weight=ft.FontWeight.W_600),
        bgcolor=bg,
        border_radius=20,
        padding=ft.padding.symmetric(horizontal=10, vertical=4),
    )


def stat_card(title, value, subtitle=None, icon=ft.icons.SHIELD_OUTLINED, accent=PRIMARY):
    return ft.Container(
        bgcolor=CARD,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        padding=16,
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text(title, size=12, color=MUTED),
                        ft.Container(
                            width=30,
                            height=30,
                            border_radius=8,
                            bgcolor=f"{accent}20",
                            content=ft.Icon(icon, color=accent, size=16),
                            alignment=CENTER,
                        ),
                    ],
                ),
                ft.Text(value, size=20, weight=ft.FontWeight.W_700, color=TEXT),
                ft.Text(subtitle or "", size=11, color=MUTED),
            ],
        ),
    )


def legal_links():
    return ft.Row(
        spacing=20,
        controls=[
            ft.Text("Terms of Service", size=10, color=MUTED),
            ft.Text("Privacy Policy", size=10, color=MUTED),
            ft.Text("Security", size=10, color=MUTED),
        ],
    )


def desktop_footer():
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text("© 2024 EscrowFlow. All rights reserved.", size=10, color=MUTED),
            legal_links(),
        ],
    )


def marketing_footer():
    feature = lambda icon, text: ft.Row(
        spacing=6,
        controls=[
            ft.Icon(icon, size=14, color="#94A3B8"),
            ft.Text(text, size=10, color="#94A3B8", weight=ft.FontWeight.W_600),
        ],
    )

    return ft.Column(
        spacing=22,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=26,
                controls=[
                    feature(ft.icons.VERIFIED_USER_OUTLINED, "AES-256 SECURED"),
                    feature(ft.icons.WORKSPACE_PREMIUM_OUTLINED, "VERIFIED WORKERS"),
                    feature(ft.icons.GROUP_OUTLINED, "10K+ CUSTOMERS"),
                ],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("© 2024 EscrowFlow. All rights reserved.", size=10, color=MUTED),
                    legal_links(),
                ],
            ),
        ],
    )


def top_bar(user="Alex Johnson", role="customer"):
    search = ft.TextField(
        hint_text="Search projects, contracts...",
        prefix_icon=ft.icons.SEARCH,
        height=40,
        border_radius=10,
        border_color=BORDER,
        text_size=12,
        expand=True,
    )
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Container(expand=True, content=search),
            ft.Row(
                spacing=12,
                controls=[
                    ft.Icon(ft.icons.NOTIFICATIONS_OUTLINED, color=MUTED),
                    ft.Container(
                        padding=8,
                        border_radius=20,
                        bgcolor="#EEF2FF",
                        content=ft.Row(
                            spacing=8,
                            controls=[
                                ft.CircleAvatar(
                                    radius=14,
                                    bgcolor=PRIMARY,
                                    content=ft.Text(user[:1], color="white"),
                                ),
                                ft.Column(
                                    spacing=0,
                                    controls=[
                                        ft.Text(user, size=12, weight=ft.FontWeight.W_600),
                                        ft.Text(role, size=10, color=MUTED),
                                    ],
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )


def nav_item(page, label, icon, route, active=False):
    return ft.Container(
        padding=ft.padding.symmetric(horizontal=12, vertical=10),
        border_radius=10,
        bgcolor="#EEF2FF" if active else None,
        on_click=lambda e: page.go(route),
        content=ft.Row(
            spacing=10,
            controls=[
                ft.Icon(icon, color=PRIMARY if active else MUTED, size=18),
                ft.Text(label, size=12, color=TEXT if active else MUTED),
            ],
        ),
    )


def sidebar(page, active_route, items):
    top_controls = [
        ft.Row(
            spacing=8,
            controls=[
                ft.Container(
                    width=28,
                    height=28,
                    border_radius=8,
                    bgcolor=PRIMARY,
                    content=ft.Icon(ft.icons.SHIELD_ROUNDED, color="white", size=16),
                    alignment=CENTER,
                ),
                ft.Text("EscrowFlow", size=14, weight=ft.FontWeight.W_700, color=PRIMARY),
            ],
        ),
        ft.Divider(height=16, color="transparent"),
    ]
    for label, icon, route in items:
        top_controls.append(nav_item(page, label, icon, route, active=route == active_route))
    return ft.Container(
        width=220,
        padding=16,
        border=ft.border.only(right=ft.BorderSide(1, BORDER)),
        content=ft.Column(
            expand=True,
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(spacing=6, controls=top_controls),
                ft.Container(
                    padding=ft.padding.symmetric(horizontal=12, vertical=10),
                    border_radius=10,
                    on_click=lambda e: _logout_session(page),
                    content=ft.Row(
                        spacing=10,
                        controls=[
                            ft.Icon(ft.icons.LOGOUT, color=DANGER, size=18),
                            ft.Text("Logout", size=12, color=DANGER),
                        ],
                    ),
                ),
            ],
        ),
        bgcolor="#FAFBFF",
    )


def shell(page, content, active_route, nav_items, user, role):
    return ft.Container(
        expand=True,
        bgcolor=BG,
        content=ft.Row(
            spacing=0,
            controls=[
                sidebar(page, active_route, nav_items),
                ft.Container(
                    expand=True,
                    padding=20,
                    content=ft.Column(
                        expand=True,
                        spacing=18,
                        controls=[
                            top_bar(user=user, role=role),
                            ft.Container(expand=True, content=content),
                            ft.Divider(height=1, color=BORDER),
                            desktop_footer(),
                        ],
                    ),
                ),
            ],
        ),
    )


def auth_layout(title, subtitle, card_content, page, topbar=False):
    header = (
        ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(
                    spacing=8,
                    controls=[
                        ft.Container(
                            width=34,
                            height=34,
                            border_radius=10,
                            bgcolor=PRIMARY,
                            content=ft.Icon(ft.icons.SHIELD_ROUNDED, color="white", size=18),
                            alignment=CENTER,
                        ),
                        ft.Text("EscrowFlow", size=18, weight=ft.FontWeight.W_700, color=PRIMARY),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.TextButton("Log in", on_click=lambda e: page.go("/")),
                        ft.ElevatedButton("Get Started", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/register")),
                    ],
                ),
            ],
        )
        if topbar
        else ft.Row(
            alignment=ft.MainAxisAlignment.CENTER,
            controls=[
                ft.Container(
                    width=36,
                    height=36,
                    border_radius=10,
                    bgcolor=PRIMARY,
                    content=ft.Icon(ft.icons.SHIELD_ROUNDED, color="white", size=18),
                    alignment=CENTER,
                ),
                ft.Text("EscrowFlow", size=18, weight=ft.FontWeight.W_700, color=PRIMARY),
            ],
        )
    )

    return ft.Container(
        expand=True,
        bgcolor="#F3F6FB",
        padding=40,
        content=ft.Column(
            spacing=36,
            controls=[
                header,
                ft.Container(
                    expand=True,
                    alignment=CENTER,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=18,
                        controls=[
                            ft.Text(title, size=24, weight=ft.FontWeight.W_700, color=TEXT),
                            ft.Text(subtitle, size=14, color=MUTED, text_align=ft.TextAlign.CENTER),
                            ft.Container(
                                width=460,
                                padding=24,
                                border_radius=16,
                                bgcolor=CARD,
                                border=ft.border.all(1, BORDER),
                                content=card_content,
                            ),
                        ],
                    ),
                ),
                marketing_footer(),
            ],
        ),
    )


def view_login(page):
    email_field = auth_text_field(
        label="Email address",
        hint_text="name@example.com",
        prefix_icon=ft.icons.MAIL_OUTLINED,
        expand=True,
    )
    password_field = auth_text_field(
        password=True,
        can_reveal_password=True,
        expand=True,
    )
    err = ft.Text("", color=DANGER, size=13)

    def submit(_):
        err.value = ""
        raw_email = email_field.value or ""
        if not raw_email.strip():
            err.value = "Please enter your email address."
            page.update()
            return
        if not is_valid_email_format(raw_email):
            err.value = (
                "Invalid email: there must be exactly one @ between your name and the domain "
                "(example: name@gmail.com). If @ does not work, check that you use the usual @ key, not a similar symbol."
            )
            page.update()
            return
        row = authenticate_user(raw_email, password_field.value)
        if not row:
            err.value = "Invalid email or password."
            page.update()
            return
        set_session_from_user(page, row)
        page.go("/dashboard")

    card = ft.Column(
        spacing=16,
        controls=[
            err,
            email_field,
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("Password", size=14, weight=ft.FontWeight.W_600, color=TEXT),
                    ft.TextButton("Forgot password?", on_click=lambda e: None),
                ],
            ),
            password_field,
            ft.Row(
                spacing=8,
                controls=[ft.Checkbox(), ft.Text("Keep me signed in", size=13, color=MUTED)],
            ),
            ft.ElevatedButton(
                "Sign In",
                bgcolor=PRIMARY,
                color="white",
                height=48,
                width=412,
                on_click=submit,
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[ft.Text("OR CONTINUE WITH", size=11, color=MUTED, weight=ft.FontWeight.W_600)],
            ),
            ft.Row(
                spacing=12,
                controls=[
                    ft.OutlinedButton("Google", icon=ft.icons.G_TRANSLATE),
                    ft.OutlinedButton("GitHub", icon=ft.icons.CODE),
                ],
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text("Don't have an account?", size=12, color=MUTED),
                    ft.TextButton("Register now", on_click=lambda e: page.go("/register")),
                ],
            ),
        ],
    )
    return auth_layout(
        "Welcome back",
        "Sign in to manage your freelance projects and secure payments.",
        card,
        page,
    )


def view_register(page):
    sel_role = ["customer"]
    card_refs = {"cust": None, "work": None}

    def refresh_borders():
        c, w = card_refs["cust"], card_refs["work"]
        if not c or not w:
            return
        c.border = ft.border.all(2, PRIMARY) if sel_role[0] == "customer" else ft.border.all(1, BORDER)
        w.border = ft.border.all(2, PRIMARY) if sel_role[0] == "worker" else ft.border.all(1, BORDER)

    def pick_customer(_):
        sel_role[0] = "customer"
        refresh_borders()
        page.update()

    def pick_worker(_):
        sel_role[0] = "worker"
        refresh_borders()
        page.update()

    cust_card = ft.Container(
        expand=True,
        padding=12,
        border_radius=12,
        border=ft.border.all(2, PRIMARY),
        on_click=pick_customer,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.icons.PERSON, color=PRIMARY),
                ft.Text("Customer", size=13, weight=ft.FontWeight.W_600),
                ft.Text("Post projects and hire talent", size=11, color=MUTED),
            ],
        ),
    )
    work_card = ft.Container(
        expand=True,
        padding=12,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        on_click=pick_worker,
        content=ft.Column(
            spacing=6,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.Icon(ft.icons.WORK_OUTLINE, color=MUTED),
                ft.Text("Freelance Worker", size=13, weight=ft.FontWeight.W_600),
                ft.Text("Find projects and offer services", size=11, color=MUTED),
            ],
        ),
    )
    card_refs["cust"] = cust_card
    card_refs["work"] = work_card

    name_field = auth_text_field(label="Full Name", expand=True)
    phone_field = auth_text_field(label="Phone Number", expand=True)
    email_field = auth_text_field(label="Work Email", expand=True)
    pw_field = auth_text_field(label="Password", password=True, can_reveal_password=True, expand=True)
    pw2_field = auth_text_field(label="Confirm Password", password=True, can_reveal_password=True, expand=True)
    terms = ft.Checkbox()
    err = ft.Text("", color=DANGER, size=13)

    def on_register(_):
        err.value = ""
        if not terms.value:
            err.value = "Please accept the terms and conditions."
            page.update()
            return
        if (pw_field.value or "") != (pw2_field.value or ""):
            err.value = "Passwords do not match."
            page.update()
            return
        ok, msg = create_user(
            email_field.value,
            pw_field.value,
            name_field.value,
            phone_field.value,
            sel_role[0],
        )
        if not ok:
            err.value = msg or "Registration failed."
            page.update()
            return
        row = authenticate_user(email_field.value, pw_field.value)
        if row:
            set_session_from_user(page, row)
        page.go("/dashboard")

    card = ft.Column(
        spacing=16,
        controls=[
            err,
            ft.Text("I AM A...", size=12, weight=ft.FontWeight.W_600, color=MUTED),
            ft.Row(spacing=12, controls=[cust_card, work_card]),
            ft.Divider(height=8, color="transparent"),
            ft.Text("PERSONAL INFORMATION", size=13, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Row(spacing=12, controls=[name_field, phone_field]),
            email_field,
            ft.Text("SECURITY", size=13, weight=ft.FontWeight.W_600, color=TEXT),
            ft.Row(spacing=12, controls=[pw_field, pw2_field]),
            ft.Row(
                spacing=8,
                controls=[terms, ft.Text("Accept terms and conditions", size=13, color=MUTED)],
            ),
            ft.ElevatedButton(
                "Get Started",
                bgcolor=PRIMARY,
                color="white",
                height=48,
                width=412,
                on_click=on_register,
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.CENTER,
                controls=[
                    ft.Text("Already have an account?", size=12, color=MUTED),
                    ft.TextButton("Log in here", on_click=lambda e: page.go("/")),
                ],
            ),
        ],
    )
    return auth_layout(
        "Create your account",
        "Join thousands of businesses and professionals using EscrowFlow.",
        card,
        page,
        topbar=True,
    )


def view_dashboard(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    stats = ft.Row(
        spacing=12,
        controls=[
            stat_card("Active Projects", "12", "+3 starting this week", ft.icons.WORK_OUTLINE),
            stat_card("Funded Escrows", "$45,200", "Across active contracts", ft.icons.PAID_OUTLINED),
            stat_card("Open Proposals", "28", "+12 new today", ft.icons.MARK_EMAIL_UNREAD_OUTLINED),
            stat_card("Open Disputes", "1", "Requires resolution in 24h", ft.icons.REPORT_OUTLINED, DANGER),
        ],
    )

    in_progress = ft.Container(
        bgcolor=CARD,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        padding=16,
        content=ft.Column(
            spacing=12,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("In-Progress Projects", size=14, weight=ft.FontWeight.W_700),
                        ft.TextButton("View All", on_click=lambda e: page.go("/projects")),
                    ],
                ),
                project_row("Mobile UI Design System", "Sarah Miller", 0.75, "In Progress", "Due Oct 24"),
                project_row("Smart Contract Audit", "Ethereal Labs", 0.4, "Milestone Pending", "Due Nov 02"),
                project_row("Backend API Integration", "David Chen", 0.95, "Awaiting Approval", "Due Today"),
                project_row("Brand Identity Revamp", "Creative Pulse", 0.15, "Recently Started", "Due Dec 12"),
            ],
        ),
    )

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=10,
                    controls=[
                        ft.Text("Quick Actions", size=13, weight=ft.FontWeight.W_700),
                        ft.ElevatedButton("Post New Project", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/project-create")),
                        ft.OutlinedButton("Review Proposals", on_click=lambda e: page.go("/projects")),
                        ft.OutlinedButton("Fund Escrow Account", on_click=lambda e: page.go("/escrow")),
                        ft.OutlinedButton("Raise a Dispute", icon=ft.icons.REPORT_OUTLINED, on_click=lambda e: page.go("/dispute")),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Activity Feed", size=13, weight=ft.FontWeight.W_700),
                        activity_item("Marcus Wright submitted a deliverable", "12 minutes ago"),
                        activity_item("Escrow System confirmed funding", "2 hours ago"),
                        activity_item("Elena Rossi sent a proposal", "5 hours ago"),
                        activity_item("Jonathan Doe completed milestone", "1 day ago"),
                        ft.TextButton("View full activity history", on_click=lambda e: page.go("/contract")),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, DANGER),
                bgcolor="#FFF1F2",
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Action Required: Open Dispute", size=12, weight=ft.FontWeight.W_700, color=DANGER),
                        ft.Text(
                            "A dispute has been raised regarding the 'Logo Design' project.",
                            size=11,
                            color=MUTED,
                        ),
                        ft.ElevatedButton("Resolve Now", bgcolor=DANGER, color="white", on_click=lambda e: page.go("/dispute")),
                    ],
                ),
            ),
        ],
    )

    lower_panels = ft.Row(
        spacing=12,
        controls=[
            ft.Container(
                expand=True,
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Escrow Security", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(
                            spacing=10,
                            controls=[
                                ft.Container(
                                    width=36,
                                    height=36,
                                    border_radius=18,
                                    bgcolor="#EAF8EE",
                                    content=ft.Icon(ft.icons.SHIELD_OUTLINED, color=SUCCESS, size=18),
                                    alignment=CENTER,
                                ),
                                ft.Column(
                                    spacing=2,
                                    controls=[
                                        ft.Text("100% Protected", size=12, weight=ft.FontWeight.W_600),
                                        ft.Text("All funds held in triple-audited accounts.", size=10, color=MUTED),
                                    ],
                                ),
                            ],
                        ),
                        ft.OutlinedButton("Review Legal Terms", on_click=lambda e: page.go("/contract")),
                    ],
                ),
            ),
            ft.Container(
                expand=True,
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Quick Statistics", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Average Approval Time", size=10, color=MUTED), ft.Text("4.2 hours", size=10, weight=ft.FontWeight.W_600)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Worker Retention Rate", size=10, color=MUTED), ft.Text("92%", size=10, weight=ft.FontWeight.W_600, color=SUCCESS)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Escrow Efficiency", size=10, color=MUTED), ft.Text("High", size=10, weight=ft.FontWeight.W_600)]),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Dashboard Overview", size=18, weight=ft.FontWeight.W_700),
                                ft.Text(
                                    f"Welcome back, {(page.session.store.get('user_name') or 'User').split()[0]}. You have 3 milestones awaiting approval today.",
                                    size=12,
                                    color=MUTED,
                                ),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.OutlinedButton("Escrow Balance: $12,450.00", icon=ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, on_click=lambda e: page.go("/escrow")),
                                ft.ElevatedButton("New Project", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/project-create")),
                            ],
                        ),
                    ],
                ),
                stats,
                in_progress,
                lower_panels,
            ]),
            ft.Container(width=300, content=right),
        ],
    )

    return shell(page, content, "/dashboard", nav_items, *session_user(page))


def project_row(title, lead, progress, status, due):
    return ft.Container(
        padding=12,
        border_radius=10,
        border=ft.border.all(1, BORDER),
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text(title, size=12, weight=ft.FontWeight.W_600),
                                ft.Text(f"Lead: {lead}", size=10, color=MUTED),
                            ],
                        ),
                        pill(status, color=PRIMARY, bg="#E8F0FF"),
                    ],
                ),
                ft.ProgressBar(value=progress, color=PRIMARY, bgcolor="#EAF0FF"),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Overall Progress", size=10, color=MUTED),
                        ft.Text(due, size=10, color=MUTED),
                    ],
                ),
            ],
        ),
    )


def activity_item(text, time):
    return ft.Row(
        spacing=8,
        controls=[
            ft.CircleAvatar(radius=12, bgcolor="#E2E8F0", content=ft.Icon(ft.icons.PERSON, size=12, color=MUTED)),
            ft.Column(
                spacing=2,
                controls=[ft.Text(text, size=11), ft.Text(time, size=10, color=MUTED)],
            ),
        ],
    )


def view_admin_overview(page):
    nav_items = [
        ("Overview", ft.icons.DASHBOARD_OUTLINED, "/admin"),
        ("Escrow Control", ft.icons.ACCOUNT_BALANCE_OUTLINED, "/escrow-control"),
        ("Disputes", ft.icons.REPORT_OUTLINED, "/dispute"),
        ("User Management", ft.icons.GROUP_OUTLINED, "/user-management"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    stats = ft.Row(
        spacing=12,
        controls=[
            stat_card("Total Escrow Balance", "$1,248,390.42", "+12.5%", ft.icons.SHIELD_OUTLINED),
            stat_card("Daily Volume", "$58,210.00", "+4.3%", ft.icons.SHOW_CHART),
            stat_card("Open Disputes", "14", "-2", ft.icons.WARNING_AMBER_OUTLINED, DANGER),
            stat_card("Active Contracts", "842", "+28", ft.icons.DESCRIPTION_OUTLINED),
        ],
    )

    chart = ft.Container(
        padding=16,
        border_radius=12,
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Transaction Volume Trends", size=13, weight=ft.FontWeight.W_700),
                        ft.Row(controls=[pill("Last 7 Days"), pill("30 Days", color=MUTED, bg="#F1F5F9")]),
                    ],
                ),
                ft.Container(
                    height=160,
                    border_radius=10,
                    bgcolor="#F8FAFF",
                    alignment=CENTER,
                    content=ft.Text("Line chart placeholder", color=MUTED, size=11),
                ),
            ],
        ),
    )

    table = ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Transaction")),
            ft.DataColumn(ft.Text("Project")),
            ft.DataColumn(ft.Text("Type")),
            ft.DataColumn(ft.Text("Amount")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("TX-9021")),
                ft.DataCell(ft.Text("Enterprise Cloud Migration")),
                ft.DataCell(pill("Release")),
                ft.DataCell(ft.Text("$12,500.00")),
                ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3")),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("TX-8842")),
                ft.DataCell(ft.Text("AI Model Training Dataset")),
                ft.DataCell(pill("Refund", color=DANGER, bg="#FEE2E2")),
                ft.DataCell(ft.Text("$8,200.00")),
                ft.DataCell(pill("Flagged", color=DANGER, bg="#FEE2E2")),
            ]),
            ft.DataRow(cells=[
                ft.DataCell(ft.Text("TX-8711")),
                ft.DataCell(ft.Text("Mobile App Redesign")),
                ft.DataCell(pill("Fund")),
                ft.DataCell(ft.Text("$4,500.00")),
                ft.DataCell(pill("Pending", color=WARNING, bg="#FEF3C7")),
            ]),
        ],
    )])

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                bgcolor=CARD,
                border=ft.border.all(1, BORDER),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("System Alerts", size=13, weight=ft.FontWeight.W_700),
                                pill("3 Urgent", color=DANGER, bg="#FEE2E2"),
                            ],
                        ),
                        ft.ListTile(title=ft.Text("High-Value Dispute Opened", size=11), subtitle=ft.Text("Contract #C-3421", size=10, color=MUTED)),
                        ft.ListTile(title=ft.Text("Pending Account Verification", size=11), subtitle=ft.Text("KYC approval awaiting", size=10, color=MUTED)),
                        ft.ListTile(title=ft.Text("System Maintenance", size=11), subtitle=ft.Text("Scheduled update at 02:00 UTC", size=10, color=MUTED)),
                        ft.OutlinedButton("View All Issues"),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                bgcolor=CARD,
                border=ft.border.all(1, BORDER),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Admin Shortcuts", size=13, weight=ft.FontWeight.W_700),
                        ft.Row(spacing=8, controls=[small_button("Transactions"), small_button("Disputes")]),
                        ft.Row(spacing=8, controls=[small_button("Contracts"), small_button("User Audit")]),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Platform Overview", size=18, weight=ft.FontWeight.W_700),
                                ft.Text("Monitoring system health and financial integrity.", size=12, color=MUTED),
                            ],
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.OutlinedButton("Manage Users", icon=ft.icons.GROUP_OUTLINED, on_click=lambda e: page.go("/user-management")),
                                ft.ElevatedButton("Audit Escrows", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/escrow-control")),
                            ],
                        ),
                    ],
                ),
                stats,
                chart,
                ft.Container(padding=16, border_radius=12, bgcolor=CARD, border=ft.border.all(1, BORDER), content=table),
            ]),
            ft.Container(width=300, content=right),
        ],
    )

    return shell(page, content, "/admin", nav_items, *session_user(page))


def view_escrow_control(page):
    nav_items = [
        ("Overview", ft.icons.DASHBOARD_OUTLINED, "/admin"),
        ("Escrow Control", ft.icons.ACCOUNT_BALANCE_OUTLINED, "/escrow-control"),
        ("Disputes", ft.icons.REPORT_OUTLINED, "/dispute"),
        ("User Management", ft.icons.GROUP_OUTLINED, "/user-management"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    content = ft.Container(
        padding=20,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        bgcolor=CARD,
        content=ft.Column(
            spacing=10,
            controls=[
                        ft.Text("Escrow Control", size=18, weight=ft.FontWeight.W_700),
                ft.Text("Administrative controls for escrow compliance and audit trails.", size=12, color=MUTED),
                ft.Row(spacing=12, controls=[
                    stat_card("Flagged Transactions", "6", "Requires review", ft.icons.REPORT_OUTLINED, WARNING),
                    stat_card("Pending Approvals", "18", "KYC + compliance", ft.icons.VERIFIED_OUTLINED, INFO),
                    stat_card("Active Audits", "3", "Quarterly checks", ft.icons.FACT_CHECK_OUTLINED, PRIMARY),
                ]),
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor="#F8FAFF",
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Compliance Queue", size=12, weight=ft.FontWeight.W_700),
                            ft.Text("Manual review items, audit checkpoints, and release approvals are centralized here.", size=11, color=MUTED),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.OutlinedButton("Open Disputes", on_click=lambda e: page.go("/dispute")),
                                    ft.ElevatedButton("Review Users", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/user-management")),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    return shell(page, content, "/escrow-control", nav_items, *session_user(page))


def small_button(text):
    return ft.Container(
        expand=True,
        padding=10,
        border_radius=10,
        bgcolor="#F1F5F9",
        content=ft.Text(text, size=11, weight=ft.FontWeight.W_600),
        alignment=CENTER,
    )


def view_projects(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    user_id = page.session.store.get("user_id")
    projects = get_projects_for_user(user_id) if user_id else []
    first_pid = int(projects[0]["id"]) if (projects and user_id) else None

    def status_pill(project_status: str):
        s = (project_status or "").strip().lower()
        if s == "draft":
            return pill("Draft", color=TEXT, bg="#F1F5F9")
        if s == "published":
            return pill("Open", color=INFO, bg="#E0F2FE")
        if s == "active":
            return pill("Active", color=PRIMARY, bg="#E8F0FF")
        if s == "completed":
            return pill("Closed", color=MUTED, bg="#F1F5F9")
        if s == "cancelled":
            return pill("Cancelled", color=DANGER, bg="#FEF2F2")
        return pill(project_status or "Unknown", color=PRIMARY, bg="#E8F0FF")

    rows = []
    if projects and user_id:
        for p in projects:
            pid = int(p["id"])
            project_id_str = f"PRJ-{pid:04d}"
            timeline = ""
            if p.get("start_date") or p.get("end_date"):
                timeline = f"{(p.get('start_date') or '').strip()} — {(p.get('end_date') or '').strip()}".strip(" —")
            budget_value = float(p.get("budget") or 0)
            budget_str = f"${budget_value:,.2f}"
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(project_id_str)),
                        ft.DataCell(ft.Text(p.get("title") or "")),
                        ft.DataCell(ft.Text(p.get("customer_ref") or "")),
                        ft.DataCell(status_pill(p.get("status"))),
                        ft.DataCell(ft.Text(timeline)),
                        ft.DataCell(ft.Text(budget_str)),
                        ft.DataCell(
                            ft.Row(
                                spacing=2,
                                controls=[
                                    ft.TextButton(
                                        "Open",
                                        on_click=lambda e, i=pid: page.go(f"/project-detail?id={i}"),
                                    ),
                                    ft.TextButton(
                                        "Edit",
                                        on_click=lambda e, i=pid: page.go(f"/project-create?id={i}"),
                                    ),
                                    ft.TextButton(
                                        "Delete",
                                        style=ft.ButtonStyle(color=DANGER),
                                        on_click=lambda e, i=pid: _confirm_delete_project(page, i, user_id),
                                    ),
                                ],
                            )
                        ),
                    ]
                )
            )
    else:
        rows = [
            ft.DataRow(
                cells=[
                    ft.DataCell(ft.Text("—")),
                    ft.DataCell(ft.Text("No projects yet. Use Create New Project.")),
                    ft.DataCell(ft.Text("—")),
                    ft.DataCell(pill("—", color=TEXT, bg="#F1F5F9")),
                    ft.DataCell(ft.Text("—")),
                    ft.DataCell(ft.Text("$0.00")),
                    ft.DataCell(ft.Text("—")),
                ]
            )
        ]

    if first_pid is not None:
        open_latest = ft.TextButton(
            "Open latest project",
            on_click=lambda e: page.go(f"/project-detail?id={first_pid}"),
        )
    else:
        open_latest = ft.TextButton("Create a project", on_click=lambda e: page.go("/project-create"))

    def open_recommendation_project(_):
        if first_pid is not None:
            page.go(f"/project-detail?id={first_pid}")
        else:
            page.go("/project-create")

    table = ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Project ID")),
            ft.DataColumn(ft.Text("Title")),
            ft.DataColumn(ft.Text("Customer")),
            ft.DataColumn(ft.Text("Status")),
            ft.DataColumn(ft.Text("Timeline")),
            ft.DataColumn(ft.Text("Budget")),
            ft.DataColumn(ft.Text("Actions")),
        ],
        rows=rows,
    )])

    content = ft.Column(
        spacing=12,
        controls=[
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Column(spacing=2, controls=[
                        ft.Text("Project Management", size=18, weight=ft.FontWeight.W_700),
                        ft.Text("Monitor your projects, evaluate proposals, and manage secure escrow accounts.", size=12, color=MUTED),
                    ]),
                    ft.ElevatedButton(
                        "Create New Project",
                        bgcolor=PRIMARY,
                        color="white",
                        on_click=lambda e: page.go("/project-create"),
                    ),
                ],
            ),
            ft.Row(
                spacing=12,
                controls=[
                    stat_card(
                        "Total Projects",
                        str(len(projects)),
                        "Your saved projects",
                        ft.icons.FOLDER_OUTLINED,
                    ),
                    stat_card("Active Escrows", "$42,300", "Funds secured in transit", ft.icons.PAID_OUTLINED),
                    stat_card("Open Proposals", "12", "Awaiting your review", ft.icons.MARK_EMAIL_UNREAD_OUTLINED),
                    stat_card("Active Disputes", "0", "All contracts healthy", ft.icons.CHECK_CIRCLE_OUTLINE, SUCCESS),
                ],
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                bgcolor=CARD,
                border=ft.border.all(1, BORDER),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("All Projects", size=13, weight=ft.FontWeight.W_700),
                                ft.Row(spacing=8, controls=[
                                    ft.TextField(hint_text="Search title, ID...", height=36),
                                    pill("All", color=TEXT, bg="#F1F5F9"),
                                    pill("Open", color=INFO, bg="#E0F2FE"),
                                    pill("Awarded", color=PRIMARY, bg="#E8F0FF"),
                                    pill("Closed", color=MUTED, bg="#F1F5F9"),
                                    open_latest,
                                ]),
                            ],
                        ),
                        table,
                    ],
                ),
            ),
            ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=16,
                        border_radius=12,
                        bgcolor=CARD,
                        border=ft.border.all(1, BORDER),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("System Recommendations", size=12, weight=ft.FontWeight.W_700),
                                ft.Container(
                                    padding=14,
                                    border_radius=12,
                                    bgcolor="#F8FAFF",
                                    border=ft.border.all(1, BORDER),
                                    content=ft.Column(
                                        spacing=4,
                                        controls=[
                                            ft.Text('New Proposals for "Mobile App API"', size=12, weight=ft.FontWeight.W_600),
                                            ft.Text("3 top-rated freelancers recently submitted competitive bids. Review their profiles now.", size=10, color=MUTED),
                                            ft.TextButton("View project", on_click=open_recommendation_project),
                                        ],
                                    ),
                                ),
                            ],
                        ),
                    ),
                    ft.Container(
                        width=280,
                        padding=16,
                        border_radius=12,
                        bgcolor=CARD,
                        border=ft.border.all(1, BORDER),
                        content=ft.Column(
                            spacing=8,
                            controls=[
                                ft.Text("Need Help?", size=12, weight=ft.FontWeight.W_700),
                                ft.Text("Stuck with awarding a contract or managing milestones? Our secure escrow guides are here to help.", size=10, color=MUTED),
                                ft.OutlinedButton("Read Documentation", on_click=lambda e: page.go("/contract")),
                            ],
                        ),
                    ),
                ],
            ),
        ],
    )

    return shell(page, content, "/projects", nav_items, *session_user(page))


def view_project_detail(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    user_id = page.session.store.get("user_id")
    project_id = route_query_int(page, "id")

    def detail_status_pill(project_status: str):
        s = (project_status or "").strip().lower()
        if s == "draft":
            return pill("Draft", color=TEXT, bg="#F1F5F9")
        if s == "published":
            return pill("Open", color=INFO, bg="#E0F2FE")
        if s == "active":
            return pill("Active", color=PRIMARY, bg="#E8F0FF")
        if s == "completed":
            return pill("Closed", color=MUTED, bg="#F1F5F9")
        if s == "cancelled":
            return pill("Cancelled", color=DANGER, bg="#FEF2F2")
        return pill(project_status or "Unknown", color=PRIMARY, bg="#E8F0FF")

    if not user_id or not project_id:
        content = ft.Container(
            padding=24,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Project not found", size=18, weight=ft.FontWeight.W_700),
                    ft.Text("Open a project from My Projects or create a new one.", size=12, color=MUTED),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.ElevatedButton("My Projects", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/projects")),
                            ft.OutlinedButton("Create project", on_click=lambda e: page.go("/project-create")),
                        ],
                    ),
                ],
            ),
        )
        return shell(page, content, "/projects", nav_items, *session_user(page))

    proj = get_project_for_owner(project_id, user_id)
    if not proj:
        content = ft.Container(
            padding=24,
            content=ft.Column(
                spacing=12,
                controls=[
                    ft.Text("Access denied or project missing", size=18, weight=ft.FontWeight.W_700),
                    ft.Text("This project may not exist or you are not the owner.", size=12, color=MUTED),
                    ft.ElevatedButton("Back to projects", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/projects")),
                ],
            ),
        )
        return shell(page, content, "/projects", nav_items, *session_user(page))

    budget_val = float(proj.get("budget") or 0)
    budget_str = f"${budget_val:,.2f}"
    timeline = ""
    if proj.get("start_date") or proj.get("end_date"):
        timeline = f"{(proj.get('start_date') or '').strip()} — {(proj.get('end_date') or '').strip()}".strip(" —")
    prj_label = f"PRJ-{int(proj['id']):04d}"
    cat = (proj.get("category") or "").strip() or "—"

    summary = ft.Container(
        padding=16,
        border_radius=12,
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        content=ft.Column(
            spacing=8,
            controls=[
                ft.Text("Project Summary", size=12, weight=ft.FontWeight.W_700),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Project ID", size=11, color=MUTED),
                        ft.Text(prj_label, size=12, weight=ft.FontWeight.W_600),
                    ],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Budget", size=11, color=MUTED), ft.Text(budget_str, size=12, weight=ft.FontWeight.W_600)],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Status", size=11, color=MUTED), detail_status_pill(proj.get("status"))],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Timeline", size=11, color=MUTED), ft.Text(timeline or "—", size=11)],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Category", size=11, color=MUTED), ft.Text(cat, size=11)],
                ),
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[ft.Text("Customer ref", size=11, color=MUTED), ft.Text((proj.get("customer_ref") or "—").strip(), size=11)],
                ),
            ],
        ),
    )

    proposals = ft.Column(
        spacing=10,
        controls=[
            ft.Container(
                padding=14,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor="#F8FAFF",
                content=ft.Text(
                    "No proposals stored yet. (Proposal bidding can be wired to the proposals table next.)",
                    size=11,
                    color=MUTED,
                ),
            )
        ],
    )

    desc = (proj.get("description") or "").strip() or "No description provided."

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(
                expand=True,
                spacing=12,
                controls=[
                    ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text(proj.get("title") or "Project", size=18, weight=ft.FontWeight.W_700),
                                    ft.Text(prj_label, size=11, color=MUTED),
                                ],
                            ),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.OutlinedButton("Back", on_click=lambda e: page.go("/projects")),
                                    ft.OutlinedButton(
                                        "Edit",
                                        on_click=lambda e, pid=project_id: page.go(f"/project-create?id={pid}"),
                                    ),
                                    ft.OutlinedButton(
                                        "Delete",
                                        style=ft.ButtonStyle(color=DANGER),
                                        on_click=lambda e, pid=project_id: _confirm_delete_project(page, pid, user_id),
                                    ),
                                ],
                            ),
                        ],
                    ),
                    ft.Text("Description", size=12, weight=ft.FontWeight.W_600),
                    ft.Text(desc, size=11, color=MUTED),
                    ft.Row(spacing=8, controls=[pill((proj.get("category") or "General").strip() or "General")]),
                    ft.Divider(),
                    ft.Row(
                        spacing=12,
                        controls=[
                            pill("Proposals (0)", color=TEXT, bg="#F1F5F9"),
                            pill("Milestones & Contract", color=MUTED, bg="#F8FAFC"),
                        ],
                    ),
                    proposals,
                ],
            ),
            ft.Container(width=280, content=ft.Column(spacing=12, controls=[summary, help_card("Need help with this project?")])),
        ],
    )

    return shell(page, content, "/projects", nav_items, *session_user(page))


def proposal_card(page, name, rating, blurb, amount):
    return ft.Container(
        padding=14,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        bgcolor=CARD,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Row(spacing=10, controls=[
                    ft.CircleAvatar(radius=18, bgcolor="#E2E8F0", content=ft.Text(name[:1])),
                    ft.Column(spacing=2, controls=[
                        ft.Row(spacing=6, controls=[ft.Text(name, size=12, weight=ft.FontWeight.W_600), pill(f"★ {rating}", color="#B45309", bg="#FEF3C7")]),
                        ft.Text(blurb, size=10, color=MUTED),
                    ]),
                ]),
                ft.Column(spacing=4, controls=[
                    ft.Text(f"Bid Amount", size=10, color=MUTED),
                    ft.Text(amount, size=12, weight=ft.FontWeight.W_700, color=PRIMARY),
                    ft.Row(spacing=6, controls=[ft.OutlinedButton("View Details"), ft.ElevatedButton("Award Project", bgcolor=PRIMARY, color="white", on_click=lambda e: show_snack(page, "Layihə uğurla təhvil verildi! ✓", "success"))]),
                ]),
            ],
        ),
    )


def help_card(text):
    return ft.Container(
        padding=14,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        bgcolor="#F8FAFF",
        content=ft.Column(
            spacing=6,
            controls=[
                ft.Text(text, size=11, weight=ft.FontWeight.W_600),
                ft.Text("Our support team is available 24/7 for escrow disputes and platform assistance.", size=10, color=MUTED),
                ft.TextButton("Contact Support"),
            ],
        ),
    )


def view_project_create(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    user_id = page.session.store.get("user_id")
    edit_id = route_query_int(page, "id")

    title_field = ft.TextField(label="Project Title")
    desc_field = ft.TextField(label="Project Description", multiline=True, min_lines=3)
    customer_ref_field = ft.TextField(label="Customer ID", expand=True)
    category_field = ft.TextField(label="Category", expand=True)
    start_date_field = ft.TextField(label="Start Date", expand=True)
    end_date_field = ft.TextField(label="Estimated End Date", expand=True)
    budget_field = ft.TextField(label="Total Project Budget (USD)")

    heading = ft.Text("Create New Project", size=18, weight=ft.FontWeight.W_700)

    if user_id and edit_id:
        existing = get_project_for_owner(edit_id, user_id)
        if existing:
            heading.value = f"Edit Project — PRJ-{int(existing['id']):04d}"
            title_field.value = existing.get("title") or ""
            desc_field.value = existing.get("description") or ""
            customer_ref_field.value = existing.get("customer_ref") or ""
            category_field.value = existing.get("category") or ""
            start_date_field.value = existing.get("start_date") or ""
            end_date_field.value = existing.get("end_date") or ""
            b = float(existing.get("budget") or 0)
            budget_field.value = f"${b:,.2f}" if b else ""
        else:
            # Will show snack after page renders via a deferred call pattern
            pass

    def submit_project(status: str):
        uid = page.session.store.get("user_id")
        if not uid:
            show_snack(page, "Zəhmət olmasa əvvəlcə daxil olun.", "error")
            return
            
        fields = [
            title_field.value, desc_field.value, customer_ref_field.value,
            category_field.value, start_date_field.value, end_date_field.value,
            budget_field.value
        ]
        if any(not str(f or "").strip() for f in fields):
            show_snack(page, "Bütün xanaları doldurmaq mütləqdir.", "error")
            return
        if edit_id:
            ok, message = update_project(
                project_id=edit_id,
                owner_user_id=uid,
                title=title_field.value,
                description=desc_field.value,
                customer_ref=customer_ref_field.value,
                category=category_field.value,
                start_date=start_date_field.value,
                end_date=end_date_field.value,
                budget_raw=budget_field.value,
                status=status,
            )
            if not ok:
                show_snack(page, message or "Layihə yenilənə bilmədi.", "error")
                return
            show_snack(page, "Layihə uğurla yeniləndi! ✓", "success")
            page.go(f"/project-detail?id={edit_id}")
            return

        ok, message, new_id = create_project(
            owner_user_id=uid,
            title=title_field.value,
            description=desc_field.value,
            customer_ref=customer_ref_field.value,
            category=category_field.value,
            start_date=start_date_field.value,
            end_date=end_date_field.value,
            budget_raw=budget_field.value,
            status=status,
        )
        if not ok:
            show_snack(page, message or "Layihə saxlanıla bilmədi.", "error")
            return
        label = "Layihə qaralama olaraq saxlandı." if status == "draft" else "Layihə uğurla nəşr edildi! ✓"
        show_snack(page, label, "success")
        if new_id:
            page.go(f"/project-detail?id={new_id}")
        else:
            page.go("/projects")

    form = ft.Column(
        spacing=14,
        controls=[
            heading,
            section("Project Identity"),
            title_field,
            desc_field,
            ft.Row(spacing=12, controls=[customer_ref_field, category_field]),
            section("Timeline & Budget"),
            ft.Row(spacing=12, controls=[start_date_field, end_date_field]),
            budget_field,
            section("Project Assets"),
            ft.Container(
                height=120,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                alignment=CENTER,
                content=ft.Column(
                    alignment=ft.MainAxisAlignment.CENTER,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    controls=[
                        ft.Icon(ft.icons.CLOUD_UPLOAD_OUTLINED, color=MUTED),
                        ft.Text("Drop files here or click to upload", size=11, color=MUTED),
                        ft.Text("Supports PDF, DOCX, ZIP", size=10, color=MUTED),
                    ],
                ),
            ),
            ft.Row(
                alignment=ft.MainAxisAlignment.END,
                controls=[
                    ft.TextButton("Cancel Changes", on_click=lambda e: page.go("/projects")),
                    ft.OutlinedButton("Save as Draft", on_click=lambda e: submit_project("draft")),
                    ft.ElevatedButton(
                        "Publish Project",
                        bgcolor=PRIMARY,
                        color="white",
                        on_click=lambda e: submit_project("published"),
                    ),
                ],
            ),
        ],
    )

    content = ft.Container(
        padding=20,
        border_radius=12,
        bgcolor=CARD,
        border=ft.border.all(1, BORDER),
        content=form,
    )

    return shell(page, content, "/projects", nav_items, *session_user(page))


def section(text):
    return ft.Row(spacing=8, controls=[ft.Icon(ft.icons.CATEGORY_OUTLINED, color=PRIMARY, size=16), ft.Text(text, size=12, weight=ft.FontWeight.W_600)])


def view_proposal(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("Find Projects", ft.icons.SEARCH_OUTLINED, "/proposal"),
        ("Proposals", ft.icons.MAIL_OUTLINED, "/proposal"),
        ("Earnings", ft.icons.ATTACH_MONEY, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Text("Project Proposal", size=18, weight=ft.FontWeight.W_700),
                ft.Text("Submit your bid and manage your active proposals for this project.", size=12, color=MUTED),
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor=CARD,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Full-Stack E-commerce Platform with Escrow Integration", size=12, weight=ft.FontWeight.W_600),
                            ft.Text("$2,000 — $3,500", size=12, color=PRIMARY),
                            ft.Row(spacing=10, controls=[pill("Deadline: Jun 30, 2024", color=MUTED, bg="#F1F5F9"), pill("Payment Verified", color=SUCCESS, bg="#ECFDF3")]),
                        ],
                    ),
                ),
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor=CARD,
                    content=ft.Column(
                        spacing=10,
                        controls=[
                            ft.Text("My Proposal History", size=12, weight=ft.FontWeight.W_700),
                            ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
                                columns=[
                                    ft.DataColumn(ft.Text("Proposal ID")),
                                    ft.DataColumn(ft.Text("Amount")),
                                    ft.DataColumn(ft.Text("Status")),
                                    ft.DataColumn(ft.Text("Submitted At")),
                                ],
                                rows=[
                                    ft.DataRow(cells=[
                                        ft.DataCell(ft.Text("PROP-8102")),
                                        ft.DataCell(ft.Text("$2,400")),
                                        ft.DataCell(pill("Pending", color=WARNING, bg="#FEF3C7")),
                                        ft.DataCell(ft.Text("2024-05-15 09:30")),
                                    ]),
                                    ft.DataRow(cells=[
                                        ft.DataCell(ft.Text("PROP-8821")),
                                        ft.DataCell(ft.Text("$2,100")),
                                        ft.DataCell(pill("Withdrawn", color=MUTED, bg="#F1F5F9")),
                                        ft.DataCell(ft.Text("2024-05-12 14:15")),
                                    ]),
                                ],
                            )]),
                        ],
                    ),
                ),
            ]),
            ft.Container(
                width=320,
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Container(
                            padding=16,
                            border_radius=12,
                            border=ft.border.all(1, BORDER),
                            bgcolor=CARD,
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Submit New Proposal", size=12, weight=ft.FontWeight.W_700),
                                    ft.TextField(label="Bid Amount (USD)", value="$ 0.00"),
                                    ft.TextField(label="Estimated Duration (Days)", value="14"),
                                    ft.TextField(label="Cover Letter / Message", multiline=True, min_lines=3),
                                    ft.OutlinedButton("Upload Attachments"),
                                    ft.ElevatedButton("Submit Proposal", bgcolor=PRIMARY, color="white", on_click=lambda e: _open_submit_proposal_sheet(page)),
                                ],
                            ),
                        ),
                        help_card("Have questions for the client?")
                    ],
                ),
            ),
        ],
    )

    return shell(page, content, "/proposal", nav_items, *session_user(page))


def view_contract(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    steps = ft.Row(
        spacing=14,
        controls=[
            pill("Drafted"), pill("Signed", color=MUTED, bg="#F1F5F9"), pill("Funded", color=MUTED, bg="#F1F5F9"), pill("Active", color=MUTED, bg="#F1F5F9"), pill("Completed", color=MUTED, bg="#F1F5F9"),
        ],
    )

    table = ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Milestone Description")),
            ft.DataColumn(ft.Text("Due Date")),
            ft.DataColumn(ft.Text("Amount")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("M1")), ft.DataCell(ft.Text("UI/UX Design Mockups & Prototypes")), ft.DataCell(ft.Text("Oct 25, 2023")), ft.DataCell(ft.Text("$2,500.00")), ft.DataCell(pill("Verified", color=SUCCESS, bg="#ECFDF3"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("M2")), ft.DataCell(ft.Text("Frontend Development (Core)")), ft.DataCell(ft.Text("Nov 15, 2023")), ft.DataCell(ft.Text("$4,000.00")), ft.DataCell(pill("Active", color=INFO, bg="#E0F2FE"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("M3")), ft.DataCell(ft.Text("API Integration & Database Setup")), ft.DataCell(ft.Text("Dec 05, 2023")), ft.DataCell(ft.Text("$3,500.00")), ft.DataCell(pill("Pending", color=WARNING, bg="#FEF3C7"))]),
        ],
    )])

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor="#F0F7FF",
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Escrow Balance", size=12, weight=ft.FontWeight.W_700),
                        ft.Text("$12,500.00", size=20, weight=ft.FontWeight.W_700, color=PRIMARY),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Deposited", size=10, color=MUTED), ft.Text("$0.00", size=10)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Pending Release", size=10, color=MUTED), ft.Text("$2,500.00", size=10)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Earned / Paid", size=10, color=MUTED), ft.Text("$0.00", size=10)]),
                        ft.ElevatedButton("Manage Escrow Account", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/escrow")),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Parties Involved", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(spacing=8, controls=[ft.CircleAvatar(radius=14, bgcolor="#E2E8F0"), ft.Text("Jonathan Vance", size=11), pill("Signed", color=SUCCESS, bg="#ECFDF3")]),
                        ft.Row(spacing=8, controls=[ft.CircleAvatar(radius=14, bgcolor="#E2E8F0"), ft.Text("Marco Rossi", size=11), pill("Pending", color=WARNING, bg="#FEF3C7")]),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, DANGER),
                bgcolor="#FEF2F2",
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Danger Zone", size=12, weight=ft.FontWeight.W_700, color=DANGER),
                        ft.Text("Terminating a contract with funds in escrow may trigger a formal dispute.", size=10, color=MUTED),
                        ft.OutlinedButton("Terminate Contract", icon=ft.icons.CANCEL, on_click=lambda e: _open_terminate_contract_sheet(page)),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Text("Full Stack E-Commerce Development", size=18, weight=ft.FontWeight.W_700),
                        ft.Row(spacing=8, controls=[ft.OutlinedButton("Export PDF"), ft.OutlinedButton("Amendments"), ft.ElevatedButton("Secure Escrow Funding", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/escrow"))]),
                    ],
                ),
                ft.Text("Contract Lifecycle", size=12, weight=ft.FontWeight.W_600),
                steps,
                ft.Container(padding=16, border_radius=12, bgcolor=CARD, border=ft.border.all(1, BORDER), content=table),
                ft.Container(
                    padding=16,
                    border_radius=12,
                    bgcolor=CARD,
                    border=ft.border.all(1, BORDER),
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Terms of Agreement", size=12, weight=ft.FontWeight.W_700),
                            ft.Text("Section 4.2: Intellectual Property Rights", size=11, weight=ft.FontWeight.W_600),
                            ft.Text("All intellectual property created during the term of this contract shall be transferred to the Client upon final payment.", size=10, color=MUTED),
                            ft.Text("Section 7.1: Dispute Resolution", size=11, weight=ft.FontWeight.W_600),
                            ft.Text("Both parties agree to utilize the EscrowFlow Dispute Mediation service as the first point of conflict resolution.", size=10, color=MUTED),
                            ft.TextButton("View Full Legal Document (12 pages)"),
                        ],
                    ),
                ),
            ]),
            ft.Container(width=300, content=right),
        ],
    )

    return shell(page, content, "/contract", nav_items, *session_user(page))


def _open_fund_escrow_sheet(page):
    amount_field = ft.TextField(
        label="Depozit Məbləği (USD)",
        value="$ 1,000.00",
        prefix_icon=ft.Icons.ATTACH_MONEY,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=10,
    )
    method_ref = {"selected": "visa"}

    visa_btn = ft.ElevatedButton(
        "💳  Visa / Master",
        bgcolor=PRIMARY,
        color="white",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )
    paypal_btn = ft.OutlinedButton(
        "🅿  PayPal",
        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8)),
    )

    def select_method(method):
        method_ref["selected"] = method
        visa_btn.bgcolor = PRIMARY if method == "visa" else None
        visa_btn.color = "white" if method == "visa" else TEXT
        paypal_btn.style = ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=8),
            bgcolor=PRIMARY if method == "paypal" else None,
            color="white" if method == "paypal" else TEXT,
        )
        page.update()

    visa_btn.on_click = lambda e: select_method("visa")
    paypal_btn.on_click = lambda e: select_method("paypal")

    def confirm(e):
        amt = (amount_field.value or "").strip()
        if not amt or amt in ("$", "$ 0", "$ 0.00"):
            show_snack(page, "Zəhmət olmasa etibarlı məbləğ daxil edin.", "error")
            return
        bs.open = False
        page.update()
        show_snack(page, f"Escrow hesabı {amt} ilə uğurla dolduruldu! ✓", "success")

    bs = show_bottom_sheet(
        page,
        "Escrow Hesabını Doldur",
        [
            ft.Text("Miqdar", size=12, color=MUTED, weight=ft.FontWeight.W_600),
            amount_field,
            ft.Text("Ödəniş Metodu", size=12, color=MUTED, weight=ft.FontWeight.W_600),
            ft.Row(spacing=10, controls=[visa_btn, paypal_btn]),
            ft.Container(
                padding=10,
                border_radius=8,
                bgcolor="#ECFDF3",
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.SHIELD_OUTLINED, color=SUCCESS, size=16),
                        ft.Text("256-bit AES şifrələmə ilə qorunur", size=11, color=SUCCESS),
                    ],
                ),
            ),
            ft.ElevatedButton(
                "Ödənişi Təsdiqlə",
                bgcolor=PRIMARY,
                color="white",
                height=46,
                expand=True,
                on_click=confirm,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ],
    )


def _open_terminate_contract_sheet(page):
    reason_field = ft.TextField(
        label="Ləğv səbəbi",
        multiline=True,
        min_lines=3,
        border_color=BORDER,
        focused_border_color=DANGER,
        border_radius=10,
    )

    def confirm_terminate(e):
        if not (reason_field.value or "").strip():
            show_snack(page, "Zəhmət olmasa ləğv səbəbini yazın.", "error")
            return
        bs.open = False
        page.update()
        show_snack(page, "Müqavilə ləğv edildi. Arbitraj prosesinə yönləndirilir.", "warning")

    bs = show_bottom_sheet(
        page,
        "Müqaviləni Ləğv Et",
        [
            ft.Container(
                padding=12,
                border_radius=8,
                bgcolor="#FEF2F2",
                border=ft.border.all(1, DANGER),
                content=ft.Row(
                    spacing=8,
                    controls=[
                        ft.Icon(ft.Icons.WARNING_AMBER_ROUNDED, color=DANGER, size=18),
                        ft.Text(
                            "Escrow-da saxlanılan vəsaitlər rəsmi mübahisəyə səbəb ola bilər.",
                            size=11,
                            color=DANGER,
                        ),
                    ],
                ),
            ),
            reason_field,
            ft.Row(
                spacing=10,
                controls=[
                    ft.OutlinedButton(
                        "Ləğv Et",
                        expand=True,
                        on_click=lambda e: _close_bs(page, bs),
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ),
                    ft.ElevatedButton(
                        "Müqaviləni Dayandır",
                        expand=True,
                        bgcolor=DANGER,
                        color="white",
                        height=46,
                        on_click=confirm_terminate,
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
                    ),
                ],
            ),
        ],
    )


def _open_submit_proposal_sheet(page):
    bid_field = ft.TextField(
        label="Təklif Məbləği (USD)",
        value="$ 0.00",
        prefix_icon=ft.Icons.ATTACH_MONEY,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=10,
        expand=True,
    )
    duration_field = ft.TextField(
        label="Müddət (Gün)",
        value="14",
        prefix_icon=ft.Icons.CALENDAR_TODAY_OUTLINED,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=10,
        expand=True,
    )
    letter_field = ft.TextField(
        label="Müraciət Məktubu",
        multiline=True,
        min_lines=3,
        border_color=BORDER,
        focused_border_color=PRIMARY,
        border_radius=10,
    )

    def submit(e):
        if not (bid_field.value or "").strip() or (bid_field.value or "").strip() in ("$", "$ 0", "$ 0.00"):
            show_snack(page, "Zəhmət olmasa etibarlı məbləğ daxil edin.", "error")
            return
        if not (letter_field.value or "").strip():
            show_snack(page, "Müraciət məktubu boş ola bilməz.", "error")
            return
        bs.open = False
        page.update()
        show_snack(page, "Təklifiniz uğurla göndərildi! ✓", "success")

    bs = show_bottom_sheet(
        page,
        "Yeni Təklif Göndər",
        [
            ft.Row(spacing=12, controls=[bid_field, duration_field]),
            letter_field,
            ft.OutlinedButton(
                "Əlavə fayl yüklə",
                icon=ft.Icons.ATTACH_FILE,
                expand=True,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
            ft.ElevatedButton(
                "Təklifi Göndər",
                bgcolor=PRIMARY,
                color="white",
                height=46,
                expand=True,
                on_click=submit,
                style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)),
            ),
        ],
    )


def view_escrow(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    ledger = ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("ID")),
            ft.DataColumn(ft.Text("Type")),
            ft.DataColumn(ft.Text("Contract")),
            ft.DataColumn(ft.Text("Date")),
            ft.DataColumn(ft.Text("Amount")),
            ft.DataColumn(ft.Text("Status")),
        ],
        rows=[
            ft.DataRow(cells=[ft.DataCell(ft.Text("TXN-8821")), ft.DataCell(pill("Fund", color=PRIMARY, bg="#E8F0FF")), ft.DataCell(ft.Text("N/A")), ft.DataCell(ft.Text("2024-05-05")), ft.DataCell(ft.Text("+$2,500.00")), ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("TXN-8822")), ft.DataCell(pill("Release", color=INFO, bg="#E0F2FE")), ft.DataCell(ft.Text("CON-104")), ft.DataCell(ft.Text("2024-05-18")), ft.DataCell(ft.Text("-$1,200.00")), ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("TXN-8823")), ft.DataCell(pill("Release", color=INFO, bg="#E0F2FE")), ft.DataCell(ft.Text("CON-205")), ft.DataCell(ft.Text("2024-05-20")), ft.DataCell(ft.Text("-$500.00")), ft.DataCell(pill("Pending", color=WARNING, bg="#FEF3C7"))]),
            ft.DataRow(cells=[ft.DataCell(ft.Text("TXN-8824")), ft.DataCell(pill("Refund", color=DANGER, bg="#FEE2E2")), ft.DataCell(ft.Text("CON-098")), ft.DataCell(ft.Text("2024-05-21")), ft.DataCell(ft.Text("-$300.00")), ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3"))]),
        ],
    )])

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Fund Escrow Account", size=12, weight=ft.FontWeight.W_700),
                        ft.TextField(label="Deposit Amount (USD)", value="$ 1000"),
                        ft.Text("Payment Method", size=11, color=MUTED),
                        ft.Row(spacing=8, controls=[pill("Visa / Master", color=TEXT, bg="#F1F5F9"), pill("PayPal", color=TEXT, bg="#F1F5F9")]),
                        ft.ElevatedButton(
                            "Confirm Funding",
                            bgcolor=PRIMARY,
                            color="white",
                            on_click=lambda e: _open_fund_escrow_sheet(page),
                        ),
                        ft.Text("Secured by 256-bit AES Encryption.", size=10, color=MUTED),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor="#F8FAFF",
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Release Milestone Payment", size=12, weight=ft.FontWeight.W_700),
                        ft.Text("2 Pending milestones ready for payout", size=10, color=MUTED),
                        ft.OutlinedButton("Review", on_click=lambda e: page.go("/milestones")),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor="#F8FAFF",
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Request Refund", size=12, weight=ft.FontWeight.W_700),
                        ft.Text("Reclaim unused funds from canceled contracts.", size=10, color=MUTED),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Text("Escrow & Financials", size=18, weight=ft.FontWeight.W_700),
                ft.Text("Manage your secured funds and track transaction history across all contracts.", size=12, color=MUTED),
                ft.Row(spacing=12, controls=[
                    stat_card("Current Balance", "$14,250.00", "Available in secured escrow", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED),
                    stat_card("Pending Release", "$3,800.00", "Committed to active milestones", ft.icons.SCHEDULE),
                    stat_card("Total Spent", "$52,490.00", "Lifetime platform expenditure", ft.icons.TRENDING_UP),
                ]),
                ft.Container(padding=16, border_radius=12, bgcolor=CARD, border=ft.border.all(1, BORDER), content=ft.Column(spacing=8, controls=[ft.Text("Transaction Ledger", size=12, weight=ft.FontWeight.W_700), ledger])),
            ]),
            ft.Container(width=300, content=right),
        ],
    )

    return shell(page, content, "/escrow", nav_items, *session_user(page))


def view_milestones(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("Find Projects", ft.icons.SEARCH_OUTLINED, "/proposal"),
        ("Proposals", ft.icons.MAIL_OUTLINED, "/proposal"),
        ("Earnings", ft.icons.ATTACH_MONEY, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    milestones = ft.Column(
        spacing=10,
        controls=[
            milestone_card("Brand Strategy & Voice", "$1,200", "Due 5/15/2024", "approved", 1.0),
            milestone_card("UI/UX Design Mockups", "$2,500", "Due 6/1/2024", "submitted", 0.6, active=True),
            milestone_card("Frontend Core Development", "$3,000", "Due 6/20/2024", "active", 0.4),
            milestone_card("Backend API Integration", "$2,000", "Due 7/10/2024", "pending", 0.2),
            milestone_card("Final Testing & QA", "$1,000", "Due 7/25/2024", "pending", 0.1),
        ],
    )

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Pending Approval", size=12, weight=ft.FontWeight.W_700),
                        ft.Text("Submitted on 5/30/2024", size=10, color=MUTED),
                        ft.Text("DELIVERABLE LINK", size=10, color=MUTED),
                        ft.Text("https://figma.com/project/mockups", size=10, color=PRIMARY),
                        ft.Text("Worker's Notes", size=10, color=MUTED),
                        ft.Text("Updated based on our last sync. Mobile views are in page 2.", size=10),
                        ft.TextField(label="Feedback for Worker", multiline=True, min_lines=3),
                        ft.Row(spacing=8, controls=[ft.OutlinedButton("Reject with Feedback"), ft.ElevatedButton("Approve & Release Funds", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/escrow"))]),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Milestone Details", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Total Amount", size=10, color=MUTED), ft.Text("$2,500", size=11, weight=ft.FontWeight.W_600)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Due Date", size=10, color=MUTED), ft.Text("Jun 1", size=11, weight=ft.FontWeight.W_600)]),
                        ft.Text("Objectives", size=10, color=MUTED),
                        ft.Text("High-fidelity Figma mockups for all core application screens.", size=10),
                        ft.Text("Overall Project Progress", size=10, color=MUTED),
                        ft.ProgressBar(value=0.6, color=PRIMARY, bgcolor="#E8F0FF"),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Text("Milestones & Deliverables", size=18, weight=ft.FontWeight.W_700),
                ft.Text("Track your progress, submit work for review, and manage financial milestones.", size=12, color=MUTED),
                milestones,
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor="#F8FAFF",
                    alignment=CENTER,
                            content=ft.TextButton("Need more stages? Add a custom milestone", on_click=lambda e: page.go("/project-create")),
                ),
            ]),
            ft.Container(width=320, content=right),
        ],
    )

    return shell(page, content, "/milestones", nav_items, *session_user(page))


def milestone_card(title, amount, due, status, progress, active=False):
    return ft.Container(
        padding=14,
        border_radius=12,
        border=ft.border.all(1, PRIMARY if active else BORDER),
        bgcolor=CARD,
        content=ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
            controls=[
                ft.Column(spacing=4, controls=[
                    ft.Text(title, size=12, weight=ft.FontWeight.W_600),
                    ft.Text(due, size=10, color=MUTED),
                    ft.ProgressBar(value=progress, color=PRIMARY, bgcolor="#E8F0FF"),
                ]),
                ft.Column(spacing=4, horizontal_alignment=ft.CrossAxisAlignment.END, controls=[
                    ft.Text(amount, size=12, weight=ft.FontWeight.W_600),
                    pill(status.title(), color=PRIMARY, bg="#E8F0FF"),
                ]),
            ],
        ),
    )


def view_dispute(page):
    nav_items = [
        ("Overview", ft.icons.DASHBOARD_OUTLINED, "/admin"),
        ("Escrow Control", ft.icons.ACCOUNT_BALANCE_OUTLINED, "/escrow-control"),
        ("Disputes", ft.icons.REPORT_OUTLINED, "/dispute"),
        ("User Management", ft.icons.GROUP_OUTLINED, "/user-management"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    conversation = ft.Column(
        spacing=10,
        controls=[
            message_bubble("TechSolutions Inc.", "The deliverables did not match the specifications.", "Oct 24, 2023"),
            message_bubble("Alex Rivera", "I followed all instructions. The issues are due to backend API timing.", "Oct 25, 2023", align="right"),
            message_bubble("Sarah Miller (Admin)", "Please provide commit hashes for the documentation updates.", "Oct 26, 2023"),
        ],
    )

    right = ft.Column(
        spacing=12,
        controls=[
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Financial Context", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Total Contract", size=10, color=MUTED), ft.Text("$12,000.00", size=11)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Locked in Escrow", size=10, color=MUTED), ft.Text("$2,500.00", size=11, color=PRIMARY)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Paid to Date", size=10, color=MUTED), ft.Text("$9,500.00", size=11)]),
                        ft.Row(alignment=ft.MainAxisAlignment.SPACE_BETWEEN, controls=[ft.Text("Platform Fee (3%)", size=10, color=MUTED), ft.Text("-$75.00", size=11, color=DANGER)]),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Dispute Parties", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(spacing=8, controls=[ft.CircleAvatar(radius=14, bgcolor="#E2E8F0"), ft.Text("TechSolutions Inc."), pill("Verified", color=SUCCESS, bg="#ECFDF3")]),
                        ft.Row(spacing=8, controls=[ft.CircleAvatar(radius=14, bgcolor="#E2E8F0"), ft.Text("Alex Rivera"), pill("Top Rated", color=PRIMARY, bg="#E8F0FF")]),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Text("Internal Checklist", size=12, weight=ft.FontWeight.W_700),
                        ft.Checkbox(label="Review Contract Scope"),
                        ft.Checkbox(label="Verify Identity of Parties"),
                        ft.Checkbox(label="Review Artifacts & Evidence"),
                        ft.Checkbox(label="Request Missing Info"),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Column(expand=True, spacing=12, controls=[
                ft.Text("Dispute: DIS-88421", size=18, weight=ft.FontWeight.W_700),
                pill("UNDER REVIEW", color=WARNING, bg="#FEF3C7"),
                ft.Container(
                    padding=14,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor=CARD,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Dispute Reason", size=11, color=MUTED),
                            ft.Text("Deliverables do not match contract specifications.", size=12, weight=ft.FontWeight.W_600),
                            ft.Text("The customer claims the worker failed to provide responsive UI components and complete API documentation.", size=10, color=MUTED),
                        ],
                    ),
                ),
                conversation,
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, BORDER),
                    bgcolor=CARD,
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Administrator Resolution Console", size=12, weight=ft.FontWeight.W_700),
                            ft.TextField(label="Resolution Findings & Details", multiline=True, min_lines=3),
                            ft.Row(spacing=8, controls=[
                                ft.ElevatedButton("Release to Worker", bgcolor=PRIMARY, color="white", on_click=lambda e: page.go("/escrow")),
                                ft.OutlinedButton("Refund to Customer", on_click=lambda e: page.go("/escrow")),
                                ft.OutlinedButton("Split Balance (50/50)", on_click=lambda e: page.go("/escrow")),
                            ]),
                        ],
                    ),
                ),
            ]),
            ft.Container(width=300, content=right),
        ],
    )

    return shell(page, content, "/dispute", nav_items, *session_user(page))


def message_bubble(sender, text, date, align="left"):
    return ft.Container(
        alignment=CENTER_LEFT if align == "left" else CENTER_RIGHT,
        content=ft.Container(
            width=480,
            padding=12,
            border_radius=12,
            bgcolor=CARD,
            border=ft.border.all(1, BORDER),
            content=ft.Column(
                spacing=6,
                controls=[
                    ft.Text(sender, size=11, weight=ft.FontWeight.W_600),
                    ft.Text(text, size=10, color=MUTED),
                    ft.Text(date, size=9, color=MUTED),
                ],
            ),
        ),
    )


def view_user_management(page):
    nav_items = [
        ("Overview", ft.icons.DASHBOARD_OUTLINED, "/admin"),
        ("Escrow Control", ft.icons.ACCOUNT_BALANCE_OUTLINED, "/escrow-control"),
        ("Disputes", ft.icons.REPORT_OUTLINED, "/dispute"),
        ("User Management", ft.icons.GROUP_OUTLINED, "/user-management"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    profile = ft.Container(
        padding=16,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        bgcolor=CARD,
        content=ft.Column(
            spacing=8,
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            controls=[
                ft.CircleAvatar(radius=36, bgcolor="#E2E8F0", content=ft.Text("SJ")),
                ft.Text("Sarah Jenkins", size=13, weight=ft.FontWeight.W_700),
                ft.Text("sarah.j@freelance-expert.com", size=10, color=MUTED),
                pill("WORKER", color=PRIMARY, bg="#E8F0FF"),
                ft.Row(spacing=12, controls=[pill("Rating 4.85", color=SUCCESS, bg="#ECFDF3"), pill("Contracts 32", color=INFO, bg="#E0F2FE")]),
                ft.Divider(),
                ft.Column(spacing=4, controls=[
                    ft.Text("Platform History", size=11, color=MUTED),
                    ft.Text("Registered: Oct 12, 2022", size=10),
                    ft.Text("Dispute Rate: 1.2%", size=10),
                    ft.Text("Account Status: active", size=10),
                ]),
                ft.Divider(),
                ft.Text("Critical Controls", size=11, color=DANGER),
                ft.OutlinedButton("Reset User Password", icon=ft.icons.LOCK_RESET),
                ft.OutlinedButton("View All Contracts", icon=ft.icons.DESCRIPTION_OUTLINED),
                ft.ElevatedButton("Deactivate Account", bgcolor=DANGER, color="white"),
            ],
        ),
    )

    details = ft.Column(
        spacing=12,
        controls=[
            ft.Row(spacing=8, controls=[pill("Public Profile", color=TEXT, bg="#F1F5F9"), pill("Edit Details", color=MUTED, bg="#F1F5F9")]),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Professional Biography", size=12, weight=ft.FontWeight.W_700),
                        ft.Text("Senior Full-Stack Developer with 8+ years of experience specializing in fintech and secure transactions.", size=10, color=MUTED),
                    ],
                ),
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Text("Skills & Technical Expertise", size=12, weight=ft.FontWeight.W_700),
                        ft.Row(spacing=6, controls=[pill("React"), pill("TypeScript"), pill("Node.js"), pill("Financial API Integration"), pill("Smart Contracts"), pill("UI/UX Design")]),
                    ],
                ),
            ),
            ft.Row(
                spacing=12,
                controls=[
                    ft.Container(
                        expand=True,
                        padding=16,
                        border_radius=12,
                        border=ft.border.all(1, BORDER),
                        bgcolor=CARD,
                        content=ft.Column(spacing=6, controls=[ft.Text("Email Address", size=10, color=MUTED), ft.Text("sarah.j@freelance-expert.com", size=11)]),
                    ),
                    ft.Container(
                        expand=True,
                        padding=16,
                        border_radius=12,
                        border=ft.border.all(1, BORDER),
                        bgcolor=CARD,
                        content=ft.Column(spacing=6, controls=[ft.Text("Primary Phone", size=10, color=MUTED), ft.Text("+1 (555) 012-3456", size=11)]),
                    ),
                ],
            ),
            ft.Container(
                padding=16,
                border_radius=12,
                border=ft.border.all(1, BORDER),
                bgcolor=CARD,
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[ft.Text("Recent Project Activity", size=12, weight=ft.FontWeight.W_700), ft.TextButton("View Full History")],
                        ),
                        ft.Row(scroll=ft.ScrollMode.AUTO, controls=[ft.DataTable(
                            columns=[
                                ft.DataColumn(ft.Text("Project / Contract")),
                                ft.DataColumn(ft.Text("Amount")),
                                ft.DataColumn(ft.Text("Status")),
                            ],
                            rows=[
                                ft.DataRow(cells=[ft.DataCell(ft.Text("Enterprise CRM Integration")), ft.DataCell(ft.Text("$4,500")), ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3"))]),
                                ft.DataRow(cells=[ft.DataCell(ft.Text("Real Estate Tokenization UI")), ft.DataCell(ft.Text("$3,200")), ft.DataCell(pill("In Progress", color=INFO, bg="#E0F2FE"))]),
                                ft.DataRow(cells=[ft.DataCell(ft.Text("Payment Gateway Audit")), ft.DataCell(ft.Text("$1,800")), ft.DataCell(pill("Completed", color=SUCCESS, bg="#ECFDF3"))]),
                            ],
                        )]),
                    ],
                ),
            ),
        ],
    )

    content = ft.Row(
        spacing=16,
        controls=[
            ft.Container(width=260, content=profile),
            ft.Column(expand=True, spacing=12, controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(spacing=2, controls=[
                            ft.Text("User Management", size=18, weight=ft.FontWeight.W_700),
                            ft.Text("Admin control panel for individual account lifecycle and reputation.", size=12, color=MUTED),
                        ]),
                        ft.Row(spacing=8, controls=[ft.OutlinedButton("Switch to Customer View", on_click=lambda e: page.go("/dashboard")), ft.ElevatedButton("Add New User", bgcolor=PRIMARY, color="white")]),
                    ],
                ),
                details,
            ]),
        ],
    )

    return shell(page, content, "/user-management", nav_items, *session_user(page))


def view_settings(page):
    nav_items = [
        ("Dashboard", ft.icons.DASHBOARD_OUTLINED, "/dashboard"),
        ("My Projects", ft.icons.FOLDER_OUTLINED, "/projects"),
        ("Contracts", ft.icons.DESCRIPTION_OUTLINED, "/contract"),
        ("Escrow Accounts", ft.icons.ACCOUNT_BALANCE_WALLET_OUTLINED, "/escrow"),
        ("Settings", ft.icons.SETTINGS_OUTLINED, "/settings"),
    ]

    content = ft.Container(
        padding=20,
        border_radius=12,
        border=ft.border.all(1, BORDER),
        bgcolor=CARD,
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                    controls=[
                        ft.Column(
                            spacing=2,
                            controls=[
                                ft.Text("Settings", size=18, weight=ft.FontWeight.W_700),
                                ft.Text("Manage profile preferences, alerts, and security controls.", size=12, color=MUTED),
                            ],
                        ),
                        ft.ElevatedButton("Save Changes", bgcolor=PRIMARY, color="white", on_click=lambda e: show_snack(page, "Parametrlər uğurla saxlandı! ✓", "success")),
                    ],
                ),
                ft.Row(
                    spacing=12,
                    controls=[
                        ft.Container(
                            expand=True,
                            padding=16,
                            border_radius=12,
                            border=ft.border.all(1, BORDER),
                            bgcolor="#F8FAFF",
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Profile Preferences", size=12, weight=ft.FontWeight.W_700),
                                    ft.TextField(label="Display Name", value=page.session.store.get("user_name") or ""),
                                    ft.TextField(label="Work Email", value="alex@example.com"),
                                    ft.TextField(label="Timezone", value="UTC+4"),
                                ],
                            ),
                        ),
                        ft.Container(
                            expand=True,
                            padding=16,
                            border_radius=12,
                            border=ft.border.all(1, BORDER),
                            bgcolor="#F8FAFF",
                            content=ft.Column(
                                spacing=8,
                                controls=[
                                    ft.Text("Notifications", size=12, weight=ft.FontWeight.W_700),
                                    ft.Checkbox(label="Milestone approvals", value=True),
                                    ft.Checkbox(label="Escrow funding alerts", value=True),
                                    ft.Checkbox(label="Dispute activity", value=False),
                                    ft.Checkbox(label="Weekly summary email", value=True),
                                ],
                            ),
                        ),
                    ],
                ),
                ft.Container(
                    padding=16,
                    border_radius=12,
                    border=ft.border.all(1, DANGER),
                    bgcolor="#FFF5F5",
                    content=ft.Column(
                        spacing=8,
                        controls=[
                            ft.Text("Security", size=12, weight=ft.FontWeight.W_700, color=DANGER),
                            ft.Text("Protect your account with password rotation and sign-in review.", size=10, color=MUTED),
                            ft.Row(
                                spacing=8,
                                controls=[
                                    ft.OutlinedButton("Change Password"),
                                    ft.OutlinedButton("Review Sessions"),
                                ],
                            ),
                        ],
                    ),
                ),
            ],
        ),
    )

    return shell(page, content, "/settings", nav_items, *session_user(page))


def router(page):
    init_db()
    raw_route = page.route or "/"
    route = raw_route.split("?")[0]
    uid = page.session.store.get("user_id")
    if route not in PUBLIC_ROUTES and not uid:
        page.go("/")
        return
    if route in PUBLIC_ROUTES and uid:
        page.go("/dashboard")
        return

    route_map = {
        "/": view_login,
        "/register": view_register,
        "/dashboard": view_dashboard,
        "/admin": view_admin_overview,
        "/escrow-control": view_escrow_control,
        "/projects": view_projects,
        "/project-detail": view_project_detail,
        "/project-create": view_project_create,
        "/proposal": view_proposal,
        "/contract": view_contract,
        "/escrow": view_escrow,
        "/milestones": view_milestones,
        "/dispute": view_dispute,
        "/user-management": view_user_management,
        "/settings": view_settings,
    }

    page.clean()
    page.add(route_map.get(route, view_login)(page))
    page.update()


def main(page: ft.Page):
    page.title = "EscrowFlow"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.padding = 0
    page.scroll = ft.ScrollMode.AUTO
    page.bgcolor = BG
    page.on_route_change = lambda e: router(page)

    page.window.width = 1280
    page.window.height = 800
    page.window.resizable = False

    if not page.route:
        page.go("/")
    else:
        router(page)


if __name__ == "__main__":
    ft.run(main, view=ft.AppView.FLET_APP)
