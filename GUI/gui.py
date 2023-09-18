from csv import DictReader, DictWriter, writer as csv_writer
from os.path import isfile
from secrets import choice
from sqlite3 import connect, IntegrityError
from string import ascii_letters, digits
from tkinter import Event, StringVar
from tkinter.constants import CENTER, VERTICAL, HORIZONTAL, END
from tkinter.font import Font
from tkinter.ttk import Treeview, Style, Scrollbar
from typing import Optional, Callable

from darkdetect import theme
from pyperclip import copy
import customtkinter

from config import DB_NAME, VALID_EMAIL_PATTERN
from re import match as regex_match
from Utils.database import get_all_account_names_urls_and_usernames_by_user_id, get_decrypted_account_password, \
    get_account_id_by_account_name_and_user_id, get_user_id_by_email, is_valid_login, create_user, create_account, \
    get_account_name_url_and_username_by_account_id, edit_account, delete_account

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


def set_treeview_to_dark_style(treeview: Treeview):
    style = Style()
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
    style = Style()
    style.map('Dark.Treeview', foreground=fixed_map('foreground', style),
              background=fixed_map('background', style))

    treeview.configure(style='Dark.Treeview')


def set_treeview_to_light_style(treeview: Treeview):
    style = Style()
    style.theme_use('default')

    style.configure("Light.Treeview",
                    rowheight=25,
                    borderwidth=0)

    style.configure("Light.Treeview.Heading",
                    relief="flat")

    # Fix for treeview foreground style not working correctly
    style = Style()
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

        # configure grid layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, rowspan=4, sticky="nsew")

        # Space row number in between the main sidebar buttons and the styling option button
        self.sidebar_frame.grid_rowconfigure(10, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="CustomTkinter", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))


        # Main sidebar buttons
        self.add_account_button = customtkinter.CTkButton(self.sidebar_frame, text='Add account', command=self.add_account_button_event, width=180)
        self.add_account_button.grid(row=1, column=0, padx=20, pady=10)

        self.copy_url_button = customtkinter.CTkButton(self.sidebar_frame, text='Copy selected url', command=self.copy_url_button_event, width=180)
        self.copy_url_button.grid(row=2, column=0, padx=20, pady=10)

        self.copy_username_button = customtkinter.CTkButton(self.sidebar_frame, text='Copy selected username', command=self.copy_username_button_event, width=180)
        self.copy_username_button.grid(row=3, column=0, padx=20, pady=10)

        self.copy_password_button = customtkinter.CTkButton(self.sidebar_frame, text='Copy selected password', command=self.copy_password_button_event, width=180)
        self.copy_password_button.grid(row=4, column=0, padx=20, pady=10)

        self.edit_account_button = customtkinter.CTkButton(self.sidebar_frame, text='Edit selected account', command=self.edit_account_button_event, width=180)
        self.edit_account_button.grid(row=5, column=0, padx=20, pady=10)

        self.delete_account_button = customtkinter.CTkButton(self.sidebar_frame, text='Delete selected account', command=self.delete_account_button_event, width=180)
        self.delete_account_button.grid(row=6, column=0, padx=20, pady=10)

        self.regenerate_password_button = customtkinter.CTkButton(self.sidebar_frame,
                                                                  text='Regenerate selected account password',
                                                                  command=self.regenerate_password_button_event,
                                                                  width=180)

        self.regenerate_password_button._text_label.configure(wraplength=140)

        self.regenerate_password_button.grid(row=7, column=0, padx=20, pady=10)

        self.import_accounts_button = customtkinter.CTkButton(self.sidebar_frame, text='Import accounts', command=self.import_accounts_button_event, width=180)
        self.import_accounts_button.grid(row=8, column=0, padx=20, pady=10)

        self.export_accounts_button = customtkinter.CTkButton(self.sidebar_frame, text='Export accounts', command=self.export_accounts_button_event, width=180)
        self.export_accounts_button.grid(row=9, column=0, padx=20, pady=10)

        # Styling option button
        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=11, column=0, padx=20, pady=(10, 0))

        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(self.sidebar_frame, values=["Light", "Dark", "System"],
                                                                       command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=11, column=0, padx=20, pady=(10, 10))

        # create main entry and button
        self.entry = customtkinter.CTkEntry(self, placeholder_text="Type to search by account name")
        self.entry.grid(row=3, column=1, columnspan=2, padx=(20, 0), pady=(20, 20), sticky="nsew")

        # set default values
        self.appearance_mode_optionemenu.set("System")
        self.treeview_iid_to_full_url_dict = {'': ''}
        self.PASSWORD_HIDDEN_TEXT = 'Click to show password'
        self.tree = Treeview()
        self.tree.bind('<1>', self.item_selected)
        self.entry.bind('<KeyRelease>', self._filter_accounts)
        self.selected_row_info_dict = None
        self.current_treeview_filter = None
        self.current_user = None
        self.current_user_email = None
        self.master_password = None
        self.current_generated_password = None

    def setup_treeview(self, user_id: int, user_email: str, master_password: str):
        self.current_user = user_id
        self.current_user_email = user_email
        self.master_password = master_password

        # define columns
        columns = ('account', 'url', 'username', 'password')

        self.tree.configure(columns=columns, show='headings')

        for col in columns:
            self.tree.column(col, anchor=CENTER, stretch=True)

        # self.tree.column('url', )

        self.tree.grid(row=0, column=1, columnspan=4, sticky="nsew")

        # Styling
        current_appearance_mode = self.appearance_mode_optionemenu.get()

        if current_appearance_mode == 'Dark' or (current_appearance_mode == 'System' and theme()):
            set_treeview_to_dark_style(self.tree)

        # add a scrollbar
        vertical_scrollbar = Scrollbar(self, orient=VERTICAL, command=self.tree.yview)
        horizontal_scrollbar = Scrollbar(self, orient=HORIZONTAL, command=self.tree.xview)
        self.tree.configure(yscrollcommand=vertical_scrollbar.set, xscrollcommand=horizontal_scrollbar.set)
        vertical_scrollbar.grid(row=0, column=5, sticky='ns')
        horizontal_scrollbar.grid(row=2, column=1, columnspan=5, sticky='ew')

        # define headings
        self.tree.heading('account', text='Account')
        self.tree.heading('url', text='Url')
        self.tree.heading('username', text='username')
        self.tree.heading('password', text='Password')

        # collect account data from database
        accounts = get_all_account_names_urls_and_usernames_by_user_id(user_id=user_id, connection=self.connection)

        if not accounts:
            return

        # Setup for getting the longest item width in each column so that the treeview column minwidth can be set
        # properly
        longest_title_item_width = 0
        longest_url_item_width = 0
        longest_username_item_width = 0

        password_item_width = Font().measure(text=self.PASSWORD_HIDDEN_TEXT, displayof=self.tree)

        # add data to the treeview and get the longest item width for each column
        for account in accounts:
            # Setup for shortening potential urls
            if account[1] is None:
                shortened_url = ''
            else:
                shortened_url = account[1][0:20] + '...' if len(account[1]) >= 23 else account[1]

            title_item_width = Font().measure(text=account[0], displayof=self.tree)
            url_item_width = Font().measure(text=shortened_url, displayof=self.tree)
            username_item_width = Font().measure(text=account[2], displayof=self.tree)

            longest_title_item_width = title_item_width if title_item_width > longest_title_item_width else longest_title_item_width
            longest_url_item_width = url_item_width if url_item_width > longest_url_item_width else longest_url_item_width
            longest_username_item_width = username_item_width if username_item_width > longest_username_item_width else longest_username_item_width

            # Pad account name, url, and username with the default hidden text string (actual passwords will replace the
            # default text only once clicked on). Also, use a shortened url for the Treeview and return the full url
            # when copied.
            iid = self.tree.insert('', END, values=(account[0], shortened_url, account[2], self.PASSWORD_HIDDEN_TEXT,))

            if account[1]:
                self.treeview_iid_to_full_url_dict[iid] = account[1]

        self.tree.column('account', minwidth=longest_title_item_width)
        self.tree.column('url', minwidth=longest_url_item_width)
        self.tree.column('username', minwidth=longest_username_item_width)
        self.tree.column('password', minwidth=password_item_width)

    def item_selected(self, event):
        item_id = self.tree.identify("item", event.x, event.y)
        column_id = self.tree.identify("column", event.x, event.y)

        # This early return avoids item selection from happening when selecting the column headings
        if not item_id:
            return

        self.selected_row_info_dict = self.tree.set(item_id)
        self.selected_row_info_dict['iid'] = item_id

        if self.tree.column(column_id)['id'] == 'password':
            password_item = self.tree.set(item_id, column_id)

            if password_item == self.PASSWORD_HIDDEN_TEXT:
                account_id = get_account_id_by_account_name_and_user_id(self.tree.set(item_id, 'account'), self.current_user, self.connection)
                password = get_decrypted_account_password(account_id, master_password=self.master_password, connection=self.connection)
                self.tree.set(item_id, column_id, password)
                self.tree.column(column_id, minwidth=Font().measure(text=password, displayof=self.tree))
            else:
                self.tree.set(item_id, column_id, self.PASSWORD_HIDDEN_TEXT)

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)
        if new_appearance_mode == 'Dark' or (new_appearance_mode == 'System' and theme()):
            set_treeview_to_dark_style(self.tree)
        else:
            set_treeview_to_light_style(self.tree)

    def _filter_accounts(self, event: Optional[Event] = None):
        """
        First removes existing filter, if one exists, before filtering.
        Filtering:
        When the user finishes typing/releases a key in the search bar by the Treeview, the search executes.
        This search filters the Treeview to display Accounts where the Account name contains the string entered into the
        search bar. Sets self.current_treeview_filter to the ids of the detached Treeview items.
        """
        if self.current_treeview_filter:
            for account_and_index in self.current_treeview_filter:
                self.tree.move(item=account_and_index[0], parent='', index=account_and_index[1])

        query = self.entry.get().lower()

        accounts_to_detach_with_index = []

        for account in self.tree.get_children():
            account_name = self.tree.item(account)['values'][0]
            if query not in str(account_name).lower():
                accounts_to_detach_with_index.append((account, self.tree.index(account)))

        for account_and_index in accounts_to_detach_with_index:
            self.tree.detach(account_and_index[0])

        self.current_treeview_filter = accounts_to_detach_with_index

    def add_account_button_event(self):
        width = 320
        height = 150
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        account_name_dialog = customtkinter.CTkInputDialog(title='Account name', text='Enter the account name')
        account_name_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_name = account_name_dialog.get_input()

        existing_account = get_account_id_by_account_name_and_user_id(account_name=account_name, user_id=self.current_user, connection=self.connection)

        if existing_account is not None:
            MessageGUI('An account with this name already exists.', 'Please update that account entry or enter a new account name.')
            return

        account_url_dialog = customtkinter.CTkInputDialog(title='Account url', text='Enter the account\'s url if applicable')
        account_url_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_url = account_url_dialog.get_input()

        account_username_dialog = customtkinter.CTkInputDialog(title='Account username', text='Enter the account\'s username')
        account_username_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_username = account_username_dialog.get_input()

        account_password_dialog = customtkinter.CTkInputDialog(title='Account password', text='Enter the account\'s password')
        account_password_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_password = account_password_dialog.get_input()

        url = account_url if account_url else None

        try:
            account_id = create_account(user_id=self.current_user, master_password=self.master_password,
                                        name=account_name, url=url, username=account_username,
                                        password=account_password, connection=self.connection)
        except ValueError:
            MessageGUI(title='Blank field', message_line_1='Please do not leave the account name, username, or password blank.')
            return

        account = (get_account_name_url_and_username_by_account_id(account_id, self.connection) +
                   (self.PASSWORD_HIDDEN_TEXT, ))

        if url is None:
            shortened_url = ''
        else:
            shortened_url = url[0:20] + '...' if len(url) >= 23 else url

        iid = self.tree.insert(parent='', index='end', values=(account[0], shortened_url, account[2], account[3],))

        if account[1]:
            self.treeview_iid_to_full_url_dict[iid] = account[1]

    def copy_url_button_event(self):
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        iid = self.selected_row_info_dict['iid']
        copy(self.treeview_iid_to_full_url_dict[iid])

    def copy_username_button_event(self):
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        copy(self.selected_row_info_dict['username'])

    def copy_password_button_event(self):
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        password = self.selected_row_info_dict['password']
        account_name = self.selected_row_info_dict['account']
        account_id = get_account_id_by_account_name_and_user_id(account_name, self.current_user, self.connection)
        
        if password == self.PASSWORD_HIDDEN_TEXT:
            password = get_decrypted_account_password(account_id, self.master_password, self.connection)

        copy(password)

    def edit_account_button_event(self):
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        account_id = get_account_id_by_account_name_and_user_id(account_name=self.selected_row_info_dict['account'],
                                                                user_id=self.current_user, connection=self.connection)

        width = 400
        height = 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        account_name_dialog = customtkinter.CTkInputDialog(title='Account name', text='Enter the account name (leave blank or cancel for no change)')
        account_name_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_name = account_name_dialog.get_input()

        existing_account = get_account_id_by_account_name_and_user_id(account_name=account_name, user_id=self.current_user, connection=self.connection)

        if existing_account is not None:
            MessageGUI('An account with this name already exists.', 'Please update that account entry or enter a new account name.')
            return

        account_url_dialog = customtkinter.CTkInputDialog(title='Account url', text='Enter the account\'s url  (leave blank or cancel for no change)')
        account_url_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_url = account_url_dialog.get_input()

        account_username_dialog = customtkinter.CTkInputDialog(title='Account username', text='Enter the account\'s username  (leave blank or cancel for no change)')
        account_username_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_username = account_username_dialog.get_input()

        account_password_dialog = customtkinter.CTkInputDialog(title='Account password', text='Enter the account\'s password  (leave blank or cancel for no change)')
        account_password_dialog.geometry(f'{width}x{height}+{x}+{y}')
        account_password = account_password_dialog.get_input()

        url = account_url if account_url else None

        edit_account(account_id=account_id, master_password=self.master_password, name=account_name, url=url,
                     username=account_username, password=account_password, connection=self.connection)

        account = (get_account_name_url_and_username_by_account_id(account_id, self.connection) +
                   (self.PASSWORD_HIDDEN_TEXT, ))

        old_url = self.selected_row_info_dict['url']

        iid = self.selected_row_info_dict['iid']

        if url is None:
            shortened_url = old_url
        else:
            shortened_url = url[0:20] + '...' if len(url) >= 23 else url
            self.treeview_iid_to_full_url_dict[iid] = account[1]

        self.tree.set(item=iid, column='account', value=account[0])
        self.tree.set(item=iid, column='url', value=shortened_url)
        self.tree.set(item=iid, column='username', value=account[2])
        self.tree.set(item=iid, column='password', value=account[3])

        self.selected_row_info_dict = self.tree.set(iid)
        self.selected_row_info_dict['iid'] = iid

    def delete_account_button_event(self):
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        account_id = get_account_id_by_account_name_and_user_id(account_name=self.selected_row_info_dict['account'],
                                                                user_id=self.current_user, connection=self.connection)

        width = 400
        height = 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        delete_account_dialog = customtkinter.CTkInputDialog(title='Delete account',
                                                                  text='Enter \"yes\" if you are sure you want to delete the selected account info.')
        delete_account_dialog.geometry(f'{width}x{height}+{x}+{y}')
        user_confirmation = delete_account_dialog.get_input()

        if not user_confirmation or user_confirmation.lower() != 'yes':
            MessageGUI(title='Account info not deleted', message_line_1=f'Your account info was NOT deleted!')
            return

        account_id = get_account_id_by_account_name_and_user_id(account_name=self.selected_row_info_dict['account'],
                                                                user_id=self.current_user, connection=self.connection)

        delete_account(account_id=account_id, connection=self.connection)

        # Remove from treeview
        iid = self.selected_row_info_dict['iid']

        self.tree.delete(iid)

        self.selected_row_info_dict = None

        MessageGUI(title='Account info deleted', message_line_1=f'Your account info was successfully deleted!')

    def regenerate_password_button_event(self):
        """
        Generate a random, 15 character, multi-case, alphanumeric password using the python secrets library.
        Assign this password to the selected account row if the user confirms they have changed the actual
        account password accordingly, otherwise do not change the password.
        """
        if not self.selected_row_info_dict:
            MessageGUI(title='No account selected', message_line_1='No account is currently selected.',
                       message_line_2='Please select an account first and try again.')
            return

        alphabet = ascii_letters + digits
        while True:
            password = ''.join(choice(alphabet) for i in range(15))
            if (
                    sum(c.islower() for c in password) >= 3
                    and sum(c.isupper() for c in password) >= 3
                    and sum(c.isdigit() for c in password) >= 3
            ):
                break

        self.current_generated_password = password

        MessageGUI(title='New password',
                   message_line_1='Your new password is displayed below. Please copy it to your account if possible.',
                   copyable_message=password, uncloseable=True, command=self._regenerate_password_button_event_confirm)

    def _regenerate_password_button_event_confirm(self):
        """
        Assign the generated password to the selected account row if the user confirms they have changed the actual
        account password accordingly, otherwise do not change the password.
        """
        width = 400
        height = 180
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        regenerate_password_dialog = customtkinter.CTkInputDialog(title='Regenerate password',
                                                                  text='Enter \"yes\" if you are sure you want to regenerate and have successfully copied over the password.')
        regenerate_password_dialog.geometry(f'{width}x{height}+{x}+{y}')
        user_confirmation = regenerate_password_dialog.get_input()

        if not user_confirmation or user_confirmation.lower() != 'yes':
            MessageGUI(title='New password not saved',
                       message_line_1=f'Your account password was NOT changed!')
            return

        account_id = get_account_id_by_account_name_and_user_id(account_name=self.selected_row_info_dict['account'],
                                                                user_id=self.current_user, connection=self.connection)

        edit_account(account_id=account_id, master_password=self.master_password,
                     password=self.current_generated_password, connection=self.connection)

        iid = self.selected_row_info_dict['iid']

        self.tree.set(item=iid, column='password', value=self.PASSWORD_HIDDEN_TEXT)

        self.selected_row_info_dict = self.tree.set(iid)
        self.selected_row_info_dict['iid'] = iid

        MessageGUI(title='New password saved',
                   message_line_1=f'Your account password was successfully changed!')

    def import_accounts_button_event(self):
        MessageGUI(title='Loading', message_line_1='The import might take a while if there are many entries.',
                   message_line_2='Please do not close the program.', command=self.import_accounts_button_event_confirm)

    def import_accounts_button_event_confirm(self):
        csv_file_original = customtkinter.filedialog.askopenfile(title='Select accounts CSV file',
                                                   filetypes=(('.csv (Microsoft Excel Comma Separated Values File)',
                                                               '*.csv'),))

        if not csv_file_original:
            return

        csv_file_original.close()

        if csv_file_original:
            with open(file=csv_file_original.name, mode='r', encoding='utf-8-sig') as csv_file:
                accounts_that_could_not_be_added = []
                reader = DictReader(csv_file)

                if not (
                        reader.fieldnames.__contains__('name')
                        and reader.fieldnames.__contains__('username')
                        and reader.fieldnames.__contains__('password')
                ):
                    MessageGUI(title='Import error', message_line_1='Please format the CSV file to have at '
                                                                    'least these exact column names - url column is '
                                                                    'optional: ',
                               message_line_2='name, url, username, password')
                    return

                for row in reader:
                    name = row['name']
                    url = row['url'] if reader.fieldnames.__contains__('url') else None
                    username = row['username']
                    password = row['password']

                    try:
                        account_id = create_account(user_id=self.current_user, master_password=self.master_password,
                                                    name=name, url=url, username=username,
                                                    password=password, connection=self.connection)

                        account = (get_account_name_url_and_username_by_account_id(account_id, self.connection) +
                                   (self.PASSWORD_HIDDEN_TEXT,))

                        if url is None:
                            shortened_url = ''
                        else:
                            shortened_url = url[0:20] + '...' if len(url) >= 23 else url

                        iid = self.tree.insert(parent='', index='end',
                                               values=(account[0], shortened_url, account[2], account[3],))

                        if account[1]:
                            self.treeview_iid_to_full_url_dict[iid] = account[1]

                    except (ValueError, IntegrityError):
                        # If all are empty, skip/only consider an Account not addable if there is at least
                        # one field value (we want to ignore empty csv rows)
                        if not (name == '' and url == '' and username == '' and password == ''):
                            accounts_that_could_not_be_added.append({'name': name, 'url': url, 'username': username,
                                                                     'password': password})

                csv_file.close()

            # If some Accounts could not be added due to missing required fields or duplicate names
            accounts_that_could_not_be_added_length = len(accounts_that_could_not_be_added)

            if accounts_that_could_not_be_added_length > 0 and accounts_that_could_not_be_added[0]:

                # Setup for not overwriting or adding to the same file, but making multiple
                not_added_counter = 1
                not_added_filename = "not_added{}.csv"
                while isfile(not_added_filename.format(f'_{not_added_counter}')):
                    not_added_counter += 1
                filename = not_added_filename.format(f'_{not_added_counter}')

                MessageGUI(title='Some accounts could not be added',
                           message_line_1=f'{accounts_that_could_not_be_added_length} accounts could not be added '
                                               f'due to missing info or duplicate account names.',
                           message_line_2=f'These have been saved in {filename}. Please search the manager for '
                                               'the entries with the corresponding account name and edit them to '
                                               'have the correct information.')

                with open(filename, 'w') as destination_file:
                    header_writer = csv_writer(destination_file)
                    header_writer.writerow(('name', 'url', 'username', 'password', ))

                    writer = DictWriter(destination_file, fieldnames=['name', 'url', 'username', 'password'],
                                            lineterminator='\n')

                    writer.writerows(accounts_that_could_not_be_added)

                    destination_file.close()

    def export_accounts_button_event(self):
        MessageGUI(title='Loading', message_line_1='The export might take a while if there are many entries.',
                   message_line_2='Please do not close the program.', command=self.export_accounts_button_event_confirm)

    def export_accounts_button_event_confirm(self):
        accounts_to_export = [{}]

        accounts = self.tree.get_children()

        if len(accounts) == 0:
            MessageGUI(title='No accounts', message_line_1='There are no accounts to export.')
            return

        for account in accounts:
            item = self.tree.item(account)
            account_name = item['values'][0]
            account_url = item['values'][1]
            account_username = item['values'][2]
            account_password = item['values'][3]

            if account_password == self.PASSWORD_HIDDEN_TEXT:
                account_id = get_account_id_by_account_name_and_user_id(account_name, self.current_user, self.connection)
                account_password = get_decrypted_account_password(account_id, self.master_password, self.connection)

            accounts_to_export.append({'name': account_name, 'url': account_url, 'username': account_username,
                                       'password': account_password})

        filename = f'exported_passwords_{self.current_user_email}.csv'

        with open(filename, 'w', encoding='utf-8-sig') as destination_file:
            header_writer = csv_writer(destination_file)
            header_writer.writerow(('name', 'url', 'username', 'password',))

            writer = DictWriter(destination_file, fieldnames=['name', 'url', 'username', 'password'],
                                    lineterminator='\n')

            writer.writerows(accounts_to_export)

            destination_file.close()

            MessageGUI(title='Passwords successfully exported', message_line_1=f'Your passwords have been exported to '
                                                                               f'{filename}.')


class LoginGUI(customtkinter.CTkToplevel):
    def __init__(self, parent: App):
        super().__init__()
        self.parent = parent
        self.connection = self.parent.connection

        self.grab_set()
        self.title('Login')
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
        self.bind('<Return>', self._login)

    def _login(self, event: Optional[Event] = None):
        self.entered_email = str.lower(self.user_entry.get())
        self.entered_password = self.user_pass.get()

        if not self.entered_email:
            MessageGUI(title='No Email', message_line_1='Please enter your email.')
        elif not regex_match(pattern=VALID_EMAIL_PATTERN, string=self.entered_email):
            MessageGUI(title='Invalid email', message_line_1='Please enter a valid email address.')
            return
        elif not self.entered_password:
            MessageGUI(title='No password', message_line_1='Please enter your password.')

        if not self.entered_email or not self.entered_password:
            return

        user_id = get_user_id_by_email(self.entered_email, self.connection)

        if not user_id:
            SignupGUI(self)

        elif is_valid_login(self.entered_email, self.entered_password, self.connection):
            self.parent.setup_treeview(user_id, self.entered_email, self.entered_password)
            self.parent.deiconify()
            self.destroy()
        else:
            MessageGUI(title='Wrong password', message_line_1='Please check your password.')


class SignupGUI(customtkinter.CTkToplevel):
    def __init__(self, parent: LoginGUI):
        super().__init__()
        self.parent = parent

        self.attributes('-topmost', True)
        self.grab_set()
        self.title('Signup')
        width = 500
        height = 250

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        self.geometry(f'{width}x{height}+{x}+{y}')

        prompt_1 = 'There is no account with this email.'
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

        self.parent.parent.setup_treeview(user_id, self.parent.entered_email, self.parent.entered_password)
        self.parent.parent.deiconify()
        self.parent.destroy()
        self.destroy()


class MessageGUI(customtkinter.CTkToplevel):
    def __init__(self, title: str, message_line_1: str, message_line_2: Optional[str] = None,
                 copyable_message: Optional[str] = None, command: Optional[Callable] = None, uncloseable: bool = False):
        super().__init__()
        self.lift()
        self.grid_propagate(False)
        self.grab_set()
        self.title(title)

        self.uncloseable = uncloseable

        self.protocol("WM_DELETE_WINDOW", self._close)


        label = customtkinter.CTkLabel(master=self, text=message_line_1, font=('', 14))
        label.pack(pady=(12, 0), padx=20)

        if message_line_2:
            label_2 = customtkinter.CTkLabel(master=self, text=message_line_2, font=('', 14))
            label_2.pack(pady=(12, 0), padx=20)

        if copyable_message:
            text_variable = StringVar(master=self, value=copyable_message)
            # entry = Entry(master=self, textvariable=text_variable, style='TLabel', font=('', 14), justify='center', state='readonly')
            entry = customtkinter.CTkEntry(master=self, textvariable=text_variable, state='readonly', font=('', 14))
            entry.pack(pady=(12, 0), padx=20)

        self.ok_button = customtkinter.CTkButton(master=self, text='Ok', command=self._ok)
        self.ok_button.pack(pady=(24, 20), padx=20)

        if command:
            self.ok_button.configure(command=lambda: [self._ok(), command()])

        self.update()

        width = self.winfo_width()
        height = self.winfo_height()

        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()

        x = ((screen_width / 2) - (width / 2)).__trunc__()
        y = ((screen_height / 2) - (height / 2)).__trunc__()

        self.geometry(f'{x}+{y}')

        self.bind('<Return>', self._ok)

    def _ok(self, event: Optional[Event] = None):
        self.destroy()

    def _close(self):
        if self.uncloseable:
            return
        else:
            self.destroy()


if __name__ == "__main__":
    app = App()

    app.mainloop()
