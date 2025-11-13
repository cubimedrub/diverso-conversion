"""Graphical user interface for the conversion tool."""

from pathlib import Path
from logging import Logger, Handler as LoggingHandler
from tkinter import Tk, filedialog, ttk, StringVar, END
import tkinter.scrolledtext as ScrolledText

from diverso_conversion.conversion import conversion


class Gui:
    """Tk based GUI for the conversion tool."""

    def __init__(self, logger: Logger):
        self.logger = logger

        # Initialize the GUI
        root = Tk()
        frm = ttk.Frame(root, padding=10, height=100, width=600)
        frm.grid()

        frm.grid(column=0, row=0, sticky="ew")
        frm.grid_columnconfigure(0, weight=1, uniform="a")
        frm.grid_columnconfigure(1, weight=1, uniform="a")
        frm.grid_columnconfigure(2, weight=1, uniform="a")
        frm.grid_columnconfigure(3, weight=1, uniform="a")

        # Initialize variables used in the GUIs
        self.patient_file_path = StringVar()
        self.column_whitelist = StringVar()
        self.output_file_path = StringVar()

        # Create the GUI elements
        ttk.Entry(
            frm, textvariable=self.patient_file_path, state="disabled", width=100
        ).grid(
            column=0,
            row=0,
            columnspan=3,
        )
        ttk.Button(frm, text="patients file", command=self.select_patient_file).grid(
            column=3, row=0, sticky="w"
        )

        ttk.Entry(
            frm,
            textvariable=self.column_whitelist,
            state="enabled",
            width=100,
        ).grid(
            column=0,
            row=1,
            columnspan=3,
        )

        ttk.Entry(
            frm, textvariable=self.output_file_path, state="disabled", width=100
        ).grid(
            column=0,
            row=2,
            columnspan=3,
        )
        ttk.Button(frm, text="output file", command=self.select_output_file).grid(
            column=3, row=2, sticky="w"
        )

        ttk.Button(frm, text="Start", command=self.run_conversion).grid(
            column=0, row=10, sticky="e"
        )
        ttk.Button(frm, text="Quit", command=root.destroy).grid(
            column=3, row=10, sticky="w"
        )

        logger_st = ScrolledText.ScrolledText(frm, state="disabled")
        logger_st.configure(font="TkFixedFont")
        logger_st.grid(column=0, row=20, columnspan=4)

        logging_widget = LoggerWidget(logger_st, level=logger.level)
        logger.addHandler(logging_widget)

        # Start the GUI event loop
        root.mainloop()

    def select_patient_file(self):
        """Open a file dialog to select the patient file."""

        filetypes = (("Excel file", "*.xlsx"),)

        filepath = filedialog.askopenfilename(
            title="select patients file", initialdir=Path.home(), filetypes=filetypes
        )

        if len(filepath) > 0:
            self.patient_file_path.set(str(filepath))
            self.output_file_path.set(str(Path(filepath).with_suffix(".merged.xlsx")))

    def select_output_file(self):
        """Open a file dialog to select the output file."""

        filetypes = (("Excel file", "*.xlsx"),)

        initial_dir = Path.home()
        initial_file = None
        if self.output_file_path.get():
            initial_dir = None
            initial_file = Path(self.output_file_path.get())

        filepath = filedialog.asksaveasfilename(
            title="select output file",
            initialdir=initial_dir,
            initialfile=initial_file,
            defaultextension=".xlsx",
            filetypes=filetypes,
        )

        if len(filepath) > 0:
            self.output_file_path.set(str(Path(filepath)))

    def run_conversion(self):
        """
        Runs the conversion process using the GUI inputs.
        """
        try:
            column_whitelist = set()
            column_whitelist_str = self.column_whitelist.get().strip()
            if len(column_whitelist_str):
                column_whitelist = {
                    col.strip()
                    for col in self.column_whitelist.get().split(",")
                    if len(col.strip()) > 0
                }

            conversion(
                Path(self.patient_file_path.get()),
                Path(self.output_file_path.get()),
                column_whitelist,
                self.logger,
            )
        except (FileNotFoundError, NotADirectoryError) as e:
            self.logger.error("%s", e)


class LoggerWidget(LoggingHandler):
    """Widget to display log messages in a Tkinter ScrolledText widget."""

    def __init__(self, widget, level: int):
        """
        Initializes the LoggerWidget.

        Parameters
        ----------
        widget : ScrolledText
            The ScrolledText widget to display log messages.
        level : int
            Log level
        """

        LoggingHandler.__init__(self, level=level)
        self.widget = widget
        self.widget.config(state="disabled")

    def emit(self, record):
        self.widget.config(state="normal")
        # Append message (record) to the widget
        self.widget.insert(END, self.format(record) + "\n")
        self.widget.see(END)  # Scroll to the bottom
        self.widget.config(state="disabled")
