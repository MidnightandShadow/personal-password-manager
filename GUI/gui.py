from sqlite3 import connect
import tkinter as tk
from tkinter import ttk
from tkinter.constants import CENTER

import darkdetect
from pyperclip import copy
import customtkinter
from tkinter import messagebox

from config import DB_NAME
from Utils.database import get_all_account_names_and_usernames_by_user_id, get_decrypted_account_password, \
    get_account_id_by_account_name_and_user_id, get_user_id_by_email, is_valid_login, create_user, create_account, \
    get_account_name_and_username_by_account_id

customtkinter.set_appearance_mode('System')  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme('blue')  # Themes: "blue" (standard), "green", "dark-blue"


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


def set_treeview_to_dark_style(treeview: ttk.Treeview):
    style = ttk.Style()
    style.theme_use('default')

    style.configure("Dark.Treeview",
                    background="#2a2d2e",
                    foreground="white",
                    rowheight=25,
                    fieldbackground="#343638",
                    bordercolor="#343638",
                    borderwidth=0)
    style.map('Dark.Treeview', background=[('selected', '#22559b')])

    style.configure("Dark.Treeview.Heading",
                    background="#565b5e",
                    foreground="white",
                    relief="flat")
    style.map("Dark.Treeview.Heading",
              background=[('active', '#3484F0')])

    # Fix for treeview foreground style not working correctly
    style = ttk.Style()
    style.map('Dark.Treeview', foreground=fixed_map('foreground', style),
              background=fixed_map('background', style))

    treeview.configure(style='Dark.Treeview')


def set_treeview_to_light_style(treeview: ttk.Treeview):
    style = ttk.Style()
    style.theme_use('default')

    style.configure("Light.Treeview",
                    rowheight=25,
                    borderwidth=0)

    style.configure("Light.Treeview.Heading",
                    relief="flat")

    # Fix for treeview foreground style not working correctly
    style = ttk.Style()
    style.map('Light.Treeview', foreground=fixed_map('foreground', style),
              background=fixed_map('background', style))

    treeview.configure(style='Light.Treeview')


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

        self.add_account_button = customtkinter.CTkButton(self.sidebar_frame, text='Add account', command=self.add_account_button_event, width=180)
        self.add_account_button.grid(row=1, column=0, padx=20, pady=10)

        self.copy_username_button = customtkinter.CTkButton(self.sidebar_frame, text='Copy selected username', command=self.copy_username_button_event, width=180)
        self.copy_username_button.grid(row=2, column=0, padx=20, pady=10)

        self.copy_password_button = customtkinter.CTkButton(self.sidebar_frame, text='Copy selected password', command=self.copy_password_button_event, width=180)
        self.copy_password_button.grid(row=3, column=0, padx=20, pady=10)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=5, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=6, column=0, padx=20, pady=(10, 10))

        # create main entry and button
        self.entry = customtkinter.CTkEntry(self, placeholder_text="CTkEntry")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        self.main_button_1 = customtkinter.CTkButton(master=self, fg_color="transparent", border_width=2, text_color=("gray10", "#DCE4EE"))
        self.main_button_1.grid(row=3, column=3, padx=(20, 20), pady=(20, 20), sticky="nsew")

        # set default values
        self.appearance_mode_optionemenu.set("System")
        self.PASSWORD_HIDDEN_TEXT = 'Click to show password'
        self.tree = ttk.Treeview()
        self.tree.bind('<1>', self.item_selected)
        self.selected_row_info_dict = None
        self.current_user = None
        self.master_password = None

    def setup_treeview(self, user_id: int, master_password: str):
        self.current_user = user_id
        self.master_password = master_password

        # define columns
        columns = ('account', 'username', 'password')

        self.tree.configure(columns=columns, show='headings')

        for col in columns:
            self.tree.column(col, anchor=CENTER, stretch=True)

        self.tree.grid(row=0, column=1, columnspan=4, sticky="nsew")

        # Styling
        current_appearance_mode = self.appearance_mode_optionemenu.get()

        if current_appearance_mode == 'Dark' or (current_appearance_mode == 'System' and darkdetect.theme()):
            set_treeview_to_dark_style(self.tree)

        # add a scrollbar
        vertical_scrollbar = ttk.Scrollbar(self, orient=tk.VERTICAL, command=self.tree.yview)
        horizontal_scrollbar = ttk.Scrollbar(self, orient=tk.HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        vertical_scrollbar.grid(row=0, column=5, sticky='ns')
        horizontal_scrollbar.grid(row=2, column=1, columnspan=5, sticky='ew')

        # define headings
        self.tree.heading('account', text='Account')
        self.tree.heading('username', text='username')
        self.tree.heading('password', text='Password')


        # collect account data from database
        accounts_name_and_username = get_all_account_names_and_usernames_by_user_id(user_id=user_id, connection=self.connection)

        if not accounts_name_and_username:
            return

        # Pad account name and username with the default hidden text string (actual passwords will replace the default
        # text only once clicked on)
        accounts = [x + (self.PASSWORD_HIDDEN_TEXT,) for x in accounts_name_and_username]

        # Setup for getting the longest item width in each column so that the treeview column minwidth can be set
        # properly
        longest_title_item_width = 0
        longest_username_item_width = 0
        longest_password_item_width = 0

        # add data to the treeview and get the longest item width for each column
        for account in accounts:
            title_item_width = tk.font.Font().measure(text=account[0], displayof=self.tree)
            username_item_width = tk.font.Font().measure(text=account[1], displayof=self.tree)
            password_item_width = tk.font.Font().measure(text=account[2], displayof=self.tree)

            longest_title_item_width = title_item_width if title_item_width > longest_title_item_width else longest_title_item_width
            longest_username_item_width = username_item_width if username_item_width > longest_username_item_width else longest_username_item_width
            longest_password_item_width = password_item_width if password_item_width > longest_password_item_width else longest_password_item_width

            self.tree.insert('', tk.END, values=account)

        self.tree.column('account', minwidth=longest_title_item_width)
        self.tree.column('username', minwidth=longest_username_item_width)
        self.tree.column('password', minwidth=longest_password_item_width)

    def item_selected(self, event):
        item_id = self.tree.identify("item", event.x, event.y)
        column_id = self.tree.identify("column", event.x, event.y)

        # This early return avoids item selection from happening when selecting the column headings
        if not item_id:
            return

        self.selected_row_info_dict = self.tree.set(item_id)

        if self.tree.column(column_id)['id'] == 'password':
            password_item = self.tree.set(item_id, column_id)

            if password_item == self.PASSWORD_HIDDEN_TEXT:
                account_id = get_account_id_by_account_name_and_user_id(self.tree.set(item_id, 'account'), self.current_user, self.connection)
                password = get_decrypted_account_password(account_id, master_password=self.master_password, connection=self.connection)
                self.tree.set(item_id, column_id, password)
                self.tree.column(column_id, minwidth=tk.font.Font().measure(text=password, displayof=self.tree))
            else:
                self.tree.set(item_id, column_id, self.PASSWORD_HIDDEN_TEXT)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        if new_appearance_mode == 'Dark' or (new_appearance_mode == 'System' and darkdetect.theme()):
            set_treeview_to_dark_style(self.tree)
        else:
            set_treeview_to_light_style(self.tree)

    def add_account_button_event(self):
        account_username = ''
        account_password = ''

        account_name_dialog = customtkinter.CTkInputDialog(title='Account name', text='Enter the account name or url')
        account_name = account_name_dialog.get_input()

        if account_name:
            account_username_dialog = customtkinter.CTkInputDialog(title='Account username', text='Enter the account\'s username')
            account_username = account_username_dialog.get_input()

        if account_username:
            account_password_dialog = customtkinter.CTkInputDialog(title='Account password', text='Enter the account\'s password')
            account_password = account_password_dialog.get_input()

        account_id = create_account(user_id=self.current_user, master_password=self.master_password,
                                    name=account_name, username=account_username,
                                    password=account_password, connection=self.connection)

        account_name_and_username = get_account_name_and_username_by_account_id(account_id, self.connection)
        account_name_username_and_hidden_password = account_name_and_username + (self.PASSWORD_HIDDEN_TEXT, )

        self.tree.insert(parent='', index='end', values=account_name_username_and_hidden_password)

    def copy_username_button_event(self):
        if not self.selected_row_info_dict:
            return

        copy(self.selected_row_info_dict['username'])

    def copy_password_button_event(self):
        if not self.selected_row_info_dict:
            return

        password = self.selected_row_info_dict['password']
        account_name = self.selected_row_info_dict['account']
        account_id = get_account_id_by_account_name_and_user_id(account_name, self.current_user, self.connection)
        
        if password == self.PASSWORD_HIDDEN_TEXT:
            password = get_decrypted_account_password(account_id, self.master_password, self.connection)

        copy(password)


class LoginGUI(customtkinter.CTkToplevel):
    def __init__(self, parent: App):
        super().__init__()
        self.parent = parent
        self.connection = self.parent.connection

        self.parent.withdraw()

        self.email = None
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

        self.user_entry = customtkinter.CTkEntry(master=frame, placeholder_text="email")
        self.user_entry.pack(pady=(48, 0), padx=10)

        self.user_pass = customtkinter.CTkEntry(master=frame, placeholder_text="Password", show="*")
        self.user_pass.pack(pady=(12, 0), padx=10)

        button = customtkinter.CTkButton(master=frame, text='Login / Signup', command=self._login)
        button.pack(pady=(36, 36), padx=10)

        self.protocol("WM_DELETE_WINDOW", self.quit)

    def _login(self):
        self.entered_email = self.user_entry.get()
        self.entered_password = self.user_pass.get()

        if not self.entered_email:
            messagebox.showwarning(title='No email', message='Please enter your email')
        elif not self.entered_password:
            messagebox.showwarning(title='No password', message='Please enter your password')

        if not self.entered_email or not self.entered_password:
            return

        user_id = get_user_id_by_email(self.entered_email, self.connection)

        if not user_id:
            SignupGUI(self)

        elif is_valid_login(self.entered_email, self.entered_password, self.connection):
            self.parent.setup_treeview(user_id, self.entered_password)
            self.parent.deiconify()
            self.destroy()
        else:
            messagebox.showwarning(title='Wrong password', message='Please check your password')


class SignupGUI(customtkinter.CTkToplevel):
    def __init__(self, parent: LoginGUI):
        super().__init__()
        self.parent = parent

        self.attributes('-topmost', True)
        width = 500
        height = 250

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        self.geometry(f'{width}x{height}+{x}+{y}')

        prompt_1 = 'This email does not exist.'
        prompt_2 = 'Click Cancel to re-enter your email or click Sign up to create an account.'

        label = customtkinter.CTkLabel(master=self, text=prompt_1, font=('', 14))
        label.pack(pady=(12, 0), padx=10)

        label_2 = customtkinter.CTkLabel(master=self, text=prompt_2, font=('', 14),
                                         wraplength=(customtkinter.CTkFont().measure(prompt_2) / 1.5).__trunc__())
        label_2.pack(pady=(12, 0), padx=10)

        self.cancel_button = customtkinter.CTkButton(master=self, text='Cancel', command=self._cancel)
        self.cancel_button.pack(pady=(24, 0), padx=10)

        self.signup_button = customtkinter.CTkButton(master=self, text='Sign up', command=self._signup)
        self.signup_button.pack(pady=(12, 0), padx=10)

    def _cancel(self):
        self.destroy()

    def _signup(self):

        user_id = create_user(email=self.parent.entered_email, password=self.parent.entered_password,
                              connection=self.parent.connection)

        self.parent.parent.setup_treeview(user_id, self.parent.entered_password)
        self.parent.parent.deiconify()
        self.parent.destroy()
        self.destroy()


if __name__ == "__main__":
    app = App()

    app.mainloop()
