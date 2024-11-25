from tkinter import ttk
import matplotlib.pyplot as plt

class DarkTheme:
    def __init__(self):
        # Define colors with better contrast
        self.colors = {
            'bg': '#2E2E2E',         # Dark background
            'fg': '#FFFFFF',         # White text
            'fg_dark': '#000000',    # Black text for light backgrounds
            'entry_bg': '#3E3E3E',   # Slightly lighter for input fields
            'button_bg': '#4A4A4A',  # Button background
            'button_pressed': '#666666',  # Button when pressed
            'accent': '#007AFF',     # Blue accent for highlights
            'combobox_bg': '#3E3E3E',  # Background for combobox
            'button_text': '#000000'  # Dark text for buttons
        }
        
    def apply(self, root):
        """Apply the theme to the root window and all widgets"""
        style = ttk.Style()
        
        # Configure frame style
        style.configure('Main.TFrame', 
                       background=self.colors['bg'])
        
        # Configure label style
        style.configure('TLabel', 
                       background=self.colors['bg'],
                       foreground=self.colors['fg'])
        
        # Configure entry style
        style.configure('TEntry',
                       fieldbackground=self.colors['entry_bg'],
                       foreground=self.colors['fg'],
                       insertcolor=self.colors['fg'])
        
        # Configure button style with explicit foreground color
        style.configure('TButton',
                       background=self.colors['button_bg'],
                       foreground=self.colors['button_text'],
                       borderwidth=1,
                       relief='raised',
                       padding=(10, 5))
        style.map('TButton',
                 background=[('pressed', self.colors['button_pressed']),
                            ('active', self.colors['accent'])],
                 foreground=[('pressed', self.colors['button_text']),
                            ('active', self.colors['button_text'])])
        
        # Configure combobox style
        style.configure('TCombobox',
                       fieldbackground=self.colors['combobox_bg'],
                       background=self.colors['button_bg'],
                       foreground=self.colors['fg_dark'],
                       selectbackground=self.colors['accent'],
                       selectforeground=self.colors['fg'])
        # Map combobox colors for different states
        style.map('TCombobox',
                 fieldbackground=[('readonly', self.colors['combobox_bg'])],
                 selectbackground=[('readonly', self.colors['accent'])],
                 selectforeground=[('readonly', self.colors['fg'])])
        
        # Configure labelframe style
        style.configure('TLabelframe',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'])
        style.configure('TLabelframe.Label',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'])
        
        # Configure progressbar style
        style.configure('TProgressbar',
                       background=self.colors['accent'],
                       troughcolor=self.colors['entry_bg'])
        
        # Configure checkbutton style
        style.configure('TCheckbutton',
                       background=self.colors['bg'],
                       foreground=self.colors['fg'])
        style.map('TCheckbutton',
                 background=[('active', self.colors['bg'])],
                 foreground=[('active', self.colors['fg'])])
        
        # Fix text color in combobox dropdown
        root.option_add('*TCombobox*Listbox.background', self.colors['combobox_bg'])
        root.option_add('*TCombobox*Listbox.foreground', self.colors['fg'])
        root.option_add('*TCombobox*Listbox.selectBackground', self.colors['accent'])
        root.option_add('*TCombobox*Listbox.selectForeground', self.colors['fg'])
        
        # Configure all frames to match background
        style.configure('TFrame', 
                       background=self.colors['bg'])
        
        # Configure root window colors
        root.configure(bg=self.colors['bg'])
        
        # Configure matplotlib style
        self.setup_matplotlib_style()
        
        return self.colors

    def setup_matplotlib_style(self):
        """Configure matplotlib style to match the dark theme"""
        plt.style.use('dark_background')
        plt.rcParams.update({
            'figure.facecolor': self.colors['bg'],
            'axes.facecolor': self.colors['bg'],
            'savefig.facecolor': self.colors['bg'],
            'axes.labelcolor': self.colors['fg'],
            'text.color': self.colors['fg'],
            'xtick.color': self.colors['fg'],
            'ytick.color': self.colors['fg'],
        })

class LightTheme:
    # [Light theme implementation could go here if needed]
    pass
