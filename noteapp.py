# import
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3
from datetime import datetime
import json
import os
from PIL import Image, ImageTk  # Import Pillow for image handling

# Main function of the note app
class ModernNotesApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Docket")
        self.root.geometry("1200x800")
        self.root.configure(bg='#f0f2f5')

        # Configure fonts
        self.setup_fonts()
        # Configure styles
        self.configure_styles()

        # Database initialization
        try:
            self.init_database()
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", f"Failed to initialize database: {str(e)}")
            self.root.destroy()  # Close the application if database initialization fails
            return  # Stop further initialization

        # Create GUI elements
        self.create_gui()

        # Load backup if exists
        self.load_backup()

    def setup_fonts(self):
        """Setup custom fonts for the application"""
        self.title_font = ('Segoe UI', 24, 'bold')
        self.header_font = ('Segoe UI', 14)
        self.card_title_font = ('Segoe UI', 12)
        self.card_date_font = ('Segoe UI', 10)

    def configure_styles(self):
        """Configure ttk styles for modern appearance"""
        style = ttk.Style()
        style.theme_use('clam')

        # Colors
        self.colors = {
            'bg': '#f0f2f5',
            'card_colors': ['#FFE0B2', '#FFCCBC', '#E8F5E9', '#E1BEE7', '#B3E5FC', '#F0F4C3'],
            'text': '#1a1a1a',
            'secondary_text': '#666666'
        }

        # Frame style
        style.configure('Main.TFrame', background=self.colors['bg'])

        # Search style
        style.configure('Search.TEntry',
                        fieldbackground='white',
                        borderwidth=0,
                        font=('Segoe UI', 11))

        # Button style
        style.configure('Add.TButton',
                        font=('Segoe UI', 18),
                        background='#000000',
                        foreground='white')

    def create_gui(self):
        """Create the main GUI elements"""
        # Main container
        self.main_container = ttk.Frame(self.root, style='Main.TFrame')
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Top bar
        self.create_top_bar()

        # Title "Notes"
        notes_label = tk.Label(self.main_container,
                               text="Notes",
                               font=self.title_font,
                               bg=self.colors['bg'],
                               fg=self.colors['text'])
        notes_label.pack(anchor='w', pady=(30, 20))

        # Cards container (using Canvas for scrolling)
        self.create_cards_container()

        # Initial load of notes
        self.load_notes()

    def create_top_bar(self):
        """Create the top bar with logo and search"""
        top_bar = ttk.Frame(self.main_container, style='Main.TFrame')
        top_bar.pack(fill=tk.X, pady=(0, 20))

        # Logo
        logo_label = tk.Label(top_bar,
                              text="Docket",
                              font=('Segoe UI', 16, 'bold'),
                              bg=self.colors['bg'],
                              fg=self.colors['text'])
        logo_label.pack(side=tk.LEFT)

        # Search frame with icon
        search_frame = ttk.Frame(top_bar, style='Main.TFrame')
        search_frame.pack(side=tk.LEFT, padx=(20, 0))

        # Search icon (using unicode for search symbol)
        search_icon = tk.Label(search_frame,
                               text="🔍",
                               bg=self.colors['bg'],
                               fg=self.colors['secondary_text'])
        search_icon.pack(side=tk.LEFT, padx=(0, 5))

        # Search entry
        self.search_var = tk.StringVar()
        self.search_var.trace('w', self.on_search)
        search_entry = ttk.Entry(search_frame,
                                 textvariable=self.search_var,
                                 style='Search.TEntry',
                                 width=30)
        search_entry.pack(side=tk.LEFT)
        search_entry.insert(0, "Search")
        search_entry.bind('<FocusIn>', lambda e: search_entry.delete(0, tk.END) if search_entry.get() == "Search" else None)
        search_entry.bind('<FocusOut>', lambda e: search_entry.insert(0, "Search") if search_entry.get() == "" else None)

        # Add note button
        add_button = tk.Button(top_bar,
                               text="+",
                               font=('Segoe UI', 18),
                               bg='#000000',
                               fg='white',
                               bd=0,
                               width=2,
                               command=self.show_note_dialog)
        add_button.pack(side=tk.RIGHT)

    def create_cards_container(self):
        """Create scrollable container for note cards"""
        # Canvas for scrolling
        self.canvas = tk.Canvas(self.main_container,
                                bg=self.colors['bg'],
                                highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = ttk.Scrollbar(self.main_container,
                                  orient="vertical",
                                  command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Configure canvas
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.bind('<Configure>', lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))

        # Frame for cards
        self.cards_frame = ttk.Frame(self.canvas, style='Main.TFrame')
        self.canvas.create_window((0, 0), window=self.cards_frame, anchor="nw", width=self.canvas.winfo_reqwidth())

    def create_note_card(self, note_id, title, content, date, image_path, color_index):  # Added image_path
        """Create a single note card"""
        card = tk.Frame(self.cards_frame,
                        bg=self.colors['card_colors'][color_index % len(self.colors['card_colors'])],
                        padx=15,
                        pady=15,
                        width=250,
                        height=200) # increased height to accommodate image
        card.pack_propagate(False)
        card.grid(row=color_index // 3,
                  column=color_index % 3,
                  padx=5,
                  pady=5,
                  sticky='nsew')

        # Image - if one exists
        if image_path:
            try:
                load = Image.open(image_path)
                load = load.resize((220, 100), Image.Resampling.LANCZOS) # resize image to fit card
                render = ImageTk.PhotoImage(load)
                img = tk.Label(card, image=render, bg=card['bg'])
                img.image = render # keep a reference!
            except Exception as e:
                print(f"Error loading image: {e}") # handle image loading errors


        # Title
        title_label = tk.Label(card,
                               text=title,
                               font=self.card_title_font,
                               bg=card['bg'],
                               wraplength=220,
                               justify=tk.LEFT,
                               anchor='w')
        title_label.pack(fill=tk.X)


        # Content preview
        content_preview = content[:100] + "..." if len(content) > 100 else content
        content_label = tk.Label(card,
                                 text=content_preview,
                                 font=self.card_date_font,
                                 bg=card['bg'],
                                 fg=self.colors['secondary_text'],
                                 wraplength=220,
                                 justify=tk.LEFT,
                                 anchor='w')
        content_label.pack(fill=tk.X, pady=(10, 0))

        # Date
        date_label = tk.Label(card,
                              text=date,
                              font=self.card_date_font,
                              bg=card['bg'],
                              fg=self.colors['secondary_text'])
        date_label.pack(side=tk.BOTTOM, anchor='w')

        # Bind click event
        card.bind('<Button-1>', lambda e, id=note_id: self.show_note_dialog(id))
        title_label.bind('<Button-1>', lambda e, id=note_id: self.show_note_dialog(id))
        content_label.bind('<Button-1>', lambda e, id=note_id: self.show_note_dialog(id))
        date_label.bind('<Button-1>', lambda e, id=note_id: self.show_note_dialog(id))


    def show_note_dialog(self, note_id=None):
        """Show dialog for creating/editing note"""
        dialog = tk.Toplevel(self.root)
        dialog.title("Note")
        dialog.geometry("600x650")
        dialog.configure(bg='white')

        # Get note data if editing
        title = ""
        content = ""
        image_path = "" # initialize image path
        if note_id:
            try:
                self.cursor.execute("SELECT title, content, image_path FROM notes WHERE id=?", (note_id,)) # updated query
                note = self.cursor.fetchone()
                if note:
                    title, content, image_path = note
            except sqlite3.OperationalError as e:
                messagebox.showerror("Error", f"Database error: {e}")
                dialog.destroy()
                return

        # Title entry
        title_entry = tk.Entry(dialog,
                               font=self.header_font,
                               bg='white',
                               bd=0)
        title_entry.pack(fill=tk.X, padx=20, pady=(20, 10))
        title_entry.insert(0, title)

        # Image selection button
        def select_image():
            nonlocal image_path # declare as nonlocal to modify parent scope variable
            filepath = filedialog.askopenfilename(
                filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.gif")]
            )
            if filepath:
                image_path = filepath

        image_button = ttk.Button(dialog, text="Select Image", command=select_image)
        image_button.pack(pady=(0, 10)) # add the button to the layout


        # Content text
        content_text = tk.Text(dialog,
                               font=self.card_title_font,
                               bg='white',
                               bd=0,
                               wrap=tk.WORD)
        content_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        content_text.insert('1.0', content)

        # Save button
        save_btn = tk.Button(dialog,
                             text="Save",
                             font=self.card_title_font,
                             bg='#000000',
                             fg='white',
                             bd=0,
                             command=lambda: self.save_note(
                                 note_id,
                                 title_entry.get(),
                                 content_text.get('1.0', tk.END),
                                 image_path, # added image_path to save_note
                                 dialog))
        save_btn.pack(side=tk.LEFT, padx=10, pady=(0, 20))

        # Delete button (only visible when editing an existing note)
        if note_id:
            delete_btn = tk.Button(dialog,
                                   text="Delete",
                                   font=self.card_title_font,
                                   bg='red',
                                   fg='white',
                                   bd=0,
                                   command=lambda: self.delete_note(note_id, dialog))
            delete_btn.pack(side=tk.LEFT, padx=10, pady=(0, 20))

    def save_note(self, note_id, title, content, image_path, dialog): # added image_path parameter
        """Save note to database"""
        try:
            if not title.strip():
                messagebox.showerror("Error", "Title cannot be empty")
                return

            now = datetime.now()
            if note_id:
                self.cursor.execute("""
                    UPDATE notes
                    SET title=?, content=?, modified_date=?, image_path=?
                    WHERE id=?
                """, (title, content, now, image_path, note_id))
            else:
                self.cursor.execute("""
                    INSERT INTO notes (title, content, created_date, modified_date, image_path)
                    VALUES (?, ?, ?, ?, ?)
                """, (title, content, now, now, image_path))

            self.conn.commit()
            dialog.destroy()
            self.load_notes()
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def delete_note(self, note_id, dialog):
        """Delete note from database"""
        try:
            self.cursor.execute("DELETE FROM notes WHERE id=?", (note_id,))
            self.conn.commit()
            dialog.destroy()
            self.load_notes()
            messagebox.showinfo("Success", "Note deleted successfully!")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def load_notes(self, search_term=None):
        """Load notes and display as cards"""
        # Clear existing cards
        for widget in self.cards_frame.winfo_children():
            widget.destroy()

        # Configure grid
        self.cards_frame.grid_columnconfigure(0, weight=1)
        self.cards_frame.grid_columnconfigure(1, weight=1)
        self.cards_frame.grid_columnconfigure(2, weight=1)

        try:
            if search_term:
                self.cursor.execute("""
                    SELECT id, title, content, modified_date, image_path
                    FROM notes
                    WHERE LOWER(title) LIKE ? OR LOWER(content) LIKE ?
                    ORDER BY modified_date DESC
                """, (f'%{search_term.lower()}%', f'%{search_term.lower()}%'))
            else:
                self.cursor.execute("""
                    SELECT id, title, content, modified_date, image_path
                    FROM notes
                    ORDER BY modified_date DESC
                """)

            for i, note in enumerate(self.cursor.fetchall()):
                note_id, title, content, date, image_path = note # updated to include image_path
                date_obj = datetime.strptime(date, '%Y-%m-%d %H:%M:%S.%f')
                date_str = date_obj.strftime('%b %d, %Y')
                self.create_note_card(note_id, title, content, date_str, image_path, i)  # pass image_path

        except sqlite3.Error as e:
            messagebox.showerror("Error", f"Failed to load notes: {str(e)}")

    def on_search(self, *args):
        """Handle search input"""
        search_term = self.search_var.get()
        if search_term and search_term != "Search":
            self.load_notes(search_term)
        else:
            self.load_notes()

    def init_database(self):
        self.conn = sqlite3.connect('notes.db')
        self.cursor = self.conn.cursor()

        try: # handles pre-existing notes.db files without image_path
            self.cursor.execute("ALTER TABLE notes ADD COLUMN image_path TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists

        self.conn.commit()


    def create_backup(self):
        try:
            self.cursor.execute("SELECT id, title, content, created_date, modified_date, image_path FROM notes")  # Include image path
            notes = self.cursor.fetchall()

            backup_data = [{
                'id': note[0],
                'title': note[1],
                'content': note[2],
                'created_date': note[3],
                'modified_date': note[4],
                'image_path': note[5]   # Add image path to backup
            } for note in notes]

            with open('notes_backup.json', 'w') as f:
                json.dump(backup_data, f, indent=4)

            messagebox.showinfo("Success", "Backup created successfully!")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to create backup: {str(e)}")

    def load_backup(self):
        try:
            self.cursor.execute("SELECT COUNT(*) FROM notes")
            if self.cursor.fetchone()[0] == 0 and os.path.exists('notes_backup.json'):
                with open('notes_backup.json', 'r') as f:
                    backup_data = json.load(f)

                for note in backup_data:
                    self.cursor.execute("""
                        INSERT INTO notes (title, content, created_date, modified_date, image_path)  # Include image path
                        VALUES (?, ?, ?, ?, ?)
                    """, (note['title'], note['content'], note['created_date'], note['modified_date'], note.get('image_path', '')))  # Handle missing image path

                self.conn.commit()
                self.load_notes()
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load backup: {str(e)}")


    def __del__(self):
        try:
            self.conn.close()
        except:
            pass

if __name__ == "__main__":
    try:
        root = tk.Tk()
        app = ModernNotesApp(root)
        root.mainloop()
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Application failed to start: {str(e)}")
