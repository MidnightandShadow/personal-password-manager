from sqlite3 import connect
import tkinter as tk
from tkinter import ttk
from tkinter.constants import CENTER

import pyperclip
import customtkinter
from tkinter import messagebox

from config import DB_NAME
from Utils.database import get_all_account_names_and_logins_by_user_id, get_decrypted_account_password, \
    get_account_id_by_account_name_and_user_id, get_user_id_by_email, get_login_password_by_user_id, is_valid_login

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"


def fixed_map(option, style):
    # Fix for setting text colour for Tkinter 8.6.9
    # From: https://core.tcl.tk/tk/info/509cafafae
    #
    # Returns the style map for 'option' with any styles starting with
    # ('!disabled', '!selected', ...) filtered out.

    # style.map() returns an empty list for missing options, so this
    # should be future-safe.
    return [elm for elm in style.map('Treeview', query_opt=option) if
            elm[:2] != ('!disabled', '!selected')]

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.connection = connect(DB_NAME)
        self.login_gui = LoginGUI(self)

        # configure window
        self.title("Personal Password Manager.py")

        width = 1280
        height = 720

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        self.geometry(f'{width}x{height}+{x}+{y}')

        # configure grid layout (4x4)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(4, weight=1)
        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CustomTkinter", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))
        self.sidebar_button_1 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_1.grid(row=1, column=0, padx=20, pady=10)
        self.sidebar_button_2 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_2.grid(row=2, column=0, padx=20, pady=10)
        self.sidebar_button_3 = customtkinter.CTkButton(self.sidebar_frame, command=self.sidebar_button_event)
        self.sidebar_button_3.grid(row=3, column=0, padx=20, pady=10)
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))
        self.scaling_label = customtkinter.CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.scaling_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["80%", "90%", "100%", "110%", "120%"],
                                                               command=self.change_scaling_event)
        self.scaling_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 20))

        # create main entry and button
        self.entry = customtkinter.CTkEntry(self, placeholder_text="CTkEntry")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        self.main_button_1.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # set default values
        self.sidebar_button_3.configure(state="disabled", text="Disabled CTkButton")
        self.appearance_mode_optionemenu.set("Dark")
        self.scaling_optionemenu.set("100%")
        self.PASSWORD_HIDDEN_TEXT = 'Click to show password'
        self.tree = ttk.Treeview()
        self.tree.bind('<1>', self.item_selected)

    def setup_treeview(self):
        # define columns
        columns = ('account', 'login', 'password')

        self.tree.configure(columns=columns, show='headings')

        for col in columns:
            self.tree.column(col, anchor=CENTER, stretch=True)

        self.tree.grid(row=0, column=1, columnspan=4, sticky="nsew")

        # Styling
        style = ttk.Style()

        style.theme_use("default")

        style.configure("Treeview",
                        background="#2a2d2e",
                        foreground="white",
                        rowheight=25,
                        fieldbackground="#343638",
                        bordercolor="#343638",
                        borderwidth=0)
        style.map('Treeview', background=[('selected', '#22559b')])

        style.configure("Treeview.Heading",
                        background="#565b5e",
                        foreground="white",
                        relief="flat")
        style.map("Treeview.Heading",
                  background=[('active', '#3484F0')])

        # Fix for treeview foreground style not working correctly
        style = ttk.Style()
        style.map('Treeview', foreground=fixed_map('foreground', style),
                  background=fixed_map('background', style))

        # add a scrollbar
        vertical_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        horizontal_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        vertical_scrollbar.grid(row=0, column=5, sticky='ns')
        horizontal_scrollbar.grid(row=2, column=1, columnspan=5, sticky='ew')

        # define headings
        self.tree.heading('account', text='Account')
        self.tree.heading('login', text='Login')
        self.tree.heading('password', text='Password')


        # collect account data from database
        accounts_name_and_login = get_all_account_names_and_logins_by_user_id(user_id=1, connection=self.connection)

        # Pad account name and username with the default hidden text string (actual passwords will replace the default
        # text only once clicked on)
        accounts = [x + (self.PASSWORD_HIDDEN_TEXT,) for x in accounts_name_and_login]

        # Setup for getting the longest item width in each column so that the treeview column minwidth can be set
        # properly
        longest_title_item_width = 0
        longest_login_item_width = 0
        longest_password_item_width = 0

        # add data to the treeview and get the longest item width for each column
        for account in accounts:
            title_item_width = tk.font.Font().measure(text=account[0], displayof=self.tree)
            login_item_width = tk.font.Font().measure(text=account[1], displayof=self.tree)
            password_item_width = tk.font.Font().measure(text=account[2], displayof=self.tree)

            longest_title_item_width = title_item_width if title_item_width > longest_title_item_width else longest_title_item_width
            longest_login_item_width = login_item_width if login_item_width > longest_login_item_width else longest_login_item_width
            longest_password_item_width = password_item_width if password_item_width > longest_password_item_width else longest_password_item_width

            self.tree.insert('', tk.END, values=account)

        self.tree.column('account', minwidth=longest_title_item_width)
        self.tree.column('login', minwidth=longest_login_item_width)
        self.tree.column('password', minwidth=longest_password_item_width)

    def item_selected(self, event):
        current_user = get_user_id_by_email(email=self.login_gui.username, connection=self.connection)
        item_id = self.tree.identify("item", event.x, event.y)
        column_id = self.tree.identify("column", event.x, event.y)

        # This early return avoids any action from happening when selecting the column headings
        if not item_id:
            return

        if self.tree.column(column_id)['id'] == 'login':
            login_item = self.tree.set(item_id, column_id)
            pyperclip.copy(login_item)

        if self.tree.column(column_id)['id'] == 'password':
            password_item = self.tree.set(item_id, column_id)

            if password_item == self.PASSWORD_HIDDEN_TEXT:
                account_id = get_account_id_by_account_name_and_user_id(self.tree.set(item_id, 'account'), current_user, self.connection)
                password = get_decrypted_account_password(account_id, master_password=self.login_gui.password, connection=self.connection)
                self.tree.set(item_id, column_id, password)
                self.tree.column(column_id, minwidth=tk.font.Font().measure(text=password, displayof=self.tree))
                pyperclip.copy(password)
            else:
                self.tree.set(item_id, column_id, self.PASSWORD_HIDDEN_TEXT)

    def open_input_dialog_event(self):
        dialog = customtkinter.CTkInputDialog(text="Type in a number:", title="CTkInputDialog")
        print("CTkInputDialog:", dialog.get_input())

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)

    def sidebar_button_event(self):
        print("sidebar_button click")


class LoginGUI(customtkinter.CTkToplevel):
    def __init__(self, parent: App):
        super().__init__()
        self.parent = parent
        self.connection = self.parent.connection

        self.parent.withdraw()

        self.username = None
        self.password = None

        # configure window
        self.title("Personal Password Manager.py")

        width = 400
        height = 400

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        self.geometry(f'{width}x{height}+{x}+{y}')

        frame = customtkinter.CTkFrame(master=self)
        frame.pack(pady=20, padx=40, fill='both', expand=True)

        label = customtkinter.CTkLabel(master=frame, text='Personal Password Manager', font=('', 20))
        label.pack(pady=(36, 0), padx=10)

        self.user_entry = customtkinter.CTkEntry(master=frame, placeholder_text="Username")
        self.user_entry.pack(pady=(48, 0), padx=10)

        self.user_pass = customtkinter.CTkEntry(master=frame, placeholder_text="Password", show="*")
        self.user_pass.pack(pady=(12, 0), padx=10)

        button = customtkinter.CTkButton(master=frame, text='Login', command=self._login)
        button.pack(pady=(36, 36), padx=10)

        self.protocol("WM_DELETE_WINDOW", self.quit)

    def _login(self):
        entered_username = self.user_entry.get()
        entered_password = self.user_pass.get()

        user_id = get_user_id_by_email(entered_username, self.connection)

        if not user_id:
            messagebox.showwarning(title='Wrong username', message='Please check your username')
        elif is_valid_login(entered_username, entered_password, self.connection):
            self.username = entered_username
            self.password = entered_password
            self.parent.setup_treeview()
            self.parent.deiconify()
            self.destroy()
        else:
            messagebox.showwarning(title='Wrong password', message='Please check your password')


if __name__ == "__main__":
    app = App()

    app.mainloop()
