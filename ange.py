import tkinter as tk
from tkinter import messagebox, filedialog
from tkinter import ttk 
import csv
import os
from datetime import datetime, date, timedelta
from collections import defaultdict 
import random 

FIELDNAMES = ['ID', 'Name', 'Birthday', 'LMP', 'Sitio', 'Health_Status', 'Records', 'PWD_Type'] 
SITIO_CHOICES = ["IBABA", "CENTRO", "SILANGAN", "KANLURAN"] 
DISEASE_CHOICES = ["NORMAL", "Diabetes", "Hypertension", "COPD", "Pneumonia", "TB (Tuberculosis)", "Asthma", "Other"] 
PWD_CHOICES = ["NOT PWD", "Physical Disability", "Intellectual Disability", "Mental Disability", "Visual Impairment", "Hearing Impairment", "Speech Impairment", "Multiple Disabilities"] 

patient_registry = []
next_id = 1 

THEMES = {
    'Light': {'PRIMARY': '#007BFF', 'SECONDARY': '#495057', 'BACKGROUND': '#F8F9FA', 'CONTENT_BG': '#FFFFFF', 'SIDEBAR_BG': '#E9ECEF', 'SIDEBAR_HOVER': '#CED4DA', 'INPUT_BG': '#F0F3F4', 'WARNING': '#FFC107', 'TEXT_COLOR': '#212529', 'CARD_BG': '#D4E6F1'},
    'Dark': {'PRIMARY': '#17A2B8', 'SECONDARY': '#FFFFFF', 'BACKGROUND': '#212529', 'CONTENT_BG': '#343A40', 'SIDEBAR_BG': '#495057', 'SIDEBAR_HOVER': '#6C757D', 'INPUT_BG': '#495057', 'WARNING': '#FFC107', 'TEXT_COLOR': '#F8F9FA', 'CARD_BG': '#34495E'},
    'Gray_Classic': {'PRIMARY': '#5D6D7E', 'SECONDARY': '#2C3E50', 'BACKGROUND': '#F8F8F8', 'CONTENT_BG': '#FFFFFF', 'SIDEBAR_BG': '#EEEEEE', 'SIDEBAR_HOVER': '#D6DBDF', 'INPUT_BG': '#F5F5F5', 'WARNING': '#FFC107', 'TEXT_COLOR': '#2C3E50', 'CARD_BG': '#EBEDEF'}
}
CURRENT_THEME_NAME = 'Light'
GLOBAL_FONT_SIZE = 11 

USER_CREDENTIALS = {"bhw": "bhw123"}
LOGGED_IN_USER = None 

def calculate_age(bday_str):
    try:
        bday = datetime.strptime(bday_str, "%Y-%m-%d").date()
        today = date.today() 
        return today.year - bday.year - ((today.month, today.day) < (bday.month, bday.day))
    except ValueError: return -1 

def calculate_edd_and_schedule(lmp_str):
    if not lmp_str or lmp_str.upper() == "N/A": return "N/A", []
    try:
        lmp = datetime.strptime(lmp_str, "%Y-%m-%d").date()
        edd = lmp + timedelta(days=280) 
        today = date.today()
        
        # New Rule: Check if LMP is too recent (less than 4 weeks)
        # If LMP is too recent, it means the patient is not yet confirmed pregnant 
        # based on LMP alone, or the LMP entry is incorrect.
        if today - lmp < timedelta(weeks=4):
             return "LMP too recent (Not Pregnant)", [] # Use a clear status for the schedule/EDD
        
        if edd < today: return edd.strftime("%Y-%m-%d"), ["Delivered (Post-Partum)"]
        
        schedule = []; current_date = lmp + timedelta(weeks=12) 
        while current_date <= edd:
            week = (current_date - lmp).days // 7
            status = "🔜" if current_date >= today else "✅"
            schedule.append(f"{status} {current_date.strftime('%Y-%m-%d')} (Week {week})")
            
            # Scheduling logic
            if week >= 36: current_date += timedelta(weeks=1) 
            elif week >= 28: current_date += timedelta(weeks=2) 
            else: current_date += timedelta(weeks=4) 
            
        return edd.strftime("%Y-%m-%d"), [s for s in schedule if s.startswith('🔜')]
    except ValueError: return "Invalid LMP Date", []

def load_data():
    global patient_registry, next_id
    DATA_FILE = 'bhw_patient_registry_auto.csv'
    patient_registry = []
    if not os.path.exists(DATA_FILE): return
    
    try:
        with open(DATA_FILE, mode='r', newline='', encoding='utf-8') as file:
            reader = csv.DictReader(file, fieldnames=FIELDNAMES)
            header_skipped = False
            for row in reader:
                if not header_skipped: header_skipped = True; continue
                
                # Data cleanup/migration for older entries
                if 'PWD_Type' not in row or not row['PWD_Type']: row['PWD_Type'] = 'NOT PWD'
                if 'LMP' not in row or not row['LMP']: row['LMP'] = 'N/A' 
                
                row['Records'] = row['Records'].split(';') if row['Records'] else []
                row['ID'] = int(row['ID'])
                patient_registry.append(row)
                
            if patient_registry: 
                next_id = max(p['ID'] for p in patient_registry) + 1
                
    except Exception as e: 
        messagebox.showerror("Data Error", f"ERROR loading data: {e}.")

def save_data():
    default_filename = f"BHW_Patient_Registry_{datetime.now().strftime('%Y%m%d')}.csv"
    filename = filedialog.asksaveasfilename(defaultextension=".csv", initialfile=default_filename, filetypes=[("CSV files (Excel Compatible)", "*.csv")])
    if not filename: return 
    
    try:
        with open(filename, mode='w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=FIELDNAMES); writer.writeheader()
            for patient in patient_registry:
                patient_to_save = patient.copy()
                patient_to_save['Records'] = ';'.join(patient_to_save['Records'])
                if 'PWD_Type' not in patient_to_save: patient_to_save['PWD_Type'] = 'NOT PWD'
                writer.writerow(patient_to_save)
                
        messagebox.showinfo("Success", f"Data successfully saved to:\n{filename}")
    except Exception as e: 
        messagebox.showerror("Save Error", f"ERROR saving data: {e}")

def find_patient_by_id_or_name(search_term):
    search_term = search_term.strip()
    if not search_term: return None
    search_term_upper = search_term.upper()
    
    try:
        search_id = int(search_term)
        for p in patient_registry:
            if p['ID'] == search_id: return p
    except ValueError: pass
    
    for p in patient_registry:
        if p['Name'].upper().startswith(search_term_upper): return p
        
    return None

class LoginScreen:
    def __init__(self, master, on_login_success):
        self.master = master
        self.on_login_success = on_login_success
        
        # Initial setup 
        master.title("BHW Connect: Secure Login")
        master.geometry("400x350")
        master.resizable(False, False)
        
        self.frame = tk.Frame(master, bg='#FFFFFF')
        self.frame.pack(expand=True, fill='both')
        
        self._create_widgets()

    def _create_widgets(self):
        tk.Label(self.frame, text="BHW Connect", font=("Segoe UI", 24, "bold"), bg='#FFFFFF', fg='#007BFF').pack(pady=(20, 5))
        tk.Label(self.frame, text="Patient Registry Login", font=("Segoe UI", 12), bg='#FFFFFF', fg='#495057').pack(pady=(0, 20))
        
        # Username
        tk.Label(self.frame, text="Username:", font=("Segoe UI", 10, "bold"), bg='#FFFFFF', fg='#212529', anchor='w').pack(fill='x', padx=50, pady=(5, 0))
        self.username_entry = tk.Entry(self.frame, font=("Segoe UI", 11), relief=tk.FLAT, bg='#E9ECEF', fg='#212529')
        self.username_entry.pack(fill='x', padx=50, ipady=5)
        
        # Password
        tk.Label(self.frame, text="Password:", font=("Segoe UI", 10, "bold"), bg='#FFFFFF', fg='#212529', anchor='w').pack(fill='x', padx=50, pady=(10, 0))
        self.password_entry = tk.Entry(self.frame, show="*", font=("Segoe UI", 11), relief=tk.FLAT, bg='#E9ECEF', fg='#212529')
        self.password_entry.pack(fill='x', padx=50, ipady=5)
        
        # Login Button
        tk.Button(self.frame, text="🔑 LOG IN", command=self._check_login, bg='#007BFF', fg='white', font=("Segoe UI", 12, "bold"), relief=tk.FLAT, pady=8).pack(fill='x', padx=50, pady=20)
        
        # Bind <Return> key to login
        self.master.bind('<Return>', lambda event: self._check_login())
        
    def _check_login(self):
        global LOGGED_IN_USER
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if username in USER_CREDENTIALS and USER_CREDENTIALS[username] == password:
            LOGGED_IN_USER = username
            self.frame.destroy()
            self.master.unbind('<Return>') # Unbind key after successful login
            self.on_login_success() 
        else:
            messagebox.showerror("Login Failed", "Invalid username or password. Please try again.")
            self.password_entry.delete(0, tk.END) 

# ===============================================
# 4. GUI APPLICATION (FRONTEND LOGIC) 
# ===============================================

class BHWApp:
    def __init__(self, master, show_login_callback): 
        self.master = master
        self.show_login_callback = show_login_callback
        
        # Initial setup
        master.title("BHW Connect: Patient Registry")
        master.geometry("1000x700") 
        
        load_data() 
        self.apply_styles() 
        self._setup_layout() 
        self.show_home_view()
        
        # State variables
        self.current_patient = None
        self.current_patient_profile = None 

    def get_colors(self):
        colors = THEMES[CURRENT_THEME_NAME]
        # Override specific colors for consistency in Light theme
        if CURRENT_THEME_NAME == 'Light':
            colors.update({'PRIMARY': '#007BFF', 'SECONDARY': '#5D6D7E', 'TEXT_COLOR': '#333333', 'INPUT_BG': '#FFFFFF', 'SIDEBAR_HOVER': '#E6E6E6', 'HIGHLIGHT_BORDER': '#CED4DA'})
        return colors

    def apply_styles(self):
        colors = self.get_colors()
        style = ttk.Style()
        style.theme_use('default') 
        self.master.configure(bg=colors['BACKGROUND'])
        
        # TNotebook Styles
        style.configure('TNotebook', background=colors['BACKGROUND'], borderwidth=0)
        style.configure('TNotebook.Tab', background=colors['SIDEBAR_BG'], foreground=colors['SECONDARY'], font=('Segoe UI', GLOBAL_FONT_SIZE, 'bold'), borderwidth=0)
        style.map('TNotebook.Tab', background=[('selected', colors['PRIMARY']), ('active', colors['SIDEBAR_HOVER'])], foreground=[('selected', 'white'), ('active', colors['PRIMARY'])]) 
        
        # TFrame (Custom)
        style.configure('Custom.TFrame', background=colors['CONTENT_BG'])
        
        # Treeview Styles
        style.configure("Treeview.Heading", font=('Segoe UI', GLOBAL_FONT_SIZE + 1, 'bold'), background=colors['PRIMARY'], foreground='white')
        style.configure("Treeview", font=('Segoe UI', GLOBAL_FONT_SIZE), rowheight=25, background=colors['CONTENT_BG'], foreground=colors['TEXT_COLOR'])
        style.map("Treeview", background=[('selected', colors['PRIMARY'])], foreground=[('selected', 'white')])

        # Re-draw UI elements if they exist
        if hasattr(self, 'sidebar'):
            current_title = self.master.title().split(': ')[-1].split('/')[0].strip()
            self.sidebar.destroy(); self.content_frame.destroy(); self._setup_layout()
            
            # Re-draw current view 
            view_map = {'Home': self.show_home_view, 'Add': self.show_add_patient, 'Update': self.show_update_record, 'View All': lambda: self.show_master_list(False), 'Senior': lambda: self.show_master_list(True), 'Pregnant': self.show_pregnant_scheduler, 'PWD': self.show_pwd_list, 'Profile': self.show_view_patient, 'Health': self.generate_report}
            # Simple check to see if the view exists and re-render it
            if current_title in view_map: view_map[current_title]()


    def _setup_layout(self):
        colors = self.get_colors()
        self.sidebar = tk.Frame(self.master, width=220, bg=colors['SIDEBAR_BG'])
        self.sidebar.pack(side="left", fill="y")
        
        self.content_frame = tk.Frame(self.master, bg=colors['CONTENT_BG'])
        self.content_frame.pack(side="right", fill="both", expand=True, padx=20, pady=20)
        
        self._create_sidebar_buttons()
        
    def _add_sidebar_divider(self, label):
        colors = self.get_colors()
        icon_map = {'DATA ENTRY': '✍️ ', 'RECORDS': '🗂️ ', 'ACTIONS': '⚙️ '}
        icon = icon_map.get(label.split(' / ')[0], '')
        
        tk.Frame(self.sidebar, height=1, bg=colors['SIDEBAR_HOVER']).pack(fill='x', padx=10, pady=(5, 5))
        tk.Label(self.sidebar, text=f"{icon}{label}", font=("Segoe UI", 8, "bold"), bg=colors['SIDEBAR_BG'], fg=colors['SECONDARY'], anchor='w').pack(fill='x', padx=15)
        tk.Frame(self.sidebar, height=1, bg=colors['SIDEBAR_HOVER']).pack(fill='x', padx=10, pady=(0, 5))

    def _add_sidebar_button(self, text, command, bg_color=None, fg_color=None):
        colors = self.get_colors()
        default_bg = colors['SIDEBAR_BG']
        default_fg = colors['SECONDARY']
        
        bg_color = bg_color if bg_color else default_bg
        fg_color = fg_color if fg_color else default_fg
        
        button_frame = tk.Frame(self.sidebar, bg=bg_color)
        button_frame.pack(fill='x', padx=5, pady=2)
        
        btn = tk.Button(button_frame, text=text, command=command, font=("Segoe UI", 11), bg=bg_color, fg=fg_color, relief=tk.FLAT, activebackground=colors['SIDEBAR_HOVER'], activeforeground=colors['PRIMARY'], anchor='w', padx=15, pady=8)
        btn.pack(fill='x')
        
        # Hover effect
        btn.bind("<Enter>", lambda e, b=btn, bc=bg_color: b.config(bg=colors['SIDEBAR_HOVER'], fg=colors['PRIMARY']))
        btn.bind("<Leave>", lambda e, b=btn, bc=bg_color: b.config(bg=bc, fg=default_fg))

    def _create_sidebar_buttons(self):
        colors = self.get_colors()
        
        # Logo/Title
        tk.Label(self.sidebar, text="BHW Connect", font=("Segoe UI", 18, "bold"), bg=colors['SIDEBAR_BG'], fg=colors['PRIMARY'], pady=15).pack(fill='x', padx=10)
        tk.Frame(self.sidebar, height=1, bg=colors['SIDEBAR_HOVER']).pack(fill='x', padx=10, pady=(0, 10))

        # Button List (Theme setting removed)
        buttons = [
            ("🏠 Home / Dashboard", self.show_home_view, None, None, False),
            ("DATA ENTRY", None, None, None, True), 
            ("  Add Resident", self.show_add_patient, None, None, False), 
            ("  Update Record", self.show_update_record, None, None, False),
            ("RECORDS / REPORTS", None, None, None, True),
            ("👥 View All Residents", lambda: self.show_master_list(is_senior_view=False), None, None, False), 
            ("👴 View Senior Citizens", lambda: self.show_master_list(is_senior_view=True), None, None, False), 
            ("♿ View PWD Master List", self.show_pwd_list, None, None, False), 
            ("🤰 Pregnant Scheduler", self.show_pregnant_scheduler, None, None, False),
            ("🔎 View Profile", self.show_view_patient, None, None, False),
            ("📈 Health Reports", self.generate_report, None, None, False),
            ("SETTINGS / ACTIONS", None, None, None, True),
            ("💾 SAVE DATA", save_data, colors['WARNING'], 'black', False), 
            ("🚪 LOG OUT", self.logout, '#DC3545', 'white', False)
        ]
        
        for text, command, bg, fg, is_divider in buttons:
            if is_divider: 
                self._add_sidebar_divider(text)
            elif command: 
                self._add_sidebar_button(text, command, bg, fg)
        
        # Space below Log Out button
        tk.Frame(self.sidebar, height=20, bg=colors['SIDEBAR_BG']).pack(fill='x', padx=10) 
        
    def _apply_theme_setting(self):
        global CURRENT_THEME_NAME
        self.apply_styles()

    def logout(self): 
        global LOGGED_IN_USER
        if messagebox.askyesno("Confirm Logout", "Are you sure you want to log out?"):
            LOGGED_IN_USER = None
            self.master.withdraw()
            self.show_login_callback() 

    def _switch_view(self, title):
        colors = self.get_colors()
        for widget in self.content_frame.winfo_children(): widget.destroy()
        
        tk.Label(self.content_frame, text=title, font=("Segoe UI", 20, "bold"), bg=colors['CONTENT_BG'], fg=colors['PRIMARY'], pady=15).pack(fill='x', padx=10)
        tk.Frame(self.content_frame, height=2, bg=colors['SIDEBAR_HOVER']).pack(fill='x', padx=10, pady=(0, 15))
        self.master.title(f"BHW Connect: {title.strip()}")
        
    # --- Form Helper ---
    def _create_form_field(self, parent, label_text, row_num, column_num, columnspan=1, is_combobox=False, choices=None):
        colors = self.get_colors(); font_style = ("Segoe UI", GLOBAL_FONT_SIZE + 1); HIGHLIGHT_BORDER = '#CED4DA' 
        
        # Label placement (sticky='w' for alignment)
        tk.Label(parent, text=label_text, bg=colors['CONTENT_BG'], font=("Segoe UI", 10, "bold"), fg=colors['TEXT_COLOR'], anchor='w').grid(row=row_num, column=column_num, sticky='w', pady=(15, 0), padx=20, columnspan=columnspan) 

        if is_combobox and choices is not None:
            var = tk.StringVar(parent)
            var.set(choices[0] if choices else "")
            
            style = ttk.Style()
            style.configure('Custom.TCombobox', fieldbackground=colors['INPUT_BG'], selectbackground=colors['PRIMARY'], selectforeground='white', bordercolor=HIGHLIGHT_BORDER) 
            
            widget = ttk.Combobox(parent, textvariable=var, values=choices, state='readonly', font=font_style, style='Custom.TCombobox')
            # Input field placement (sticky='ew' for expansion/alignment)
            widget.grid(row=row_num+1, column=column_num, sticky='ew', pady=(5, 15), padx=20, columnspan=columnspan) 
            return widget, var
        else:
            # Entry field setup
            entry = tk.Entry(parent, relief=tk.FLAT, bd=1, bg=colors['INPUT_BG'], font=font_style, insertbackground=colors['PRIMARY'], highlightthickness=1, highlightbackground=HIGHLIGHT_BORDER, highlightcolor=colors['PRIMARY'], fg=colors['TEXT_COLOR'])
            # Input field placement (sticky='ew' for expansion/alignment)
            entry.grid(row=row_num+1, column=column_num, sticky='ew', pady=(5, 15), padx=20, columnspan=columnspan) 
            return entry
    
    # --- SHOW ADD PATIENT VIEW (FIXED ALIGNMENT) ---
    def show_add_patient(self):
        colors = self.get_colors(); self._switch_view("✍️ Add New Resident / Household")
        notebook = ttk.Notebook(self.content_frame, padding=10); notebook.pack(pady=10, padx=20, fill='both', expand=True)

        tab1 = ttk.Frame(notebook, style='Custom.TFrame'); notebook.add(tab1, text='👤 Personal Information')
        
        # Grid Weights for Alignment - 50/50 split
        tab1.grid_columnconfigure(0, weight=1) # Column 0: Left Half
        tab1.grid_columnconfigure(1, weight=1) # Column 1: Right Half
        
        # Centralized field creation using a list of tuples
        # Format: (Label, Colspan, Attribute Name, Default Text, Choices)
        fields = [
            # Row 0 (row 0 & 1): Name (Left) and Birthday (Right)
            ("Full Name (First, Middle, Last):", 1, 'name_entry', None, None), 
            ("Birthday (YYYY-MM-DD):", 1, 'bday_entry', "YYYY-MM-DD", None),  
            
            # Row 2 (row 2 & 3): Sitio (Left) and PWD (Right)
            ("Sitio/Zone:", 1, 'sitio_var', None, SITIO_CHOICES),            
            ("PWD Status/Type:", 1, 'pwd_var', None, PWD_CHOICES),            
            
            # Row 4 (row 4 & 5): LMP (Full width)
            ("Last Menstrual Period (LMP) Date:", 2, 'lmp_entry', "YYYY-MM-DD or N/A", None) 
        ]

        # Loop to Create and Align Fields
        for i, (label, span, attr_name, default_text, choices) in enumerate(fields):
            
            # Logic to determine grid row (0, 2, or 4)
            if i < 2: 
                current_row = 0 
            elif i < 4: 
                current_row = 2
            else: 
                current_row = 4
            
            # Logic to determine grid column and span
            col = i % 2 if span == 1 else 0
            col_span = span

            # Create the widget (Entry or Combobox)
            if choices:
                _, var = self._create_form_field(tab1, label, current_row, col, columnspan=col_span, is_combobox=True, choices=choices)
                setattr(self, attr_name, var)
            else:
                entry = self._create_form_field(tab1, label, current_row, col, columnspan=col_span)
                setattr(self, attr_name, entry)
                if default_text: entry.insert(0, default_text)
        
        # Tab 2: Health Conditions
        tab2 = ttk.Frame(notebook, style='Custom.TFrame', padding=(30, 20)); notebook.add(tab2, text='🩺 Health Conditions')
        tab2.grid_columnconfigure(0, weight=1); tab2.grid_columnconfigure(1, weight=1) 
        tk.Label(tab2, text="Primary Illnesses / Health Conditions:", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 13, "bold")).grid(row=0, column=0, sticky='w', pady=(0, 15), padx=5, columnspan=2)
        
        self.disease_vars = {}
        for i, disease in enumerate(DISEASE_CHOICES):
            var = tk.BooleanVar(tab2); self.disease_vars[disease] = var
            cb = tk.Checkbutton(tab2, text=disease, variable=var, bg=colors['CONTENT_BG'], anchor='w', fg=colors['TEXT_COLOR'], selectcolor=colors['PRIMARY'], font=("Segoe UI", 12), activebackground=colors['CONTENT_BG'], activeforeground=colors['TEXT_COLOR'])
            cb.grid(row=i // 2 + 1, column=i % 2, sticky='w', padx=20, pady=5)
            
        tk.Button(self.content_frame, text="✅ SAVE NEW RESIDENT", command=self._add_patient_action, bg='#2ECC71', fg='white', font=("Segoe UI", 14, "bold"), relief=tk.FLAT, pady=12).pack(pady=(10, 20), padx=20, fill='x')

    def _add_patient_action(self):
        global next_id
        name = self.name_entry.get().strip().upper()
        bday = self.bday_entry.get().strip()
        lmp = self.lmp_entry.get().strip().upper()
        sitio = self.sitio_var.get().upper()
        pwd_type = self.pwd_var.get()
        
        if not name or name == "N/A": messagebox.showerror("Validation Error", "Name is required."); return
        
        # --- Birthday Validation ---
        if bday == "YYYY-MM-DD": bday = 'N/A'
        if bday != 'N/A' and calculate_age(bday) == -1: 
            messagebox.showerror("Validation Error", "Invalid Birthday format. Use YYYY-MM-DD."); return
        
        # --- LMP Validation and Check (NEW LOGIC) ---
        if lmp in ["YYYY-MM-DD OR N/A", "N/A"]: 
            lmp = 'N/A'
        elif lmp != 'N/A':
            try:
                lmp_date = datetime.strptime(lmp, "%Y-%m-%d").date()
                today = date.today()
                
                if lmp_date > today:
                    messagebox.showerror("Validation Error", "LMP Date cannot be in the future."); return
                
                # Check if LMP is too recent (less than 4 weeks)
                if today - lmp_date < timedelta(weeks=4):
                    # Warning/Advice for BHW
                    if not messagebox.askyesno("LMP Warning", 
                                                f"The LMP date ({lmp}) is less than 4 weeks ago.\n"
                                                f"It is too soon to confirm pregnancy via LMP alone.\n"
                                                f"Do you want to save the record WITHOUT the LMP date? (Set LMP to N/A)"):
                        return # Cancel action
                    
                    lmp = 'N/A' # Set to N/A if BHW confirms it's too early/incorrect
                
            except ValueError: 
                messagebox.showerror("Validation Error", "Invalid LMP Date format. Use YYYY-MM-DD."); return

        health_statuses = [disease for disease, var in self.disease_vars.items() if var.get()]
        health_status_str = ", ".join(health_statuses) if health_statuses else "N/A"
        
        # Save action
        new_patient = {
            'ID': next_id, 
            'Name': name, 
            'Birthday': bday, 
            'LMP': lmp, 
            'Sitio': sitio, 
            'Health_Status': health_status_str, 
            'Records': [f"REGISTRATION: {datetime.now().strftime('%Y-%m-%d')} - Initial Record Created."], 
            'PWD_Type': pwd_type 
        }
        patient_registry.append(new_patient)
        next_id += 1
        
        messagebox.showinfo("Success", f"Resident {name} (ID: {new_patient['ID']}) successfully added!")
        self.show_home_view() 

    # --- UPDATE RECORD ---
    def show_update_record(self):
        # ... (Same as before) ...
        colors = self.get_colors()
        self._switch_view("✍️ Update Resident Records / Status")
        
        search_frame = tk.Frame(self.content_frame, bg=colors['CONTENT_BG'])
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(search_frame, text="Search Resident (ID or Name):", bg=colors['CONTENT_BG'], fg=colors['SECONDARY'], font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.update_search_entry = tk.Entry(search_frame, relief=tk.FLAT, bg=colors['INPUT_BG'], font=("Segoe UI", 11))
        self.update_search_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5, ipady=3)
        
        tk.Button(search_frame, text="Search", command=self._search_patient_for_update, bg=colors['PRIMARY'], fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        self.patient_info_frame = tk.Frame(self.content_frame, bg=colors['CONTENT_BG'])
        self.patient_info_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
    def _search_patient_for_update(self):
        colors = self.get_colors()
        for widget in self.patient_info_frame.winfo_children(): widget.destroy()
        search_term = self.update_search_entry.get()
        self.current_patient = find_patient_by_id_or_name(search_term)
        
        if not self.current_patient:
            tk.Label(self.patient_info_frame, text="Patient Not Found.", bg=colors['CONTENT_BG'], fg='#DC3545', font=("Segoe UI", 12, "bold")).pack(pady=20)
            return

        info = self.current_patient
        age = calculate_age(info.get('Birthday', 'N/A'))
        edd, _ = calculate_edd_and_schedule(info.get('LMP', 'N/A'))
        
        tk.Label(self.patient_info_frame, text=f"Patient ID: {info['ID']} | Name: {info['Name']}", bg=colors['CONTENT_BG'], fg=colors['PRIMARY'], font=("Segoe UI", 14, "bold")).pack(pady=(10, 5))
        tk.Label(self.patient_info_frame, text=f"Age: {age} | Sitio: {info['Sitio']} | Health: {info['Health_Status']}", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11)).pack(pady=(0, 5))
        tk.Label(self.patient_info_frame, text=f"LMP: {info.get('LMP', 'N/A')} | EDD: {edd} | PWD Type: {info.get('PWD_Type', 'NOT PWD')}", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11)).pack(pady=(0, 15))

        update_area = tk.LabelFrame(self.patient_info_frame, text="Add New Record / Update Status", font=("Segoe UI", 12, "bold"), bg=colors['CONTENT_BG'], fg=colors['SECONDARY'], padx=15, pady=10)
        update_area.pack(fill='x', padx=10, pady=10)
        
        # New Record
        tk.Label(update_area, text="New Record Description:", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 10, "bold")).pack(fill='x', pady=(5, 0))
        self.new_record_entry = tk.Entry(update_area, relief=tk.FLAT, bg=colors['INPUT_BG'], font=("Segoe UI", 11))
        self.new_record_entry.pack(fill='x', ipady=3, pady=(0, 10))
        
        # New Health Status
        tk.Label(update_area, text="Update Health Status:", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 10, "bold")).pack(fill='x', pady=(5, 0))
        self.new_health_status_var = tk.StringVar(update_area)
        self.new_health_status_var.set(info['Health_Status'].split(', ')[0] if info['Health_Status'] and info['Health_Status'] != 'N/A' else DISEASE_CHOICES[0])
        ttk.Combobox(update_area, textvariable=self.new_health_status_var, values=DISEASE_CHOICES, state='readonly').pack(fill='x', ipady=3, pady=(0, 10))

        # New PWD Status
        tk.Label(update_area, text="Update PWD Status:", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 10, "bold")).pack(fill='x', pady=(5, 0))
        self.new_pwd_var = tk.StringVar(update_area)
        self.new_pwd_var.set(info.get('PWD_Type', PWD_CHOICES[0]))
        ttk.Combobox(update_area, textvariable=self.new_pwd_var, values=PWD_CHOICES, state='readonly').pack(fill='x', ipady=3, pady=(0, 10))
        
        # New LMP Update
        tk.Label(update_area, text="Update LMP Date (YYYY-MM-DD or N/A):", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 10, "bold")).pack(fill='x', pady=(5, 0))
        self.new_lmp_entry = tk.Entry(update_area, relief=tk.FLAT, bg=colors['INPUT_BG'], font=("Segoe UI", 11))
        self.new_lmp_entry.insert(0, info.get('LMP', 'N/A'))
        self.new_lmp_entry.pack(fill='x', ipady=3, pady=(0, 10))
        
        tk.Button(update_area, text="💾 SAVE UPDATE", command=self._save_patient_update, bg=colors['PRIMARY'], fg='white', font=("Segoe UI", 11, "bold"), relief=tk.FLAT).pack(fill='x', pady=5)
        
    def _save_patient_update(self):
        if not self.current_patient: messagebox.showerror("Error", "No patient selected for update."); return
        
        new_record_text = self.new_record_entry.get().strip()
        new_status = self.new_health_status_var.get()
        new_pwd_type = self.new_pwd_var.get() 
        new_lmp = self.new_lmp_entry.get().strip().upper()

        if not new_record_text: messagebox.showerror("Error", "Please enter a record description."); return
        
        # --- Update LMP Validation Check (Same logic as Add Resident) ---
        validated_lmp = new_lmp
        if new_lmp in ["N/A", ""]:
            validated_lmp = 'N/A'
        else:
            try:
                lmp_date = datetime.strptime(new_lmp, "%Y-%m-%d").date()
                today = date.today()
                
                if lmp_date > today:
                    messagebox.showerror("Validation Error", "LMP Date cannot be in the future."); return
                
                if today - lmp_date < timedelta(weeks=4):
                    if not messagebox.askyesno("LMP Warning", 
                                                f"The new LMP date ({new_lmp}) is less than 4 weeks ago.\n"
                                                f"It is too soon to confirm pregnancy via LMP alone.\n"
                                                f"Do you want to save the record WITHOUT the new LMP date? (Set LMP to N/A)"):
                        return
                    validated_lmp = 'N/A'
                    
            except ValueError:
                 messagebox.showerror("Validation Error", "Invalid LMP Date format. Use YYYY-MM-DD."); return

        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M')
        self.current_patient['Records'].insert(0, f"{timestamp}: {new_record_text}")
        self.current_patient['Health_Status'] = new_status
        self.current_patient['PWD_Type'] = new_pwd_type
        self.current_patient['LMP'] = validated_lmp # Update with validated LMP

        messagebox.showinfo("Success", f"Records for {self.current_patient['Name']} successfully updated!")
        self.show_update_record() 

    # --- HOME VIEW (Same as before) ---
    def show_home_view(self):
        colors = self.get_colors()
        self._switch_view("🏠 Home / Dashboard")
        
        total_patients = len(patient_registry)
        senior_count = sum(1 for p in patient_registry if calculate_age(p.get('Birthday', '1900-01-01')) >= 60)
        pregnant_count = sum(1 for p in patient_registry if p.get('LMP') and p['LMP'] != 'N/A' and calculate_edd_and_schedule(p['LMP'])[0] not in ["N/A", "Invalid LMP Date", "Delivered (Post-Partum)", "LMP too recent (Not Pregnant)"])
        pwd_count = sum(1 for p in patient_registry if p.get('PWD_Type', 'NOT PWD') != 'NOT PWD') 

        card_frame = tk.Frame(self.content_frame, bg=colors['CONTENT_BG'])
        card_frame.pack(pady=20, fill='x')
        
        def create_card(parent, label_text, value, bg_color, value_fg_color):
            card = tk.Frame(parent, bg=bg_color, relief=tk.RAISED, bd=2, padx=15, pady=15)
            card.pack(side=tk.LEFT, padx=15, expand=True, fill='x')
            tk.Label(card, text=label_text, font=("Segoe UI", 12, "bold"), bg=bg_color, fg=colors['SECONDARY'], anchor='w').pack(pady=(0, 5), fill='x')
            tk.Label(card, text=value, font=("Segoe UI", 36, "bold"), bg=bg_color, fg=value_fg_color).pack(pady=(5, 0))
        
        create_card(card_frame, "TOTAL RESIDENTS", total_patients, colors['CARD_BG'], colors['PRIMARY']) 
        create_card(card_frame, "SENIOR CITIZENS", senior_count, '#FCF3CF', '#F39C12')     
        create_card(card_frame, "ACTIVE PREGNANT", pregnant_count, '#FADBD8', '#E74C3C')    
        create_card(card_frame, "REGISTERED PWD", pwd_count, '#EBEDEF', '#5D6D7E') 

        # Sitio Breakdown Layout 
        sitio_counts = defaultdict(int)
        for p in patient_registry: sitio_counts[p.get('Sitio', 'N/A')] += 1
        
        sitio_frame = tk.LabelFrame(self.content_frame, text="📍 RESIDENTS PER SITIO BREAKDOWN", font=("Segoe UI", 12, "bold"), bg=colors['CONTENT_BG'], fg=colors['PRIMARY'], padx=20, pady=15)
        sitio_frame.pack(pady=(40, 20), padx=20, fill='x', anchor='w')
        
        sitio_list_frame = tk.Frame(sitio_frame, bg=colors['CONTENT_BG'])
        sitio_list_frame.pack(fill='x')
        sitio_list_frame.grid_columnconfigure(0, weight=1)
        sitio_list_frame.grid_columnconfigure(1, weight=1)

        sorted_sitios = sorted([s.upper() for s in SITIO_CHOICES])
        
        for i, sitio in enumerate(sorted_sitios):
            count = sitio_counts[sitio]
            tk.Label(sitio_list_frame, text=f"• {sitio.capitalize()}:", bg=colors['CONTENT_BG'], fg=colors['SECONDARY'], font=("Segoe UI", 11, "bold"), anchor='w', padx=5).grid(row=i, column=0, sticky='w', pady=3)
            tk.Label(sitio_list_frame, text=f"{count} Residents", bg=colors['CONTENT_BG'], fg=colors['PRIMARY'], font=("Segoe UI", 11), anchor='w', padx=5).grid(row=i, column=1, sticky='w', pady=3)
        
        # Display N/A or Undefined
        if sitio_counts['N/A'] > 0:
              tk.Label(sitio_list_frame, text=f"• N/A or Undefined Sitio:", bg=colors['CONTENT_BG'], fg='#DC3545', font=("Segoe UI", 11, "bold"), anchor='w', padx=5).grid(row=len(sorted_sitios), column=0, sticky='w', pady=3)
              tk.Label(sitio_list_frame, text=f"{sitio_counts['N/A']} Residents", bg=colors['CONTENT_BG'], fg='#DC3545', font=("Segoe UI", 11, "italic"), anchor='w', padx=5).grid(row=len(sorted_sitios), column=1, sticky='w', pady=3)

    # --- LIST VIEWS (Same as before, updated to handle 'LMP too recent') ---
    def _create_resident_table(self, data, title):
        self._switch_view(title)
        
        table_frame = tk.Frame(self.content_frame, bg=self.get_colors()['CONTENT_BG'])
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ('ID', 'Name', 'Age', 'Sitio', 'Health_Status', 'LMP', 'EDD', 'PWD_Type') 
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        
        # Configure Columns
        col_widths = {'ID': 50, 'Name': 200, 'Age': 60, 'Sitio': 100, 'Health_Status': 150, 'LMP': 100, 'EDD': 100, 'PWD_Type': 150}
        
        for col in columns: 
            tree.column(col, width=col_widths.get(col, 100), anchor='center' if col not in ['Name', 'Health_Status', 'PWD_Type'] else 'w')
            tree.heading(col, text=col.replace('_', ' ').upper())
        
        # Insert Data
        for p in data:
            age = calculate_age(p['Birthday'])
            edd, _ = calculate_edd_and_schedule(p.get('LMP', 'N/A'))
            
            # Display logic for LMP too recent
            edd_display = edd
            if edd == "LMP too recent (Not Pregnant)":
                edd_display = "N/A (LMP too recent)"
            
            tree.insert('', tk.END, values=(
                p['ID'], 
                p['Name'], 
                age if age != -1 else 'N/A', 
                p['Sitio'], 
                p['Health_Status'], 
                p.get('LMP', 'N/A'), 
                edd_display, 
                p.get('PWD_Type', 'NOT PWD')
            ))

        tree.pack(fill='both', expand=True)
        scrollbar.config(command=tree.yview)

    def show_master_list(self, is_senior_view=False):
        title = "👴 Senior Citizens List (60+ Y.O.)" if is_senior_view else "👥 Master Resident List (All Residents)"
        data = [p for p in patient_registry if calculate_age(p.get('Birthday', '1900-01-01')) >= 60] if is_senior_view else patient_registry 
        self._create_resident_table(data, title)
        
    def show_pwd_list(self): 
        colors = self.get_colors()
        self._switch_view("♿ PWD Master List (Persons with Disability)")
        pwd_data = [p for p in patient_registry if p.get('PWD_Type', 'NOT PWD') != 'NOT PWD']
        
        if not pwd_data: 
            tk.Label(self.content_frame, text="No registered PWDs in the system.", bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 14, "bold")).pack(pady=50)
            return
            
        self._create_resident_table(pwd_data, "♿ PWD Master List (Persons with Disability)") 
        
    def show_pregnant_scheduler(self):
        self._switch_view("🤰 Pregnant: EDD and Midwife Scheduler")
        
        pregnant_patients = [
            p for p in patient_registry 
            if p.get('LMP') and p['LMP'] != 'N/A' and 
            calculate_edd_and_schedule(p['LMP'])[0] not in ["N/A", "Invalid LMP Date", "Delivered (Post-Partum)", "LMP too recent (Not Pregnant)"]
        ]
        
        if not pregnant_patients: 
            tk.Label(self.content_frame, text="No active pregnant patients in the list.", bg=self.get_colors()['CONTENT_BG'], fg=self.get_colors()['TEXT_COLOR'], font=("Segoe UI", 14, "bold")).pack(pady=50)
            return

        table_frame = tk.Frame(self.content_frame, bg=self.get_colors()['CONTENT_BG'])
        table_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
        scrollbar = ttk.Scrollbar(table_frame, orient=tk.VERTICAL)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        columns = ('ID', 'Name', 'LMP', 'EDD', 'Sitio', 'Next_Checkup')
        tree = ttk.Treeview(table_frame, columns=columns, show='headings', yscrollcommand=scrollbar.set)
        
        col_widths = {'ID': 50, 'Name': 180, 'LMP': 120, 'EDD': 120, 'Sitio': 80, 'Next_Checkup': 300}
        col_headings = {'LMP': "LAST MENSTRUAL", 'EDD': "EDD (EXPECTED)", 'Next_Checkup': "SCHEDULES/NEXT CHECK-UP"}
        
        for col in columns: 
            tree.column(col, width=col_widths.get(col, 100), anchor='center' if col not in ['Name', 'Next_Checkup'] else 'w')
            tree.heading(col, text=col_headings.get(col, col.upper()))

        for p in pregnant_patients:
            edd, schedule = calculate_edd_and_schedule(p['LMP'])
            next_checkup_display = schedule[0] if schedule else "No upcoming checkups."
            tree.insert('', tk.END, values=(p['ID'], p['Name'], p['LMP'], edd, p['Sitio'], next_checkup_display))

        tree.pack(fill='both', expand=True)
        scrollbar.config(command=tree.yview)

    # --- PROFILE VIEW (Same as before, updated to handle 'LMP too recent') ---
    def show_view_patient(self):
        colors = self.get_colors()
        self._switch_view("🔎 View Resident Profile / History")
        
        search_frame = tk.Frame(self.content_frame, bg=colors['CONTENT_BG'])
        search_frame.pack(fill='x', padx=20, pady=10)
        
        tk.Label(search_frame, text="Search Resident (ID or Name):", bg=colors['CONTENT_BG'], fg=colors['SECONDARY'], font=("Segoe UI", 10, "bold")).pack(side=tk.LEFT, padx=5)
        
        self.profile_search_entry = tk.Entry(search_frame, relief=tk.FLAT, bg=colors['INPUT_BG'], font=("Segoe UI", 11))
        self.profile_search_entry.pack(side=tk.LEFT, fill='x', expand=True, padx=5, ipady=3)
        
        tk.Button(search_frame, text="Search", command=self._search_patient_for_profile, bg=colors['PRIMARY'], fg='white', relief=tk.FLAT).pack(side=tk.LEFT, padx=5)
        
        self.profile_display_frame = tk.Frame(self.content_frame, bg=colors['CONTENT_BG'])
        self.profile_display_frame.pack(fill='both', expand=True, padx=20, pady=10)
        
    def _search_patient_for_profile(self):
        colors = self.get_colors()
        for widget in self.profile_display_frame.winfo_children(): widget.destroy()
        
        self.current_patient_profile = find_patient_by_id_or_name(self.profile_search_entry.get())
        
        if not self.current_patient_profile: 
            tk.Label(self.profile_display_frame, text="Patient Not Found.", bg=colors['CONTENT_BG'], fg='#DC3545', font=("Segoe UI", 12, "bold")).pack(pady=20)
            return

        info = self.current_patient_profile
        age = calculate_age(info.get('Birthday', 'N/A'))
        edd, schedule = calculate_edd_and_schedule(info.get('LMP', 'N/A'))
        
        # Profile Card
        card = tk.Frame(self.profile_display_frame, bg=colors['CARD_BG'], padx=20, pady=15, relief=tk.RIDGE, bd=2)
        card.pack(fill='x', pady=10)
        
        tk.Label(card, text=f"👤 {info['Name']} (ID: {info['ID']})", bg=colors['CARD_BG'], fg=colors['PRIMARY'], font=("Segoe UI", 18, "bold")).pack(anchor='w')
        tk.Label(card, text=f"Sitio: {info['Sitio']} | Birthday: {info['Birthday']} (Age: {age})", bg=colors['CARD_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11)).pack(anchor='w', pady=(5, 0))
        tk.Label(card, text=f"Current Health Status: {info['Health_Status']} | PWD Status: {info.get('PWD_Type', 'NOT PWD')}", bg=colors['CARD_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11)).pack(anchor='w')
        
        # Display EDD logic
        lmp_edd_text = f"LMP: {info.get('LMP', 'N/A')} | EDD: {edd}"
        if edd == "LMP too recent (Not Pregnant)":
             lmp_edd_text = f"LMP: {info.get('LMP', 'N/A')} | EDD: N/A (LMP too recent)"
        
        tk.Label(card, text=lmp_edd_text, bg=colors['CARD_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11)).pack(anchor='w')

        if schedule:
            schedule_text = "\n".join(schedule) if len(schedule) <= 5 else "\n".join(schedule[:5]) + "\n...(More schedules not shown)"
            tk.Label(card, text=f"Upcoming Prenatal Schedule:\n{schedule_text}", bg=colors['CARD_BG'], fg='#E74C3C', font=("Segoe UI", 11, 'bold'), justify=tk.LEFT).pack(anchor='w', pady=(10, 0))

        # History Log
        history_frame = tk.LabelFrame(self.profile_display_frame, text="Medical History / Records Log", font=("Segoe UI", 12, "bold"), bg=colors['CONTENT_BG'], fg=colors['SECONDARY'], padx=15, pady=10)
        history_frame.pack(fill='both', expand=True, padx=10, pady=10)
        
        history_text = tk.Text(history_frame, bg=colors['INPUT_BG'], fg=colors['TEXT_COLOR'], font=("Consolas", 10), wrap=tk.WORD, height=15, relief=tk.FLAT)
        history_scrollbar = ttk.Scrollbar(history_frame, command=history_text.yview)
        history_text.config(yscrollcommand=history_scrollbar.set)
        
        history_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        history_text.pack(side=tk.LEFT, fill='both', expand=True)

        history_text.insert(tk.END, "\n\n---\n".join(info['Records']) if info['Records'] else "No recorded history yet.")
        history_text.config(state=tk.DISABLED) 
        
    # --- REPORTS VIEW (Same as before) ---
    def generate_report(self):
        colors = self.get_colors()
        self._switch_view("📈 Health Reports & Summary")
        total = len(patient_registry)
        
        illness_counts = defaultdict(int)
        pwd_counts = defaultdict(int)
        
        for p in patient_registry:
            # Count Illnesses
            for status in p['Health_Status'].split(', '):
                if status and status != 'N/A': illness_counts[status] += 1
            # Count PWD Types
            pwd_counts[p.get('PWD_Type', 'NOT PWD')] += 1

        def create_report_frame(title, counts_dict):
            frame = tk.LabelFrame(self.content_frame, text=title, font=("Segoe UI", 12, "bold"), bg=colors['CONTENT_BG'], fg=colors['PRIMARY'], padx=20, pady=15)
            frame.pack(pady=10, padx=20, fill='x', anchor='w')
            
            report_text = ""
            if counts_dict:
                # Sort by count descending
                sorted_items = sorted(counts_dict.items(), key=lambda item: item[1], reverse=True)
                for item, count in sorted_items:
                    if title.startswith("Primary Illnesses") and item == "NORMAL": continue
                    percentage = (count / total) * 100 if total > 0 else 0
                    report_text += f"• {item}: {count} Residents ({percentage:.1f}%)\n"
            else: 
                report_text = "No data recorded."
                
            tk.Label(frame, text=report_text, bg=colors['CONTENT_BG'], fg=colors['TEXT_COLOR'], font=("Segoe UI", 11), justify=tk.LEFT).pack(fill='x', padx=5, pady=5)

        create_report_frame("Primary Illnesses Breakdown (Excluding Normal)", illness_counts)
        create_report_frame("PWD Category Breakdown", pwd_counts)

def run_app():
    """Starts the main BHWApp interface after successful login."""
    global root
    root.deiconify() 
    root.geometry("1000x700") 
    root.resizable(True, True)
    
    # Clear any leftover login widgets
    for widget in root.winfo_children():
        widget.destroy()

    BHWApp(root, start_login_screen) # Pass the login function as a callback

def start_login_screen():
    """Sets up and displays the login screen."""
    global root
    # Reset main window size/title for login
    root.geometry("400x350")
    root.title("BHW Connect: Secure Login")
    root.resizable(False, False)
    
    # Clear any leftover BHWApp widgets
    for widget in root.winfo_children():
        widget.destroy()
        
    LoginScreen(root, run_app)

if __name__ == '__main__':
    root = tk.Tk()
    start_login_screen()
    root.mainloop()