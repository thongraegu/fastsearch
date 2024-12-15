import os
import subprocess
import pickle
from collections import defaultdict
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QLabel, QLineEdit,
                             QPushButton, QTreeWidget, QTreeWidgetItem, QVBoxLayout, QWidget,
                             QMessageBox, QHBoxLayout, QSizeGrip, QComboBox)
from PyQt5.QtCore import Qt, QTimer, QSettings

class FileIndex:
    def __init__(self):
        self.index = defaultdict(list)

    def build_index(self, root_directory):
        """Builds an index of filenames."""
        for dirpath, _, filenames in os.walk(root_directory):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                self.index[filename].append(filepath)

    def search(self, query):
        """Searches for files by name with partial matching, removing duplicates."""
        if not query:
            return []
        results = []
        query_lower = query.lower()
        for filename, filepaths in self.index.items():
            if query_lower in filename.lower():
                results.extend(filepaths)
        # Remove duplicates
        results = list(set(results))
        return results

    def save_index(self, filename):
        with open(filename, 'wb') as f:
            pickle.dump(dict(self.index), f)

    def load_index(self, filename):
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                loaded_index = pickle.load(f)
                self.index = defaultdict(list, loaded_index)
                return True
        return False


class FileItem(QTreeWidgetItem):
    def __lt__(self, other):
        column = self.treeWidget().sortColumn()
        if column == 1:
            # Size column - numeric comparison
            return self.data(1, Qt.UserRole) < other.data(1, Qt.UserRole)
        elif column == 2:
            # Date column - numeric timestamp comparison
            return self.data(2, Qt.UserRole) < other.data(2, Qt.UserRole)
        else:
            # For Name (0) and Full Path (3), default string comparison
            return super().__lt__(other)


class FastFileSearchGUI(QMainWindow):
    def __init__(self, index):
        super().__init__()

        self.index = index
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.resize(800, 600)

        self.settings = QSettings("MyCompany", "FastFileSearch")

        # Custom title bar
        self.title_bar = QWidget(self)
        self.title_bar.setFixedHeight(40)
        self.title_bar.setStyleSheet("background-color: #2a2a2a; border-top-left-radius:8px; border-top-right-radius:8px;")

        self.title_layout = QVBoxLayout(self.title_bar)
        self.title_layout.setContentsMargins(10, 0, 10, 0)

        self.title_h_layout = QHBoxLayout()
        self.title_h_layout.setContentsMargins(0,0,0,0)

        self.title_label = QLabel("Fast File Search", self.title_bar)
        self.title_label.setStyleSheet("color: white; font: 12pt 'Segoe UI';")
        self.title_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)

        self.title_status_label = QLabel("", self.title_bar)
        self.title_status_label.setStyleSheet("color: green; font: 10pt 'Segoe UI';")

        # Close button
        self.btn_close = QPushButton("✕", self.title_bar)
        self.btn_close.setFixedSize(32, 32)
        self.btn_close.setStyleSheet("""
        QPushButton {
            background-color: red;
            border: none;
            border-radius: 16px;
            color: white;
            font-size: 13pt;
            font-weight: normal;
        }
        QPushButton:hover {
            background-color: #cc0000;
        }
        """)
        self.btn_close.clicked.connect(self.close)

        self.title_h_layout.addWidget(self.title_label)
        self.title_h_layout.addStretch(1)
        self.title_h_layout.addWidget(self.title_status_label, 0, Qt.AlignCenter)
        self.title_h_layout.addStretch(1)
        self.title_h_layout.addWidget(self.btn_close)
        self.title_layout.addLayout(self.title_h_layout)

        central_widget = QWidget(self)
        layout = QVBoxLayout()

        # Indexing controls layout
        indexing_layout = QHBoxLayout()

        red_button_style = """
        QPushButton {
            background-color: red;
            border: none;
            border-radius: 4px;
            color: white;
            font-size: 10pt;
            font-weight: bold;
            padding: 4px 8px;
        }
        QPushButton:hover {
            background-color: #cc0000;
        }
        """

        # Smaller red "Index C:/"
        self.btn_index_c = QPushButton("Index C:/")
        self.btn_index_c.setStyleSheet(red_button_style)
        self.btn_index_c.setFixedWidth(100)
        self.btn_index_c.clicked.connect(self.index_c_drive)
        indexing_layout.addWidget(self.btn_index_c)

        # Add spacing after Index C:/
        indexing_layout.addSpacing(10)

        # Add a stretch to push the next widgets to the right side
        indexing_layout.addStretch(1)

        # Drive selection combo
        self.drive_combo = QComboBox()
        self.drive_combo.addItems(["C:/", "D:/", "E:/", "F:/", "G:/"])
        self.drive_combo.setFixedWidth(120)
        indexing_layout.addWidget(self.drive_combo)

        # Index drive button next to combo
        self.btn_index_drive = QPushButton("Index Drive")
        self.btn_index_drive.setStyleSheet(red_button_style)
        self.btn_index_drive.setFixedWidth(120)
        self.btn_index_drive.clicked.connect(self.index_selected_drive)
        indexing_layout.addWidget(self.btn_index_drive)

        layout.addLayout(indexing_layout)

        # Search input
        self.label_query = QLabel("Search Filename:")
        self.edit_query = QLineEdit()
        layout.addWidget(self.label_query)
        layout.addWidget(self.edit_query)

        self.enter_pressed = False
        self.edit_query.returnPressed.connect(self.enter_search)

        self.search_delay_timer = QTimer(self)
        self.search_delay_timer.setSingleShot(True)
        self.search_delay_timer.setInterval(300)
        self.search_delay_timer.timeout.connect(self.perform_search_delayed)

        self.edit_query.textChanged.connect(self.schedule_search)

        # No search button as requested

        # Tree widget for results with 4 columns
        self.tree_files = QTreeWidget()
        self.tree_files.setColumnCount(4)
        self.tree_files.setHeaderLabels(["Name", "Size", "Modified Date", "Full Path"])
        self.tree_files.itemDoubleClicked.connect(self.open_file_in_explorer)
        self.tree_files.setSortingEnabled(True)  # Enable sorting by column click
        # Always show horizontal scrollbar
        self.tree_files.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        layout.addWidget(self.tree_files)

        central_widget.setLayout(layout)

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0,0,0,0)
        main_layout.setSpacing(0)
        main_layout.addWidget(self.title_bar)
        main_layout.addWidget(central_widget)

        self.size_grip = QSizeGrip(self)
        main_layout.addWidget(self.size_grip, 0, Qt.AlignBottom | Qt.AlignRight)

        container = QWidget()
        container.setLayout(main_layout)
        self.setCentralWidget(container)

        # Additional scrollbar styling
        self.setStyleSheet("""
        QMainWindow {
            background-color: #2a2a2a;
            border: 1px solid #444444;
            border-radius: 8px;
        }
        QLabel {
            color: white;
            font: 10pt "Segoe UI";
        }
        QLineEdit {
            background-color: #3a3a3a;
            color: white;
            border: 1px solid #555555;
            border-radius: 4px;
            padding: 4px;
        }
        QPushButton {
            background-color: #555555;
            color: white;
            border: none;
            border-radius: 4px;
            padding: 6px 12px;
        }
        QPushButton:hover {
            background-color: #666666;
        }
        QTreeWidget {
            background-color: #3a3a3a;
            color: white;
            border-radius: 4px;
            border: 1px solid #444444;
            font-size: 12pt; 
        }
        QHeaderView::section {
            background-color: #2a2a2a;
            color: white;
        }

        /* Scrollbar styling */
        QScrollBar:horizontal {
            background: #2a2a2a;
            height: 10px;
        }
        QScrollBar::handle:horizontal {
            background: #666666;
            min-width: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
            background: none;
            border: none;
            width: 0px;
            height: 0px;
        }
        QScrollBar:vertical {
            background: #2a2a2a;
            width: 10px;
        }
        QScrollBar::handle:vertical {
            background: #666666;
            min-height: 20px;
            border-radius: 5px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            background: none;
            border: none;
            height: 0px;
            width: 0px;
        }
        """)

        # Implement window dragging
        self.offset = None
        def mousePressEvent(event):
            if event.button() == Qt.LeftButton and self.title_bar.geometry().contains(event.pos()):
                self.offset = event.globalPos() - self.pos()

        def mouseMoveEvent(event):
            if self.offset is not None and event.buttons() == Qt.LeftButton:
                self.move(event.globalPos() - self.offset)

        def mouseReleaseEvent(event):
            self.offset = None

        self.mousePressEvent = mousePressEvent
        self.mouseMoveEvent = mouseMoveEvent
        self.mouseReleaseEvent = mouseReleaseEvent

        loaded = self.index.load_index('file_index.pkl')
        if loaded:
            self.title_status_label.setText("Index Loaded")
            self.title_status_label.setStyleSheet("color: green; font: 10pt 'Segoe UI';")
        else:
            self.title_status_label.setText("")
            self.title_status_label.setStyleSheet("color: green; font: 10pt 'Segoe UI';")

        geom = self.settings.value("geometry")
        if geom is not None:
            self.restoreGeometry(geom)

    def index_selected_drive(self):
        drive = self.drive_combo.currentText().strip()
        if drive:
            self.title_status_label.setText("Loading index...")
            self.title_status_label.setStyleSheet("color: red; font: 10pt 'Segoe UI';")
            QApplication.processEvents()
            self.perform_indexing(drive)

    def schedule_search(self):
        self.search_delay_timer.start()

    def perform_search_delayed(self):
        self.perform_search()

    def enter_search(self):
        self.enter_pressed = True
        self.perform_search()
        self.enter_pressed = False

    def index_c_drive(self):
        self.title_status_label.setText("Loading index...")
        self.title_status_label.setStyleSheet("color: red; font: 10pt 'Segoe UI';")
        QApplication.processEvents()  # update UI before blocking operation
        self.perform_indexing("C:/")

    def perform_indexing(self, directory):
        if not os.path.isdir(directory):
            QMessageBox.critical(self, "Error", f"{directory} is not a valid directory.")
            return
        # Clear old index before building a new one
        self.index.index.clear()
        self.index.build_index(directory)
        self.index.save_index('file_index.pkl')
        self.title_status_label.setText("Index Loaded")
        self.title_status_label.setStyleSheet("color: green; font: 10pt 'Segoe UI';")

    def human_readable_size(self, size):
        for unit in ['B','KB','MB','GB','TB']:
            if size < 1024:
                return f"{int(size)} {unit}"
            size /= 1024.0
        return f"{size:.2f} TB"

    def perform_search(self):
        query = self.edit_query.text().strip()
        # If not triggered by enter and length less than 4, do nothing
        if not self.enter_pressed and len(query) < 4:
            self.tree_files.clear()
            return

        results = self.index.search(query)

        # Gather metadata
        file_entries = []
        for path in results:
            try:
                size = os.path.getsize(path)
                mtime = os.path.getmtime(path)
                file_entries.append((path, size, mtime))
            except OSError:
                continue

        # Limit to 50 results
        file_entries = file_entries[:50]

        self.tree_files.clear()

        if file_entries:
            for (path, size, mtime) in file_entries:
                name = os.path.basename(path)
                size_str = self.human_readable_size(size)
                date_str = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M:%S")

                item = FileItem([name, size_str, date_str, path])
                # Store numeric size and mtime for sorting
                item.setData(1, Qt.UserRole, size)
                item.setData(2, Qt.UserRole, mtime)
                item.setData(0, Qt.UserRole, path)  # store path in name column as well
                self.tree_files.addTopLevelItem(item)
        else:
            if query:
                no_item = FileItem(["No files found", "", "", ""])
                self.tree_files.addTopLevelItem(no_item)

        # Adjust column widths after populating
        self.tree_files.setColumnWidth(0, 300)  # Name
        self.tree_files.setColumnWidth(2, 300)  # Modified Date
        self.tree_files.setColumnWidth(3, 1200) # Full Path - large width to ensure scroll

    def open_file_in_explorer(self, item, column):
        path = item.data(0, Qt.UserRole)
        if not path or not os.path.exists(path):
            return
        path = os.path.abspath(path)
        path = path.replace('/', '\\')
        cmd = f'explorer /select,"{path}"'
        subprocess.run(cmd, shell=True)

    def closeEvent(self, event):
        self.settings.setValue("geometry", self.saveGeometry())
        event.accept()


if __name__ == "__main__":
    import sys
    app = QApplication(sys.argv)
    file_index = FileIndex()
    main_window = FastFileSearchGUI(file_index)
    main_window.show()
    sys.exit(app.exec_())
