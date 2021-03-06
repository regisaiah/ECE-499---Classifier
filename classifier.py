# |ECE 499: Classifier|--------------------------------------------------------
#
# Project: Brain Assessment for Mental Fatigue
# Program: Machine Learning Classifier (v1.200712)
#
# Description:
#      This Application is used to train the classifier for the
# ECE 499 Project: Brain Assessment of Mental Fatigue. The data is
# preprocessed and prepared into Pandas Data Frames. Knowing the label of the
# data set, the classifier is trained. The application also has the ability to
# test the classifier and output the result.
#
# Date Created:     May 22, 2020
#
# v1.200522 - Isaiah Regacho
#    - Script adopted from original ECE 399 project
#    - Added description blocks for each method.
# v1.200524 - Austin Weir
#    - Test
# v1.200527 - IR
#    - Changed the filename check for Grand Truth from "Early" to "Pre"
#    - Added folder selection for test spreadsheet output.
#    - Changed test output to use tabs instead.
# v1.200528 - IR
#    - Initialize Classifier once Train Classifier is called.
#    - Added Flags for Classifier Options
# v1.200606 - IR
#    - Added Font Changer
#    - Modified the GUI
# v1.200712 - IR
#    - Major Changes
# -----------------------------------------------------------------------------

# |MODULES|--------------------------------------------------------------------
import cProfile
import io
import os
import pstats
import sys

import itertools as it
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pickle as pk
import tkinter as tk
import tkinter.ttk as ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from pstats import SortKey
from scipy import signal, fftpack
from sklearn.feature_selection import RFECV
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix
from sklearn.model_selection import GridSearchCV, PredefinedSplit
from sklearn.svm import SVC
from tkinter import N, E, W, S, filedialog, font, END, RIDGE


class EegGui:
    def __init__(self, master=None):
        # Initialize ttk Style
        self.style = ttk.Style()
        # Ttk Style Label Settings
        self.allLabels = {'Main.TLabel': [],
                          'Controls.TLabel': [],
                          'Display.TLabel': [],
                          'ControlsL.TLabel': [],
                          'DisplayL.TLabel': [],
                          'Main.TNotebook': [],
                          'TButton': [],
                          'TMenubutton': []}

        self.fontpreset = {'Title': ['Arial', 20, 'bold'],
                           'Tab': ['Arial', 14, ''],
                           'Heading': ['Arial', 14, 'bold'],
                           'Label': ['Arial', 12, ''],
                           'Button': ['Arial', 12, 'bold']}
        self.initstyle()

        # Initialize the Main Window
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.master.quit)  # handle event when window is closed by user
        self.master.bind("<Escape>", self.onClose)  # Bind: Press Escape to Close Application
        self.master.title("ECE 399 BAMF GUI")
        self.master.geometry("1680x720")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        # Main Frame
        self.mainpage = ttk.Frame(self.master, style='Main.TFrame')
        for i, w in enumerate([1]):
            self.mainpage.grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.mainpage.grid_rowconfigure(i, weight=w)
        self.mainpage.grid(sticky=N+E+W+S)

        # MF - Title
        self.titsep = ttk.Separator(self.mainpage, style='Main.TSeparator')
        self.titsep.grid(row=0, sticky=E+W, columnspan=2, padx=200)
        self.title = ttk.Label(self.mainpage, style='Main.TLabel', text="Brain Assessment of Mental Fatigue")
        self.title.bind("<Button-1>", self.switchfont)
        self.title.grid(row=0, padx=5, pady=5)
        self.allLabels['Main.TLabel'].append(self.title)

        # MF - Notebook
        self.note = ttk.Notebook(self.mainpage, style='Main.TNotebook')
        self.note.grid(row=1, sticky=N+E+W+S, padx=15, pady=15)
        self.allLabels['Main.TNotebook'].append(self.note)

        self.pageTitle = ["View Data",
                          "Feature Plots",
                          "Marked Data",
                          "Train Classifier",
                          "Histogram"]

        self.page = []
        self.pagectr = []
        self.pagedis = []
        for title in self.pageTitle:
            frm = ttk.Frame(self.note, style='Page.TFrame')
            frm.grid_rowconfigure(0, weight=1)
            frm.grid_columnconfigure(1, weight=1)
            frm.grid(sticky=N+E+W+S, padx=15, pady=15)

            self.page.append(frm)
            self.note.add(frm, text=title, sticky=N+E+W+S)

            frmctr = ttk.Frame(frm, style='Controls.TFrame')
            frmctr.grid(row=0, column=0, sticky=N+E+W+S, padx=15, pady=15)
            self.pagectr.append(frmctr)

            frmdis = ttk.Frame(frm, style='Display.TFrame')
            frmdis.grid(row=0, column=1, sticky=N+E+W+S, padx=15, pady=15)
            self.pagedis.append(frmdis)

        # Page 0 - Time Domain Control
        for i, w in enumerate([0, 1]):
            self.pagectr[0].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]):
            self.pagectr[0].grid_rowconfigure(i, weight=w)

        self.selDatsep0 = ttk.Separator(self.pagectr[0], style='Controls.TSeparator')
        self.selDatsep0.grid(row=0, column=0, columnspan=2, sticky=E + W, pady=5, padx=5)

        self.selDatlbl = ttk.Label(self.pagectr[0], text="Select Data", style='Controls.TLabel')
        self.selDatlbl.grid(row=0, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.selDatlbl)

        self.ploDatbtn = ttk.Button(self.pagectr[0], text="Plot Data", command=self.viewcsv)
        self.ploDatbtn.grid(row=2, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['TButton'].append(self.ploDatbtn)

        self.axiConsep = ttk.Separator(self.pagectr[0], style='Controls.TSeparator')
        self.axiConsep.grid(row=3, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        self.axiConlbl = ttk.Label(self.pagectr[0], text="Axis Controls", style='Controls.TLabel')
        self.axiConlbl.grid(row=3, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.axiConlbl)

        self.axiWidlbl = ttk.Label(self.pagectr[0], text="Width:", style='ControlsL.TLabel')
        self.axiWidlbl.grid(row=6, column=0, sticky=E, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.axiWidlbl)
        self.axiOfflbl = ttk.Label(self.pagectr[0], text="Offset:", style='ControlsL.TLabel')
        self.axiOfflbl.grid(row=7, column=0, sticky=E, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.axiOfflbl)

        self.varXwidth = tk.DoubleVar()
        self.varXoffset = tk.DoubleVar()
        self.varXwidth.set(400)
        self.varXwidth.trace('w', self.ploteeg)
        self.varXoffset.trace('w', self.ploteeg)
        self.axiWidsld = ttk.Scale(self.pagectr[0], from_=1, to=400, variable=self.varXwidth, length=150)
        self.axiOffsld = ttk.Scale(self.pagectr[0], from_=0, to=400, variable=self.varXoffset, length=150)
        self.axiWidsld.grid(row=6, column=1, sticky=E+W)
        self.axiOffsld.grid(row=7, column=1, sticky=E+W)

        self.axiFWidlbl = ttk.Label(self.pagectr[0], text="Fine Width:", style='ControlsL.TLabel')
        self.axiFWidlbl.grid(row=8, column=0, sticky=E, pady=2, padx=2)
        self.allLabels['Controls.TLabel'].append(self.axiWidlbl)

        self.varXFwidth = tk.DoubleVar()
        self.varXFwidth.set(100)
        self.varXFwidth.trace('w', self.ploteeg)
        self.axiFWidsld = ttk.Scale(self.pagectr[0], from_=1, to=100, variable=self.varXFwidth, length=150)
        self.axiFWidsld.grid(row=8, column=1, sticky=E+W)

        self.domConsep = ttk.Separator(self.pagectr[0], style='Controls.TSeparator')
        self.domConsep.grid(row=9, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        self.domConlbl = ttk.Label(self.pagectr[0], text="Domain Controls", style='Controls.TLabel')
        self.domConlbl.grid(row=9, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.domConlbl)

        self.varPlot = 0
        self.switchbtn = ttk.Button(self.pagectr[0], text="Frequency", command=self.switchdomain)
        self.switchbtn.grid(row=10, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['TButton'].append(self.switchbtn)

        self.endsep0 = ttk.Separator(self.pagectr[0], style='Controls.TSeparator')
        self.endsep0.grid(row=11, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        # Page 0 - Time Domain Display
        for i, w in enumerate([1]):
            self.pagedis[0].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.pagedis[0].grid_rowconfigure(i, weight=w)

        self.timPlosep = ttk.Separator(self.pagedis[0], style='Display.TSeparator')
        self.timPlosep.grid(row=0, column=0, columnspan=2, sticky=E+W, pady=5, padx=200)
        self.disTimlbl = ttk.Label(self.pagedis[0], text="Time Domain Plot", style='Display.TLabel')
        self.disTimlbl.grid(row=0, column=0, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.disTimlbl)

        self.y1 = []
        self.ys1 = None
        self.fig1, self.axs1 = plt.subplots(1, 1)
        plt.tight_layout(pad=2)
        self.fig1.patch.set_facecolor('#F8C15A')

        self.eegline = FigureCanvasTkAgg(self.fig1, self.pagedis[0])
        self.eegline.get_tk_widget().grid(row=1, column=0, sticky=N+E+W+S, pady=5, padx=5)

        self.y2 = []
        self.ys2 = None
        self.fig2, self.axs2 = plt.subplots(1, 1)
        plt.tight_layout(pad=2)
        self.fig2.patch.set_facecolor('#F8C15A')

        self.eegfft = FigureCanvasTkAgg(self.fig2, self.pagedis[0])
        self.eegfft.get_tk_widget().grid(row=1, column=0, sticky=N+E+W+S, pady=5, padx=5)
        self.eegfft.get_tk_widget().grid_remove()

        self.fig1.canvas.mpl_connect('button_press_event', self.switchplot)
        self.fig2.canvas.mpl_connect('button_press_event', self.switchplot)

        # Page 1 - Feature Plot Control
        for i, w in enumerate([0]):
            self.pagectr[1].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0, 0, 1]):
            self.pagectr[1].grid_rowconfigure(i, weight=w)

        self.selMrksep = ttk.Separator(self.pagectr[1], style='Controls.TSeparator')
        self.selMrksep.grid(row=0, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        self.selMrklbl = ttk.Label(self.pagectr[1], text='Select Feature', style='Controls.TLabel')
        self.selMrklbl.grid(row=0, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.selMrklbl)

        self.varXax = tk.StringVar()
        self.varXax.trace('w', self.plotfeature)
        self.varYax = tk.StringVar()
        self.varYax.trace('w', self.plotfeature)
        self.mnuXaxlbl = ttk.Label(self.pagectr[1], text='X-Axis', style='ControlsL.TLabel')
        self.mnuXaxlbl.grid(row=1, column=0, sticky=E, pady=5, padx=5)
        self.allLabels['ControlsL.TLabel'].append(self.mnuXaxlbl)
        self.mnuYaxlbl = ttk.Label(self.pagectr[1], text='Y-Axis', style='ControlsL.TLabel')
        self.mnuYaxlbl.grid(row=2, column=0, sticky=E, pady=5, padx=5)
        self.allLabels['ControlsL.TLabel'].append(self.mnuYaxlbl)
        self.selXaxmnu = ttk.OptionMenu(self.pagectr[1], variable=self.varXax, style='TMenubutton')
        self.selXaxmnu.grid(row=1, column=1, sticky=W)
        self.allLabels['TMenubutton'].append(self.selXaxmnu)
        self.selYaxmnu = ttk.OptionMenu(self.pagectr[1], variable=self.varYax, style='TMenubutton')
        self.selYaxmnu.grid(row=2, column=1, sticky=W)
        self.allLabels['TMenubutton'].append(self.selYaxmnu)

        self.endsep1 = ttk.Separator(self.pagectr[1], style='Controls.TSeparator')
        self.endsep1.grid(row=3, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        # Page 1 - Feature Plot Display
        for i, w in enumerate([1]):
            self.pagedis[1].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.pagedis[1].grid_rowconfigure(i, weight=w)

        self.feaPlosep = ttk.Separator(self.pagedis[1], style='Display.TSeparator')
        self.feaPlosep.grid(row=0, column=0, sticky=E+W, pady=5, padx=50)
        self.feaPlolbl = ttk.Label(self.pagedis[1], text='Feature Plot', style='Display.TLabel')
        self.feaPlolbl.grid(row=0, column=0, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.feaPlolbl)

        self.fig3, self.axs3 = plt.subplots(1, 1)
        plt.tight_layout(pad=2)
        featplt = FigureCanvasTkAgg(self.fig3, self.pagedis[1])
        featplt.get_tk_widget().grid(row=1, sticky=N+E+W+S, pady=10, padx=10)
        self.fig3.patch.set_facecolor('#F8C15A')

        # Page 2 - Marked Data Control
        for i, w in enumerate([0, 1]):
            self.pagectr[2].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0, 1]):
            self.pagectr[2].grid_rowconfigure(i, weight=w)

        self.selMrksep = ttk.Separator(self.pagectr[2], style='Controls.TSeparator')
        self.selMrksep.grid(row=0, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        self.selMrklbl = ttk.Label(self.pagectr[2], text='Select Marker', style='Controls.TLabel')
        self.selMrklbl.grid(row=0, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.selMrklbl)

        self.varMrk = tk.IntVar()
        self.varMrk.set(0)
        self.varMrk.trace('w', self.plotmarker)
        self.mnuMrklbl = ttk.Label(self.pagectr[2], text='Marker', style='ControlsL.TLabel')
        self.mnuMrklbl.grid(row=1, column=0, sticky=E, pady=5, padx=5)
        self.allLabels['ControlsL.TLabel'].append(self.mnuMrklbl)
        self.selMrkmnu = ttk.OptionMenu(self.pagectr[2], variable=self.varMrk, style='TMenubutton')
        self.selMrkmnu.grid(row=1, column=1, sticky=W)
        self.allLabels['TMenubutton'].append(self.selMrkmnu)

        self.endsep2 = ttk.Separator(self.pagectr[2], style='Controls.TSeparator')
        self.endsep2.grid(row=2, column=0, columnspan=2, sticky=E+W, pady=5, padx=5)

        # Page 2 - Marked Data Display
        for i, w in enumerate([1]):
            self.pagedis[2].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.pagedis[2].grid_rowconfigure(i, weight=w)
        self.mrkPlosep = ttk.Separator(self.pagedis[2], style='Display.TSeparator')
        self.mrkPlosep.grid(row=0, column=0, sticky=E+W, pady=5, padx=50)

        self.mrkPlolbl = ttk.Label(self.pagedis[2], text='Marker Plot', style='Display.TLabel')
        self.mrkPlolbl.grid(row=0, column=0, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.mrkPlolbl)

        self.fig4, self.axs4 = plt.subplots(1, 1)
        plt.tight_layout(pad=2)
        markplt = FigureCanvasTkAgg(self.fig4, self.pagedis[2])
        markplt.get_tk_widget().grid(row=1, sticky=N+E+W+S, pady=10, padx=10)
        self.fig4.patch.set_facecolor('#F8C15A')

        # Page 3 - Train Classifier Controls
        for i, w in enumerate([1]):
            self.pagectr[3].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]):
            self.pagectr[3].grid_rowconfigure(i, weight=w)

        self.modConsep = ttk.Separator(self.pagectr[3], style='Controls.TSeparator')
        self.modConsep.grid(row=0, column=0, columnspan=3,  sticky=E+W, pady=5, padx=5)

        self.modConlbl = ttk.Label(self.pagectr[3], text='Model Controls', style='Controls.TLabel')
        self.modConlbl.grid(row=0, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.modConlbl)

        self.selTrabtn = ttk.Button(self.pagectr[3], text="Select Train", command=lambda x="Train": self.getcsv(x))
        self.selTrabtn.grid(row=1, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.selTrabtn)

        self.selTesbtn = ttk.Button(self.pagectr[3], text="Select Test", command=lambda x="Test": self.getcsv(x))
        self.selTesbtn.grid(row=2, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.selTesbtn)

        self.traModbtn = ttk.Button(self.pagectr[3], text="Train Model", command=self.train)
        self.traModbtn.grid(row=3, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.traModbtn)

        self.tstModbtn = ttk.Button(self.pagectr[3], text="Test Model", command=self.test)
        self.tstModbtn.grid(row=4, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.tstModbtn)

        self.savModbtn = ttk.Button(self.pagectr[3], text="Save Model", command=self.save)
        self.savModbtn.grid(row=5, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.savModbtn)

        self.filConsep = ttk.Separator(self.pagectr[3], style='Controls.TSeparator')
        self.filConsep.grid(row=6, column=0, columnspan=3, sticky=E + W, pady=5, padx=5)

        self.filConlbl = ttk.Label(self.pagectr[3], text='Filter Controls', style='Controls.TLabel')
        self.filConlbl.grid(row=6, column=0, columnspan=3, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.filConlbl)

        self.filHiglbl = ttk.Label(self.pagectr[3], text="High:", style='ControlsL.TLabel')
        self.filHiglbl.grid(row=7, column=0, sticky=E, pady=2, padx=0)
        self.allLabels['ControlsL.TLabel'].append(self.filHiglbl)

        self.filLowlbl = ttk.Label(self.pagectr[3], text="Low:", style='ControlsL.TLabel')
        self.filLowlbl.grid(row=8, column=0, sticky=E, pady=2, padx=0)
        self.allLabels['ControlsL.TLabel'].append(self.filLowlbl)

        self.filDurlbl = ttk.Label(self.pagectr[3], text="Duration:", style='ControlsL.TLabel')
        self.filDurlbl.grid(row=9, column=0, sticky=E, pady=2, padx=0)
        self.allLabels['ControlsL.TLabel'].append(self.filDurlbl)

        self.filPuslbl = ttk.Label(self.pagectr[3], text="Max Amplitude:", style='ControlsL.TLabel')
        self.filPuslbl.grid(row=10, column=0, sticky=E, pady=2, padx=0)
        self.allLabels['ControlsL.TLabel'].append(self.filPuslbl)

        self.varHighCut = tk.IntVar()
        self.varHighCut.set(100)
        self.varHighCut.trace('w', self.limitlower)
        self.filHigsld = ttk.Scale(self.pagectr[3], from_=1, to=250, variable=self.varHighCut, length=150)
        self.filHigsld.grid(row=7, column=1, sticky=E + W)

        self.varLowCut = tk.IntVar()
        self.varLowCut.set(1)
        self.varLowCut.trace('w', self.limitupper)
        self.filLowsld = ttk.Scale(self.pagectr[3], from_=1, to=250, variable=self.varLowCut, length=150)
        self.filLowsld.grid(row=8, column=1, sticky=E+W)

        self.varWindow = tk.IntVar()
        self.varWindow.set(4)
        self.varWindow.trace('w', self.updateduration)
        self.filWinsld = ttk.Scale(self.pagectr[3], from_=1, to=250, variable=self.varWindow, length=150)
        self.filWinsld.grid(row=9, column=1, sticky=E+W)

        self.varPulsemax = tk.IntVar()
        self.varPulsemax.set(15)
        self.varPulsemax.trace('w', self.updatepulse)
        self.filPussld = ttk.Scale(self.pagectr[3], from_=1, to=250, variable=self.varPulsemax, length=150)
        self.filPussld.grid(row=10, column=1, sticky=E+W)

        self.filHigval = ttk.Label(self.pagectr[3], text='50', style='ControlsL.TLabel')
        self.filHigval.grid(row=7, column=2, sticky=W, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.filHigval)

        self.filLowval = ttk.Label(self.pagectr[3], text='0.5', style='ControlsL.TLabel')
        self.filLowval.grid(row=8, column=2, sticky=W, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.filLowval)

        self.filDurval = ttk.Label(self.pagectr[3], text='4.0 s', style='ControlsL.TLabel')
        self.filDurval.grid(row=9, column=2, sticky=W, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.filDurval)

        self.filPusval = ttk.Label(self.pagectr[3], text='15 uV', style='ControlsL.TLabel')
        self.filPusval.grid(row=10, column=2, sticky=W, pady=2, padx=2)
        self.allLabels['ControlsL.TLabel'].append(self.filPusval)

        self.endsep3 = ttk.Separator(self.pagectr[3], style='Controls.TSeparator')
        self.endsep3.grid(row=11, column=0, columnspan=3, sticky=E+W, pady=5, padx=5)

        self.bar = ttk.Progressbar(self.pagectr[3])
        self.bar.grid(row=11, column=0, columnspan=3, sticky=E+W, pady=5, padx=5)
        self.bar.grid_remove()

        self.modFeasep = ttk.Separator(self.pagectr[3], style='Controls.TSeparator')
        self.modFeasep.grid(row=0, column=3, columnspan=2, sticky=E+W, pady=5, padx=5)
        self.modFealbl = ttk.Label(self.pagectr[3], text='Feature Selection', style='Controls.TLabel')
        self.modFealbl.grid(row=0, column=3, columnspan=2, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.modFealbl)

        self.includelist = tk.StringVar()
        self.excludelist = tk.StringVar()
        self.tstInclst = tk.Listbox(self.pagectr[3], selectmode='extended', listvariable=self.includelist)
        self.tstInclst.grid(row=1, column=3, rowspan=12, sticky=N+E+W+S, pady=10, padx=10)
        self.tstExclst = tk.Listbox(self.pagectr[3], selectmode='extended', listvariable=self.excludelist)
        self.tstExclst.grid(row=1, column=4, rowspan=12, sticky=N+E+W+S, pady=10, padx=10)

        self.tstExcbtn = ttk.Button(self.pagectr[3], text="Exclude", command=self.exclude)
        self.tstExcbtn.grid(row=13, column=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.tstExcbtn)

        self.tstIncbtn = ttk.Button(self.pagectr[3], text="Include", command=self.include)
        self.tstIncbtn.grid(row=13, column=4, pady=5, padx=5)
        self.allLabels['TButton'].append(self.tstIncbtn)

        self.tstRembtn = ttk.Button(self.pagectr[3], text="Exclude All", command=self.removefeat)
        self.tstRembtn.grid(row=14, column=3, pady=5, padx=5)
        self.allLabels['TButton'].append(self.tstRembtn)

        self.tstAddbtn = ttk.Button(self.pagectr[3], text="Include All", command=self.addfeat)
        self.tstAddbtn.grid(row=14, column=4, pady=5, padx=5)
        self.allLabels['TButton'].append(self.tstAddbtn)

        # Page 3 - Train Classifier Display
        for i, w in enumerate([0, 0, 0, 0, 0, 1]):
            self.pagedis[3].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0, 0, 0, 0, 0, 0, 1]):
            self.pagedis[3].grid_rowconfigure(i, weight=w)

        #self.claScosep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        #self.claScosep.grid(row=0, column=2, sticky=E+W, pady=5, padx=50)
        #self.claScolbl = ttk.Label(self.pagedis[3], text="Test Score by File", style='Display.TLabel')
        #self.claScolbl.grid(row=0, column=2, pady=5, padx=5)
        #self.allLabels['Display.TLabel'].append(self.claScolbl)

        self.traScosep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        self.traScosep.grid(row=0, column=0, columnspan=2, sticky=E+W, pady=5, padx=10)
        self.traScolbl = ttk.Label(self.pagedis[3], text="Training Score", style='Display.TLabel')
        self.traScolbl.grid(row=0, column=0, columnspan=2, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.traScolbl)

        self.senTralbl = ttk.Label(self.pagedis[3], text="Sensitivity:", style='DisplayL.TLabel')
        self.senTralbl.grid(row=1, column=0, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.senTralbl)

        self.speTralbl = ttk.Label(self.pagedis[3], text="Specificity:", style='DisplayL.TLabel')
        self.speTralbl.grid(row=2, column=0, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.speTralbl)

        self.posTralbl = ttk.Label(self.pagedis[3], text="Positive Predictive:", style='DisplayL.TLabel')
        self.posTralbl.grid(row=3, column=0, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.posTralbl)

        self.negTralbl = ttk.Label(self.pagedis[3], text="Negative Predictive:", style='DisplayL.TLabel')
        self.negTralbl.grid(row=4, column=0, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.negTralbl)

        self.perTrasep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        self.perTrasep.grid(row=5, column=0, columnspan=2, sticky=E+W, pady=5, padx=10)

        self.perTralbl = ttk.Label(self.pagedis[3], text="Overall Performance:", style='DisplayL.TLabel')
        self.perTralbl.grid(row=6, column=0, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.perTralbl)

        self.varSensTrain = tk.DoubleVar()
        self.varSpecTrain = tk.DoubleVar()
        self.varPospTrain = tk.DoubleVar()
        self.varNegpTrain = tk.DoubleVar()
        self.varPerfTrain = tk.DoubleVar()

        self.varSensTrain.set(0)
        self.varSpecTrain.set(0)
        self.varPospTrain.set(0)
        self.varNegpTrain.set(0)
        self.varPerfTrain.set(0)

        self.varPerfTrain.trace('w', self.updatetrainscore)

        self.senTraval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.senTraval.grid(row=1, column=1, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.senTraval)

        self.speTraval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.speTraval.grid(row=2, column=1, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.speTraval)

        self.posTraval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.posTraval.grid(row=3, column=1, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.posTraval)

        self.negTraval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.negTraval.grid(row=4, column=1, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.negTraval)

        self.perTraval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.perTraval.grid(row=6, column=1, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.perTraval)

        self.tesScosep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        self.tesScosep.grid(row=0, column=2, columnspan=2, sticky=E + W, pady=5, padx=10)
        self.tesScolbl = ttk.Label(self.pagedis[3], text="Testing Score", style='Display.TLabel')
        self.tesScolbl.grid(row=0, column=2, columnspan=2, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.tesScolbl)

        self.senTeslbl = ttk.Label(self.pagedis[3], text="Sensitivity:", style='DisplayL.TLabel')
        self.senTeslbl.grid(row=1, column=2, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.senTeslbl)

        self.speTeslbl = ttk.Label(self.pagedis[3], text="Specificity:", style='DisplayL.TLabel')
        self.speTeslbl.grid(row=2, column=2, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.speTeslbl)

        self.posTeslbl = ttk.Label(self.pagedis[3], text="Positive Predictive:", style='DisplayL.TLabel')
        self.posTeslbl.grid(row=3, column=2, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.posTeslbl)

        self.negTeslbl = ttk.Label(self.pagedis[3], text="Negative Predictive:", style='DisplayL.TLabel')
        self.negTeslbl.grid(row=4, column=2, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.negTeslbl)

        self.perTessep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        self.perTessep.grid(row=5, column=2, columnspan=2, sticky=E + W, pady=5, padx=10)

        self.perTeslbl = ttk.Label(self.pagedis[3], text="Overall Performance:", style='DisplayL.TLabel')
        self.perTeslbl.grid(row=6, column=2, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.perTeslbl)

        self.varSensTest = tk.DoubleVar()
        self.varSpecTest = tk.DoubleVar()
        self.varPospTest = tk.DoubleVar()
        self.varNegpTest = tk.DoubleVar()
        self.varPerfTest = tk.DoubleVar()

        self.varSensTest.set(0)
        self.varSpecTest.set(0)
        self.varPospTest.set(0)
        self.varNegpTest.set(0)
        self.varPerfTest.set(0)

        self.varPerfTest.trace('w', self.updatetestscore)

        self.senTesval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.senTesval.grid(row=1, column=3, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.senTesval)

        self.speTesval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.speTesval.grid(row=2, column=3, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.speTesval)

        self.posTesval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.posTesval.grid(row=3, column=3, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.posTesval)

        self.negTesval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.negTesval.grid(row=4, column=3, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.negTesval)

        self.perTesval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.perTesval.grid(row=6, column=3, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.perTesval)

        self.valScosep = ttk.Separator(self.pagedis[3], style='Display.TSeparator')
        self.valScosep.grid(row=0, column=4, columnspan=2, sticky=E + W, pady=5, padx=10)
        self.valScolbl = ttk.Label(self.pagedis[3], text="Validation Score", style='Display.TLabel')
        self.valScolbl.grid(row=0, column=4, columnspan=2, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.valScolbl)

        self.scoVallbl = ttk.Label(self.pagedis[3], text="Score:", style='DisplayL.TLabel')
        self.scoVallbl.grid(row=1, column=4, sticky=E, pady=1, padx=5)
        self.allLabels['DisplayL.TLabel'].append(self.scoVallbl)

        self.varPerfValid = tk.DoubleVar()
        self.varPerfValid.set(0)

        self.perValval = ttk.Label(self.pagedis[3], text='0.00%', style='DisplayL.TLabel')
        self.perValval.grid(row=1, column=5, sticky=W, pady=1, padx=2)
        self.allLabels['DisplayL.TLabel'].append(self.perValval)

        # self.tstCSVtxt = tk.Text(self.pagedis[3])
        # self.tstCSVtxt.grid(row=1, column=4, rowspan=8, sticky=N+E+W+S, pady=10, padx=10)

        # Page 4 - Histogram
        for i, w in enumerate([0]):
            self.pagectr[4].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 1]):
            self.pagectr[4].grid_rowconfigure(i, weight=w)

        self.hisctrsep = ttk.Separator(self.pagectr[4], style='Controls.TSeparator')
        self.hisctrsep.grid(row=0, column=0, sticky=E+W, pady=5, padx=5)

        self.hisctrlbl = ttk.Label(self.pagectr[4], text='No Controls', style='Controls.TLabel')
        self.hisctrlbl.grid(row=0, column=0, pady=5, padx=5)
        self.allLabels['Controls.TLabel'].append(self.hisctrlbl)

        self.endsep4 = ttk.Separator(self.pagectr[4], style='Controls.TSeparator')
        self.endsep4.grid(row=1, column=0, sticky=E+W, pady=5, padx=5)

        # Page 4 - Histogram
        for i, w in enumerate([1]):
            self.pagedis[4].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.pagedis[4].grid_rowconfigure(i, weight=w)
        self.hisPlosep = ttk.Separator(self.pagedis[4], style='Display.TSeparator')
        self.hisPlosep.grid(row=0, column=0, sticky=E+W, pady=5, padx=50)

        self.hisPlolbl = ttk.Label(self.pagedis[4], text='Histogram Plot', style='Display.TLabel')
        self.hisPlolbl.grid(row=0, column=0, pady=5, padx=5)
        self.allLabels['Display.TLabel'].append(self.hisPlolbl)

        self.fig5, self.axs5 = plt.subplots(1, 1)
        plt.tight_layout(pad=2)
        hisplt = FigureCanvasTkAgg(self.fig5, self.pagedis[4])
        hisplt.get_tk_widget().grid(row=1, sticky=N+E+W+S, pady=10, padx=10)
        self.fig5.patch.set_facecolor('#F8C15A')

        # List of Fonts
        self.fontlist = it.cycle(sorted(font.families()))

        # Test Parameter Flags
        self.useMark = False
        self.testing = ''

        # File Variables
        self.file = ''
        self.filename = ''
        self.filenumber = 0
        self.filelist = []
        self.folder = ''

        # Pre-processing DataFrames
        self.eegdf = pd.DataFrame()
        fftheading = ['Freq', 'EEG1fft', 'EEG2fft', 'EEG3fft', 'EEG4fft']
        self.fftdf = pd.DataFrame(columns=fftheading)

        # Features Extraction
        self.trainheading = []
        for sensor in ['1', '2', '3', '4']:
            for feat in ['delta', 'theta', 'alpha', 'beta', 'gamma', 'phi',
                         'theta/beta', 'theta/alpha', 'theta/phi',
                         'theta/(beta + alpha + gamma)', 'delta/(beta + alpha + gamma)',
                         'delta/alpha', 'delta/phi', 'delta/beta', 'delta/theta', '(theta + alpha)/beta']:
                self.trainheading.append('Sen{}-{}'.format(sensor, feat))
        self.trainheading.append('Class')
        self.trainheading.append('File')

        self.traindf = pd.DataFrame(columns=self.trainheading)
        self.testdf = pd.DataFrame(columns=self.trainheading)

        self.trainlist = []
        self.testlist = []

        self.minrow = [100000] * 5
        self.maxrow = [0] * 5

        self.X = None
        self.clf = None

    # |METHODS|----------------------------------------------------------------
    # -------------------------------------------------------------------------
    # initStyle
    #
    # Description:
    #       This method updates the ttk style object to modify the widgets.
    #
    # -------------------------------------------------------------------------
    def initstyle(self):
        # Colors
        uvicblue = '#005493'
        uvicdarkblue = '#002754'
        uvicyellow = '#F5AA1C'
        uvicred = '#C63527'
        fadeyellow = '#F8C15A'
        darkgrey = '#414141'

        # Ttk Style Settings
        self.style.theme_use('default')

        # Ttk Label Settings
        self.style.configure('Main.TLabel', foreground=uvicyellow, background=darkgrey, padding=[10, 10],
                             font=self.fontpreset['Title'])
        self.style.configure('Controls.TLabel', foreground=uvicyellow, background=uvicdarkblue, padding=[10, 10],
                             font=self.fontpreset['Heading'])
        self.style.configure('Display.TLabel', foreground=uvicdarkblue, background=fadeyellow, padding=[10, 10],
                             font=self.fontpreset['Heading'])
        self.style.configure('ControlsL.TLabel', foreground=uvicyellow, background=uvicdarkblue, padding=[5, 5],
                             font=self.fontpreset['Label'])
        self.style.configure('DisplayL.TLabel', foreground=uvicdarkblue, background=fadeyellow, padding=[5, 5],
                             font=self.fontpreset['Button'])

        # Ttk Style Separator Settings
        self.style.configure('Main.TSeparator', background=uvicyellow)
        self.style.configure('Controls.TSeparator', background=uvicyellow)
        self.style.configure('Display.TSeparator', background=uvicdarkblue)

        # Ttk Style Notebook Settings
        self.style.map('Main.TNotebook.Tab',
                       background=[('selected', uvicdarkblue),
                                   ('active', uvicblue)],
                       focuscolor=[('selected', uvicdarkblue),
                                   ('active', uvicblue)])
        self.style.configure('Main.TNotebook.Tab', font=self.fontpreset['Tab'], expand=[-2, 0, -2, 0], width=20,
                             padding=[10, 10], foreground=uvicyellow, background=darkgrey, focuscolor=darkgrey)
        self.style.configure('Main.TNotebook', tabmargins=[-6, 0, -6, 0], tabposition='wn', borderwidth=0, padding=[0],
                             background=darkgrey, lightcolor=darkgrey, darkcolor=darkgrey)

        # Ttk Style Frame Settings
        self.style.configure('TFrame', padding=[5, 5])
        self.style.configure('Main.TFrame', background=darkgrey, padding=[5, 5])
        self.style.configure('Page.TFrame', background=uvicdarkblue, bordercolor=darkgrey,
                             borderwidth=5, padding=[5, 5])
        self.style.configure('Controls.TFrame', background=uvicdarkblue, bordercolor=darkgrey,
                             borderwidth=5, padding=[5, 5])
        self.style.configure('Display.TFrame', background=fadeyellow, bordercolor=darkgrey,
                             borderwidth=5, relief=RIDGE, padding=[5, 5])

        # Ttk Style Scale Settings
        self.style.map('TScale', background=[('active', uvicred)])
        self.style.configure('TScale', background=uvicyellow, troughcolor=uvicblue)

        # Ttk Style Button Settings
        self.style.map('TButton', background=[('active', uvicred)])
        self.style.configure('TButton', padding=[5, 5], background=uvicyellow, foreground=uvicdarkblue,
                             font=self.fontpreset['Button'], width=15)
        self.style.map('TMenubutton', background=[('active', uvicred)])
        self.style.configure('TMenubutton', padding=[5, 5], background=uvicyellow, foreground=uvicdarkblue,
                             font=self.fontpreset['Button'], width=10)

        # Ttk Style Progressbar Settings
        self.style.configure('TProgressbar', background=uvicyellow, troughcolor=uvicblue)

        # Matplotlib.Pyplot Settings
        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.9, wspace=0, hspace=0)

    # -------------------------------------------------------------------------
    # switchplot
    #
    # Description:
    #       This method is used to cycle the displayed plot on page 2. Clicking
    # on the figure will draw the next set of data in the itertools objects.
    #
    # -------------------------------------------------------------------------
    def switchplot(self, event):
        # Matplotlib.Pyplot Settings
        plt.subplots_adjust(left=0.02, right=0.98, bottom=0.1, top=0.9, wspace=0, hspace=0.1)

        # Time Domain Plot
        self.axs1.cla()
        y1 = next(self.ys1)
        y1.plot(kind='line', x='Time', legend=True, ax=self.axs1, linewidth=0.3)
        self.axs1.set_title('Time Domain:{}'.format(self.file))
        self.axs1.set_xlabel('Time, [s]')
        self.axs1.set_ylabel('EEG Signal, [uV]')
        self.fig1.canvas.draw()

        # Frequency Domain Plot
        self.axs2.cla()
        y2 = next(self.ys2)
        y2.plot(kind='line', x='Freqp', legend=True, ax=self.axs2, linewidth=0.3)
        self.axs2.set_title('Frequency Domain:{}'.format(self.file))
        self.axs2.set_xlabel('Frequency, [Hz]')
        self.axs2.set_ylabel('EEG Amplitude, [uV]')
        self.fig2.canvas.draw()

        # Call to update the time axis variables
        self.ploteeg()

    # -------------------------------------------------------------------------
    # switchfont
    #
    # Description:
    #       This method is used to change the font of all text in the
    # application.
    #
    # -------------------------------------------------------------------------
    def switchfont(self, event):
        # Update the font presets to preserve the size and modifiers.
        new = next(self.fontlist)
        self.fontpreset['Title'][0] = new
        self.fontpreset['Tab'][0] = new
        self.fontpreset['Heading'][0] = new
        self.fontpreset['Label'][0] = new
        self.fontpreset['Button'][0] = new

        # Update the Widget Styles
        self.style.configure('Main.TLabel', font=self.fontpreset['Title'])
        self.style.configure('Controls.TLabel', font=self.fontpreset['Heading'])
        self.style.configure('Display.TLabel', font=self.fontpreset['Heading'])
        self.style.configure('ControlsL.TLabel', font=self.fontpreset['Label'])
        self.style.configure('DisplayL.TLabel', font=self.fontpreset['Label'])
        self.style.configure('Main.TNotebook.Tab', font=self.fontpreset['Tab'])
        self.style.configure('TButton', font=self.fontpreset['Button'])
        self.style.configure('TMenubutton', font=self.fontpreset['Button'])

        for style in ['Main.TLabel', 'Controls.TLabel', 'Display.TLabel', 'ControlsL.TLabel', 'DisplayL.TLabel',
                      'Main.TNotebook', 'TButton', 'TMenubutton']:
            for widget in self.allLabels[style]:
                widget.config(style=style)
        print(new)

    # -------------------------------------------------------------------------
    # limitlower
    #
    # Description:
    #       This method sets the lower limit for the higher cut-off frequency.
    #
    # -------------------------------------------------------------------------
    def limitlower(self, *args):
        self.varHighCut.set(int(self.varHighCut.get()))
        self.filLowsld.config(to=self.varHighCut.get())
        self.filHigval.config(text=self.varHighCut.get()/2)

    # -------------------------------------------------------------------------
    # limitupper
    #
    # Description:
    #       This method sets the lower limit for the higher cut-off frequency.
    #
    # -------------------------------------------------------------------------
    def limitupper(self, *args):
        self.varLowCut.set(int(self.varLowCut.get()))
        self.filHigsld.config(from_=self.varLowCut.get())
        self.filLowval.config(text=self.varLowCut.get()/2)

    # -------------------------------------------------------------------------
    # updateduration
    #
    # Description:
    #       This method sets the window for sample size.
    #
    # -------------------------------------------------------------------------
    def updateduration(self, *args):
        self.varWindow.set(int(self.varWindow.get()))
        self.filDurval.config(text="{} s".format(self.varWindow.get()))

    # -------------------------------------------------------------------------
    # updatepulse
    #
    # Description:
    #       This method sets the window for sample size.
    #
    # -------------------------------------------------------------------------
    def updatepulse(self, *args):
        self.varPulsemax.set(int(self.varPulsemax.get()))
        self.filPusval.config(text="{} uV".format(self.varPulsemax.get()))

    # -------------------------------------------------------------------------
    # updatetrainscore
    #
    # Description:
    #       This method updates the training score displayed on the GUI.
    #
    # -------------------------------------------------------------------------
    def updatetrainscore(self, *args):
        self.senTraval.config(text="{:.2f}%".format(self.varSensTrain.get() * 100))
        self.speTraval.config(text="{:.2f}%".format(self.varSpecTrain.get() * 100))
        self.posTraval.config(text="{:.2f}%".format(self.varPospTrain.get() * 100))
        self.negTraval.config(text="{:.2f}%".format(self.varNegpTrain.get() * 100))
        self.perTraval.config(text="{:.2f}%".format(self.varPerfTrain.get() * 100))
        self.perValval.config(text="{:.2f}%".format(self.varPerfValid.get() * 100))

    # -------------------------------------------------------------------------
    # updatetestscore
    #
    # Description:
    #       This method updates the testing score displayed on the GUI.
    #
    # -------------------------------------------------------------------------
    def updatetestscore(self, *args):
        self.senTesval.config(text="{:.2f}%".format(self.varSensTest.get() * 100))
        self.speTesval.config(text="{:.2f}%".format(self.varSpecTest.get() * 100))
        self.posTesval.config(text="{:.2f}%".format(self.varPospTest.get() * 100))
        self.negTesval.config(text="{:.2f}%".format(self.varNegpTest.get() * 100))
        self.perTesval.config(text="{:.2f}%".format(self.varPerfTest.get() * 100))

    # -------------------------------------------------------------------------
    # viewcsv
    #
    # Description:
    #       This method is used for selecting the data to plot on the page 0.
    #
    # -------------------------------------------------------------------------
    def viewcsv(self):
        # Select the file
        self.filename = filedialog.askopenfilename()
        self.file = os.path.basename(self.filename)

        # Read the file into a pandas data frame
        rawdf = pd.read_csv(self.filename)

        # Select the Desired Columns
        self.eegdf = rawdf[['Marker', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].copy()
        self.eegdf = self.eegdf.dropna()

        # Refresh the marker option based on marker values
        self.selMrkmnu['menu'].delete(0, 'end')
        for mark in sorted(rawdf.Marker.unique()):
            self.selMrkmnu['menu'].add_command(label=mark, command=lambda x=mark: self.varMrk.set(x))

        # Process the raw data
        self.getbands()

    # -------------------------------------------------------------------------
    # addfeat
    #
    # Description:
    #       This method resets the columns that the user previously excluded.
    #
    # -------------------------------------------------------------------------
    def addfeat(self):
        self.tstInclst.delete(0, END)
        self.tstExclst.delete(0, END)

        for column in sorted(self.trainheading[:-2]):
            self.tstInclst.insert(END, column)

        self.axupdate()

    # -------------------------------------------------------------------------
    # removefeat
    #
    # Description:
    #       This method resets the columns that the user previously excluded.
    #
    # -------------------------------------------------------------------------
    def removefeat(self):
        self.tstInclst.delete(0, END)
        self.tstExclst.delete(0, END)

        for column in self.trainheading[:-2]:
            self.tstExclst.insert(END, column)

        self.axupdate()

    # -------------------------------------------------------------------------
    # exclude
    #
    # Description:
    #       This method removes features to be used based on user selection.
    #
    # -------------------------------------------------------------------------
    def exclude(self):
        lst = sorted(self.tstInclst.curselection(), reverse=True)
        for item in lst:
            self.tstExclst.insert(END, self.tstInclst.get(item))
            self.tstInclst.delete(item)

        sort = sorted(self.tstExclst.get(0, END))
        self.tstExclst.delete(0, END)
        for item in sort:
            self.tstExclst.insert(END, item)

        self.axupdate()

    # -------------------------------------------------------------------------
    # include
    #
    # Description:
    #       This method includes features to be used based on user selection.
    #
    # -------------------------------------------------------------------------
    def include(self):
        list = sorted(self.tstExclst.curselection(), reverse=True)
        for item in list:
            self.tstInclst.insert(END, self.tstExclst.get(item))
            self.tstExclst.delete(item)

        sort = sorted(self.tstInclst.get(0, END))
        self.tstInclst.delete(0, END)
        for item in sort:
            self.tstInclst.insert(END, item)

        self.axupdate()

    # -------------------------------------------------------------------------
    # axupdate
    #
    # Description:
    #       This method updates the axis options for the feature plots.
    #
    # -------------------------------------------------------------------------
    def axupdate(self):
        self.selXaxmnu['menu'].delete(0, 'end')
        self.selYaxmnu['menu'].delete(0, 'end')
        for item in self.tstInclst.get(0, END):
            self.selXaxmnu['menu'].add_command(label=item, command=lambda x=item: self.varXax.set(x))
            self.selYaxmnu['menu'].add_command(label=item, command=lambda x=item: self.varYax.set(x))

    # -------------------------------------------------------------------------
    # getcsv
    #
    # Description:
    #       This method is used for selecting the data folders.
    #
    # -------------------------------------------------------------------------
    def getcsv(self, test):
        # Select the training data folder
        self.folder = filedialog.askdirectory(title="Select the Folder with the {}ing Data".format(test))
        if test == "Test":
            # Select the output folder
            self.testlist = []
        if test == "Train":
            self.trainlist = []
            self.addfeat()

        self.minrow = [100000] * 5
        self.maxrow = [0] * 5
        self.filelist = iter(sorted(os.listdir(self.folder)))
        self.bar.grid()
        self.bar.config(maximum=len(os.listdir(self.folder)), value=0)
        self.testing = test

        self.master.after(1, self.collectcsv)

    def collectcsv(self):
        self.file = next(self.filelist, "end")
        if self.file != "end":
            self.bar.step()
            self.bar.update_idletasks()
            self.mainpage.update_idletasks()
            self.filename = "{}/{}".format(self.folder, self.file)

            # Read the file into a pandas data frame
            rawdf = pd.read_csv(self.filename)

            # Select the Desired Columns
            self.eegdf = rawdf[['Marker', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].copy()
            self.eegdf = self.eegdf.dropna()
            # Prepare the
            self.filenumber = int(''.join(c for c in self.file if c.isdigit()))
            feats = self.preprocess()
            if self.testing == "Train":
                self.trainlist.extend(feats)
            else:
                self.testlist.extend(feats)

            # Test the Data
            self.master.after(1, self.collectcsv)
        else:
            self.bar.grid_remove()

    # -------------------------------------------------------------------------
    # switchdomain
    #
    # Description:
    #       This method is used for switching the plot displayed.
    #
    # -------------------------------------------------------------------------
    def switchdomain(self):
        if self.varPlot:
            self.switchbtn.config(text='Frequency')
            self.disTimlbl.config(text='Time Domain Plot')
            self.eegfft.get_tk_widget().grid_remove()
            self.eegline.get_tk_widget().grid()
            self.varPlot = 0
        else:
            self.switchbtn.config(text='Time')
            self.disTimlbl.config(text='Frequency Domain Plot')
            self.eegline.get_tk_widget().grid_remove()
            self.eegfft.get_tk_widget().grid()
            self.varPlot = 1

    # -------------------------------------------------------------------------
    # preprocess
    #
    # Description:
    #       This method does all the pre-processing before extracting features.
    #
    # -------------------------------------------------------------------------
    def preprocess(self):
        fs = 250
        window = self.varWindow.get()
        pulsemax = self.varPulsemax.get()
        datalist = []

        # Change the 20 into a variable
        if self.useMark:
            self.eegdf = self.eegdf.loc[(self.eegdf['Marker'] < 20)].copy()
            self.eegdf.reset_index(inplace=True)

        # Signal Pre-Processing
        [b, a] = signal.butter(4, [self.varLowCut.get() / fs, self.varHighCut.get() / fs], btype='bandpass')
        self.eegdf['Total'] = 0
        self.eegdf = (self.eegdf - self.eegdf.mean())*1.64498               # Convert into uV
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])        # Apply the bandpass filter
        self.eegdf['Total'] = self.eegdf.abs().mean(axis=1)                 # Record the Average Amplitude

        # Remove High Amplitude Spikes
#        for i in range(0, 10, 1):
#            if not (self.eegdf['Total'] > pulsemax).sum():
#                break
        while (self.eegdf['Total'] > pulsemax).sum():
            self.eegdf = self.eegdf[self.eegdf['Total'] < pulsemax].copy()
            for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
                self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])
            self.eegdf['Total'] = self.eegdf.abs().mean(axis=1)             # Record the Average Amplitude

        self.eegdf.reset_index(inplace=True)
        size = self.eegdf.shape[0]

        # Add a time column 250 Hz
        time = np.linspace(0, size/fs, size)
        self.eegdf.insert(0, "Time", time)

        # Prepare the Frequency Data Frame
        self.fftdf['Freq'] = np.linspace(0.0, fs / 2, fs*window // 2 + 1)
        self.fftdf.set_index("Freq")

        for i in range(0, size, window*fs):
            df = self.eegdf.iloc[i:i+window*fs]
            N = df.shape[0]
            for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
                if df[col].shape[0]:
                    fft = fftpack.fft(df[col].to_numpy())[0:N // 2 + 1]
                    fft = 1 / (fs * N) * np.abs(fft) ** 2
                    fft[2:-2] = [2 * x for x in fft[2:-2]]
                    self.fftdf[col + 'fft'] = pd.Series(fft)
            if N:
                datalist.append(self.extractfeatures(self.fftdf))

        return datalist

    # -------------------------------------------------------------------------
    # getbands
    #
    # Description:
    #       This method splits the data in the bands of interest. Before
    # calculating the next band, the lower frequency bands are subtracted.
    #
    # -------------------------------------------------------------------------
    def getbands(self):
        fs = 250
        fband = [4, 8, 15, 32, 100]
        wband = [2 * x / fs for x in fband]
        pulsemax = self.varPulsemax.get()

        # Change the 20 into a variable
        if self.useMark:
            self.eegdf = self.eegdf[(self.eegdf['Marker'] < 20)].copy()
            self.eegdf.reset_index(inplace=True)

        # Signal Pre-Processing
        [b, a] = signal.butter(4, [self.varLowCut.get() / fs, self.varHighCut.get() / fs], btype='bandpass')
        self.eegdf['Total'] = 0

        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            self.eegdf[col + 'Raw'] = self.eegdf[col].copy()
            self.eegdf[col] -= 800# self.eegdf[col].mean()                       # Remove the mean offset (~800 Muse Units)
            self.eegdf.loc[:, col] *= 1.64498                               # Convert into uV
            self.eegdf[col + 'uV'] = self.eegdf[col].copy()
            self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])        # Apply the bandpass filter
            self.eegdf[col + 'Filter'] = self.eegdf[col].copy()
            self.eegdf['Total'] += abs(self.eegdf[col]) / 4                 # Record the Average Amplitude

        # Remove High Amplitude Spikes
        self.eegdf = self.eegdf[self.eegdf['Total'] < pulsemax].copy()
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])
        #while not self.eegdf[self.eegdf['Total'] > 15].copy().empty:
        #    self.eegdf = self.eegdf[self.eegdf['Total'] < 15].copy()        # Remove High Amplitude Samples
        #    self.eegdf['Total'] = 0                                         # Reset the Average Amplitude
        #    for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
        #        self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])    # Re-apply bandpass filter
        #        self.eegdf['Total'] += abs(self.eegdf[col]) / 4             # Record Average Amplitude

        self.eegdf.reset_index(inplace=True)
        size = self.eegdf.shape[0]

        # Plot a Histogram of the Signal Amplitude
        self.fig5.gca().hist(self.eegdf['Total'], bins=100, log=True)
        self.axs5.set_title('Histogram'.format(self.file))
        self.axs5.set_xlabel('Difference')
        self.axs5.set_ylabel('Occurrences')
        self.fig5.canvas.draw()

        # Add a time column 250 Hz
        time = [1/fs * x for x in range(0, size)]
        self.eegdf.insert(0, "Time", time)

        # Adjust the X Axis Control Widgets
        self.axiWidsld.config(to=self.eegdf["Time"].max())
        self.varXoffset.set(self.eegdf["Time"].max()/2)
        self.varXwidth.set(self.eegdf["Time"].max())

        b = [None] * 5
        a = [None] * 5
        for i, band in enumerate(wband):
            [b[i], a[i]] = signal.butter(4, band)

        # Separate the desired bands into EEG Bands
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            # First EEG Band Delta 0-4 Hz
            self.eegdf[col + 'Delta'] = self.eegdf[col]
            self.eegdf[col + 'Delta'] = signal.filtfilt(b[0], a[0], self.eegdf[col+'Delta'])

            # Second EEG Band Theta 4-8 Hz
            self.eegdf[col + 'Theta'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta'])
            self.eegdf[col + 'Theta'] = signal.filtfilt(b[1], a[1], self.eegdf[col+'Theta'])

            # Third EEG Band Alpha 8-15 Hz
            self.eegdf[col + 'Alpha'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta'])
            self.eegdf[col + 'Alpha'] = signal.filtfilt(b[2], a[2], self.eegdf[col+'Alpha'])

            # Fourth EEG Band Beta 15-32 Hz
            self.eegdf[col + 'Beta'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta']) \
                .subtract(self.eegdf[col + 'Alpha'])
            self.eegdf[col + 'Beta'] = signal.filtfilt(b[3], a[3], self.eegdf[col+'Beta'])

            # Fifth EEG Band Gamma +32 Hz
            self.eegdf[col + 'Gamma'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta']) \
                .subtract(self.eegdf[col + 'Alpha']) \
                .subtract(self.eegdf[col + 'Beta'])
            self.eegdf[col + 'Gamma'] = signal.filtfilt(b[4], a[4], self.eegdf[col+'Gamma'])

        # Plot the Time Domain
        self.y1 = []
        for i, band in enumerate(['', 'Raw', 'uV', 'Filter', 'Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']):
            self.y1.append(self.eegdf[['Time', 'EEG1'+band, 'EEG2'+band, 'EEG3'+band, 'EEG4'+band]].copy()) # 'Total'

        self.ys1 = it.cycle(self.y1)

        # Plot the Fourier Transform
        self.eegdf['Freqp'] = pd.Series(np.linspace(0.0, fs / 2, size // 2))

        self.y2 = []
        for i, band in enumerate(['', 'Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']):
            for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
                fft = fftpack.fft(self.eegdf[col+band].to_numpy())[0:size // 2 + 1]
                fft = 1/(fs*size) * np.abs(fft)**2
                fft[2:-2] = [2 * x for x in fft[2:-2]]
                self.eegdf[col + band + 'fftp'] = pd.Series(fft)
            self.y2.append(self.eegdf[['Freqp',
                                       'EEG1' + band + 'fftp',
                                       'EEG2' + band + 'fftp',
                                       'EEG3' + band + 'fftp',
                                       'EEG4' + band + 'fftp']].copy())

        self.ys2 = it.cycle(self.y2)

        # Call to plot the graph
        self.switchplot(None)

    # -------------------------------------------------------------------------
    # ploteeg
    #
    # Description:
    #       This method draws the EEG data.
    #
    # -------------------------------------------------------------------------
    def ploteeg(self, *args):
        self.axiOffsld.config(from_=self.varXwidth.get()/2, to=self.axiWidsld['to'] - self.varXwidth.get()/2)
        width = self.varXwidth.get() * self.varXFwidth.get() / 100
        lowlim = self.varXoffset.get() - width/2
        upperlim = lowlim + width
        self.axs1.set_xlim(lowlim, upperlim)
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

    # -------------------------------------------------------------------------
    # plotfeature
    #
    # Description:
    #       This method draws the EEG data.
    #
    # -------------------------------------------------------------------------
    def plotfeature(self, *args):
        self.axs3.cla()
        x = self.varXax.get()
        y = self.varYax.get()
        if x in self.traindf.columns and y in self.traindf.columns:
            self.traindf.loc[self.traindf['Class'] == "Fatigued"].plot.scatter(x=x, y=y, c='red', ax=self.axs3, s=0.2)
            self.traindf.loc[self.traindf['Class'] == "Not Fatigued"].plot.scatter(x=x, y=y, c='blue', ax=self.axs3,
                                                                                   s=0.2)
            self.fig3.canvas.draw()

    # -------------------------------------------------------------------------
    # plotmarker
    #
    # Description:
    #       This method draws the EEG data.
    #
    # -------------------------------------------------------------------------
    def plotmarker(self, *args):
        self.axs4.cla()
        df = self.eegdf.loc[self.eegdf['Marker'] == self.varMrk.get()]
        df[['Time', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].plot(kind='line', x='Time', legend=False, ax=self.axs4)

    # -------------------------------------------------------------------------
    # extractfeatures
    #
    # Description:
    #       This method extracts features from the data.
    #
    # -------------------------------------------------------------------------
    def extractfeatures(self, freqdf):
        # Holds the features for Machine Learning
        feat = []

        # Split the Data Frame by the EEG Bands
        window = self.varWindow.get()

        deltamean = freqdf.iloc[:4*window].mean()
        thetamean = freqdf.iloc[4*window+1:8*window].mean()
        alphamean = freqdf.iloc[8*window+1:15*window].mean()
        betamean = freqdf.iloc[15*window+1:32*window].mean()
        gammamean = freqdf.iloc[32*window+1:].mean()
        freqmean = freqdf.mean()

        for sensor in ['EEG1fft', 'EEG2fft', 'EEG3fft', 'EEG4fft']:
            delta = deltamean[sensor]
            theta = thetamean[sensor]
            alpha = alphamean[sensor]
            beta = betamean[sensor]
            gamma = gammamean[sensor]
            phi = freqmean[sensor]

            feat.extend([delta, theta, alpha, beta, gamma, phi, theta/beta, theta/alpha, theta/phi,
                         theta/(beta + alpha + gamma), delta/(beta + alpha + gamma), delta/alpha, delta/phi,
                         delta/beta, delta/theta, (theta + alpha)/beta])

        # Check for 'Early' for the old dataset.
        # Check for 'pre' for the new Mining Dataset
        mental = "Not Fatigued" if 'pre' in self.filename else "Fatigued"
        if self.testing == "Train":
            feat.extend([mental, self.filenumber % 5])
        else:
            feat.extend([mental, self.filenumber])
        return feat

    # -------------------------------------------------------------------------
    # train
    #
    # Description:
    #       This method trains the classifier.
    #
    # -------------------------------------------------------------------------
    def train(self):
        self.traindf = pd.DataFrame(self.trainlist, columns=self.trainheading)
        self.traindf = self.traindf.dropna()
        self.X = self.traindf.loc[:, self.tstInclst.get(0, END)].copy()
        x = (self.X - self.X.mean(axis=0))/self.X.std(axis=0)

        x = x.to_numpy()
        y = self.traindf.loc[:, "Class"].to_numpy()

        # Hyperparameters to Test
        #param_grid = {'C': [0.008, 0.009, 0.01, 0.012, 0.013],
        #              'gamma': [0.008, 0.009, 0.01, 0.012, 0.013],
        param_grid = {'C': [1],
                      'gamma': ['scale'],
                      'kernel': ['rbf'],
                      'class_weight': ['balanced']}

        # Cross Validation Split by 5 -> Split by File Number % 5
        group = PredefinedSplit(self.traindf['File'].tolist())
        clf = SVC(kernel='rbf')

        self.clf = GridSearchCV(clf, param_grid, refit=True, verbose=3, n_jobs=-1, pre_dispatch=8, cv=group)
        self.clf.fit(x, y)

        self.varPerfValid.set(self.clf.best_score_)
        print(self.clf.best_estimator_)
        predict = self.clf.predict(x)
        sens, spec, posp, negp = self.evaluate(y, predict)

        self.varSensTrain.set(sens)
        self.varSpecTrain.set(spec)
        self.varPospTrain.set(posp)
        self.varNegpTrain.set(negp)

        self.varPerfTrain.set((sens * spec) ** (1 / 2))

    # -------------------------------------------------------------------------
    # test
    #
    # Description:
    #       This method tests the classifier.
    #
    # -------------------------------------------------------------------------
    def test(self):
        self.testdf = pd.DataFrame(self.testlist, columns=self.trainheading)
        self.testdf = self.testdf.dropna()

        # Prepare Test Matrix
        x = self.testdf.loc[:, self.tstInclst.get(0, END)].copy()
        x = (x - self.X.mean(axis=0)) / self.X.std(axis=0)
        x = x.to_numpy()

        # Set Grand Truth Aside
        y = self.testdf.loc[:, "Class"].to_numpy()

        # Evaluate the Classifier
        predict = self.clf.predict(x)
        sens, spec, posp, negp = self.evaluate(y, predict)

        self.varSensTest.set(sens)
        self.varSpecTest.set(spec)
        self.varPospTest.set(posp)
        self.varNegpTest.set(negp)

        self.varPerfTest.set((sens * spec) ** (1 / 2))
        # Reset the Test Data Frame and List
        self.testdf = self.testdf.iloc[0:0]
        # self.testlist = []

    # -------------------------------------------------------------------------
    # test
    #
    # Description:
    #       This method saves the trained model with a pickler.
    #
    # -------------------------------------------------------------------------
    def save(self):
        # Save the trained model.
        pd.DataFrame(self.trainlist, columns=self.trainheading).dropna().to_csv('trainlist.csv')
        pd.DataFrame(self.testlist, columns=self.trainheading).dropna().to_csv('testlist.csv')
        filename = 'finalized_model.sav'
        pk.dump(self.clf.best_estimator_, open(filename, 'wb'))
        mean = self.X.mean(axis=0)
        var = self.X.std(axis=0)
        pk.dump(mean, open('mean.sav', 'wb'))
        pk.dump(var, open('var.sav', 'wb'))

    # -------------------------------------------------------------------------
    # test
    #
    # Description:
    #       This method tests the classifier.
    #
    # -------------------------------------------------------------------------
    def evaluate(self, truth, predict):
        tn, fp, fn, tp = confusion_matrix(truth, predict, labels=["Fatigued", "Not Fatigued"]).ravel()
        print(tn, tp, fn, fp)
        sensitivity = tn / (tn + fp)
        specificity = tp / (tp + fn)
        pospred = tn / (tn + fn)
        negpred = tp / (tp + fp)
        return sensitivity, specificity, pospred, negpred

    # -------------------------------------------------------------------------
    # onClose
    #
    # Description:
    #       This method closes the application.
    #
    # -------------------------------------------------------------------------
    def onClose(self, event):
        self.master.quit()


if __name__ == "__main__":
    # Profiler Start
    useProfile = False
    if useProfile:
        pr = cProfile.Profile()
        pr.enable()

    root = tk.Tk()
    game = EegGui(master=root)
    root.mainloop()
    root.quit()

    # Profiler End
    if useProfile:
        pr.disable()
        s = io.StringIO()
        sortby = SortKey.CUMULATIVE
        ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
        ps.print_callees(.05)
        print(s.getvalue())
    sys.exit(0)

