import tkinter as tk
import logging
from zotero_topic_modeling.ui.app import ZoteroTopicModelingApp

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    """Main entry point for the application"""
    root = tk.Tk()
    root.title("Zotero Topic Modeling")
    
    # Set initial window icon if available
    try:
        # Try to set application icon
        root.iconbitmap("icon.ico")  # For Windows
    except:
        try:
            # For macOS and Linux
            logo = tk.PhotoImage(file="icon.png")
            root.iconphoto(True, logo)
        except:
            logging.warning("Application icon not found")
    
    # Create and start the application
    app = ZoteroTopicModelingApp(root)
    
    # Center the window on screen
    root.update_idletasks()
    width = root.winfo_width()
    height = root.winfo_height()
    x = (root.winfo_screenwidth() // 2) - (width // 2)
    y = (root.winfo_screenheight() // 2) - (height // 2)
    root.geometry('{}x{}+{}+{}'.format(width, height, x, y))
    
    # Start the main event loop
    root.mainloop()

if __name__ == '__main__':
    main()
