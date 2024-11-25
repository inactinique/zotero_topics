import tkinter as tk
from zotero_topic_modeling.ui.app import ZoteroTopicModelingApp

def main():
    root = tk.Tk()
    app = ZoteroTopicModelingApp(root)
    root.mainloop()

if __name__ == '__main__':
    main()
