# |ECE 499: Classifier|--------------------------------------------------------
#
# Project: Brain Assessment for Mental Fatigue
# Program: Machine Learning Classifier (v1.200522)
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
# Version 1.200522 - Isaiah Regacho
#    - Script adopted from original ECE 399 project
#    - Added description blocks for each method.
# Version 1.200524 - Austin Weir
#    - Test
# -----------------------------------------------------------------------------

# |MODULES|--------------------------------------------------------------------
from tkinter import *
from tkinter.ttk import *
from tkinter import filedialog
import pandas
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from scipy import signal, fftpack
import numpy as np
from sklearn.svm import SVC
import xlsxwriter
import cProfile, pstats, io
from pstats import SortKey
import os
import itertools


class EEG_GUI():
    def __init__(self, master=None):
        self.master = master
        self.p = 0
        self.clf = SVC(gamma='auto', kernel='rbf')
        self.filename = ""
        self.rawdf = pandas.DataFrame()
        self.eegdf = pandas.DataFrame()
        self.trainheading = []
        for sensor in ['1', '2', '3', '4']:
            for feat in range(1, 13):
                self.trainheading.append('Sen{}F{}'.format(sensor, feat))
        self.trainheading.append('Class')
        self.traindf = pandas.DataFrame(columns=self.trainheading)
        self.testdf = pandas.DataFrame(columns=self.trainheading)
        fftheading = ['Freq', 'EEG1fft', 'EEG2fft', 'EEG3fft', 'EEG4fft']
        self.fftdf = pandas.DataFrame(columns=fftheading)
        self.n = 0
        self.m = 0

        self.master.title("ECE 399 BAMF GUI")
        self.master.geometry("1800x800")
        self.master.rowconfigure(0, weight=1)
        self.master.columnconfigure(0, weight=1)

        self.pageTitle = ["Select Data", "Time Domain", "Frequency Domain", "Marked Data", "Training Data"]

        self.mainpage = Frame(self.master)
        self.mainpage.grid_rowconfigure(1, weight=1)
        self.mainpage.grid_columnconfigure(0, weight=1)
        self.mainpage.grid(sticky=N+E+W+S)

        self.title = Label(self.mainpage, text="Brain Assessment of Mental Fatigue", font="Arial 20 bold")
        self.title.grid(row=0)
        s = Style()
        s.configure('TNotebook.Tab', font=('Arial', '16'), padding=[50, 10])
        self.note = Notebook(self.mainpage)
        self.note.grid(row=1, sticky=N+E+W+S, padx=10, pady=10)

        plt.subplots_adjust(left=0.05, right=0.95, bottom=0.1, top=0.9, wspace=1.2, hspace=1.2)


        self.page = []
        for title in self.pageTitle:
            frm = Frame(self.note)
            frm.grid_rowconfigure(0, weight=1)
            frm.grid_columnconfigure(0, weight=1)
            frm.grid(sticky=N+E+W+S)
            self.page.append(frm)
            self.note.add(frm, text=title, sticky=N+E+W+S)

        # Page 0
        for i, w in enumerate([0, 1]):
            self.page[0].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.page[0].grid_rowconfigure(i, weight=w)

        self.ctrCSVfrm = Frame(self.page[0])
        self.ctrCSVfrm.grid(row=0, column=0, sticky=N, rowspan=2)
        self.ctrCSVlbl = Label(self.ctrCSVfrm, text="Data Selection Controls", font="Arial 14 bold")
        self.ctrCSVlbl.grid(row=0, pady=10, padx=10)
        self.getCSVbtn0 = Button(self.ctrCSVfrm, text="Get CSV", command=lambda x="Train": self.getCSV(x))
        self.getCSVbtn0.grid(row=1)
        self.preCSVbtn0 = Button(self.ctrCSVfrm, text="Preview CSV", command=lambda x="Preview": self.getCSV(x))
        self.preCSVbtn0.grid(row=2)

        self.preCSVlbl = Label(self.page[0], text="Data Preview", font="Arial 14 bold")
        self.preCSVlbl.grid(row=0, column=1, pady=10, padx=10)
        self.preCSVtxt0 = Text(self.page[0])
        self.preCSVtxt0.grid(row=1, column=1, sticky=N+E+W+S)


        # Page 1
        self.ctrTimfrm = Frame(self.page[1])
        self.ctrTimfrm.grid(row=0, column=0, padx=10, pady=10, sticky=N+E+W+S)
        for i, w in enumerate([0, 1]):
            self.ctrTimfrm.grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 0]):
            self.ctrTimfrm.grid_rowconfigure(i, weight=w)

        self.ctrXaxlbl = Label(self.ctrTimfrm, text="X Axis Controls", font="Arial 14 bold")
        self.ctrXaxlbl.grid(row=0, column=0, columnspan=2)
        self.widXaxlbl = Label(self.ctrTimfrm, text="Width:", font="Arial 12")
        self.widXaxlbl.grid(row=1, column=0)
        self.offXaxlbl = Label(self.ctrTimfrm, text="Offset:", font="Arial 12")
        self.offXaxlbl.grid(row=2, column=0)
        self.preCSVbtn1 = Button(self.ctrTimfrm, text="Preview CSV", command=lambda x="Preview": self.getCSV(x))
        self.preCSVbtn1.grid(row=3)
        self.varXwidth = DoubleVar()
        self.varXoffset = DoubleVar()
        self.varXwidth.set(400)
        self.varXwidth.trace('w', self.plotEEG)
        self.varXoffset.trace('w', self.plotEEG)
        self.widXaxsld1 = Scale(self.ctrTimfrm, from_=0, to=400, variable=self.varXwidth)
        self.offXaxsld1 = Scale(self.ctrTimfrm, from_=0, to=400, variable=self.varXoffset)
        self.widXaxsld1.grid(row=1, column=1, sticky=N+E+W+S)
        self.offXaxsld1.grid(row=2, column=1, sticky=N+E+W+S)
        self.page[1].grid_rowconfigure(0, weight=0)
        self.page[1].grid_rowconfigure(2, weight=1)

        self.y1 = []
        self.fig1, self.axs1 = plt.subplots(1, 1)

        eegline = FigureCanvasTkAgg(self.fig1, self.page[1])
        eegline.get_tk_widget().grid(row=2, sticky=N+E+W+S)

        cid1 = self.fig1.canvas.mpl_connect('button_press_event', self.onclick)

        # Page 2
        self.y2 = []
        self.fig2, self.axs2 = plt.subplots(1, 1)

        eegfft = FigureCanvasTkAgg(self.fig2, self.page[2])
        eegfft.get_tk_widget().grid(row=0, sticky=N+E+W+S)

        cid2 = self.fig2.canvas.mpl_connect('button_press_event', self.onclick)

        # Page 3 - Parse by marker and band
        for i, w in enumerate([1]):
            self.page[3].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 1]):
            self.page[3].grid_rowconfigure(i, weight=w)

        self.ctrMrkfrm = Frame(self.page[3])
        self.ctrMrkfrm.grid(sticky=N+E+W+S)
        for i, w in enumerate([1, 1]):
            self.ctrMrkfrm.grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0]):
            self.ctrMrkfrm.grid_rowconfigure(i, weight=w)
        self.ctrMrklbl = Label(self.ctrMrkfrm, text='Marked Data Control', font='Arial 14 bold')
        self.ctrMrklbl.grid(row=0, column=0, columnspan=2)

        self.varMrk = IntVar()
        self.varMrk.set(0)
        self.varMrk.trace('w', self.plotMarker)
        self.selMrklbl = Label(self.ctrMrkfrm, text='Marker', font='Arial 12')
        self.selMrklbl.grid(row=1, column=0, sticky=E)
        self.selMrkmnu = OptionMenu(self.ctrMrkfrm, variable=self.varMrk)
        self.selMrkmnu.grid(row=1, column=1, sticky=W)


        self.fig3, self.axs3 = plt.subplots(1, 1)
        eegtrain = FigureCanvasTkAgg(self.fig3, self.page[3])
        eegtrain.get_tk_widget().grid(row=1, sticky=N+E+W+S)

        # Page 4
        for i, w in enumerate([1, 1]):
            self.page[4].grid_columnconfigure(i, weight=w)
        for i, w in enumerate([0, 0, 1]):
            self.page[4].grid_rowconfigure(i, weight=w)
        self.traDatlbl = Label(self.page[4], text="Training Data", font="Arial 14 bold")
        self.traDatlbl.grid(row=0, column=0, columnspan=2)
        self.tryModbtn = Button(self.page[4], text="Test Model", command=lambda x="Test": self.getCSV(x))
        self.tryModbtn.grid(row=1, column=0)
        self.traModbtn = Button(self.page[4], text="Train Model", command=self.train)
        self.traModbtn.grid(row=1, column=1)
        self.traCSVtxt = Text(self.page[4])
        self.traCSVtxt.grid(row=2, column=0, sticky=N+E+W+S)
        self.tstCSVtxt = Text(self.page[4])
        self.tstCSVtxt.grid(row=2, column=1, sticky=N+E+W+S)

    # |METHODS|----------------------------------------------------------------
    # -------------------------------------------------------------------------
    # onclick
    #
    # Description:
    #       This method is used to cycle the displayed plot on page 2. Clicking
    # on the figure will draw the next set of data in the itertools objects.
    #
    # -------------------------------------------------------------------------
    def onclick(self, event):
        self.axs1.cla()
        self.axs2.cla()
        y1 = next(self.ys1)
        y2 = next(self.ys2)
        y1.plot(kind='line', x='Time', legend=True, ax=self.axs1, linewidth=0.2)
        y2.plot(kind='line', x='Freqp', legend=True, ax=self.axs2, linewidth=0.2)
        self.axs1.set_title('Time Domain:{}'.format(self.file))
        self.axs2.set_title('Frequency Domain:{}'.format(self.file))
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

    # -------------------------------------------------------------------------
    # getCSV
    #
    # Description:
    #       This method is used for selecting the data.
    #
    # -------------------------------------------------------------------------
    def getCSV(self, test):
        if test == "Preview":
            self.axs1.cla()
            self.axs2.cla()
            self.axs3.cla()
            self.filename = filedialog.askopenfilename()
            self.file = os.path.basename(self.filename)

            self.getRawData()
            self.selMrkmnu['menu'].delete(0, 'end')
            for mark in sorted(self.rawdf.Marker.unique()):
                self.selMrkmnu['menu'].add_command(label=mark, command=lambda x=mark: self.varMrk.set(x))
            self.getBands(test)

        else:
            self.folder = filedialog.askdirectory()
            self.tstCSVtxt.delete(1.0, END)
            for file in sorted(os.listdir(self.folder)):
                self.file = file
                self.filename = "{}/{}".format(self.folder, file)
                self.getRawData()
                self.getData(test)

                if  test == "Test":
                    self.test()

            if test == "Train":
                self.traCSVtxt.delete(1.0, END)
                self.traCSVtxt.insert(INSERT, self.traindf)
                self.traCSVtxt.update_idletasks()

    # -------------------------------------------------------------------------
    # getRawData
    #
    # Description:
    #       This method is used for converting the .csv files into pandas data
    # frames.
    #
    # -------------------------------------------------------------------------
    def getRawData(self):
        self.rawdf = pandas.read_csv(self.filename)
        self.preCSVtxt0.delete(1.0, END)
        self.preCSVtxt0.insert(INSERT, self.rawdf)

    # -------------------------------------------------------------------------
    # getData
    #
    # Description:
    #       This method does all the pre-processing before extracting features.
    #
    # -------------------------------------------------------------------------
    def getData(self, test):
        fs = 250
        window = 4

        self.eegdf = self.rawdf[['Marker', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].copy()
        self.eegdf = self.eegdf.loc[(self.eegdf['Marker'] < 20)].copy()
        self.eegdf.reset_index(inplace=True)
        size = self.eegdf.shape[0]

        # Add a time column 250 Hz
        time = [0.004 * x for x in range(0, size)]
        self.eegdf.insert(0, "Time", time)

        # Remove the mean offset about 800 Muse Units
        # Place a band stop filter from 55 Hz to 60 Hz
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            self.eegdf[col] -= self.eegdf[col].mean()
            self.eegdf.loc[:, col] *= 1.64498
            b, a = signal.butter(4, [2*55/fs, 2*60/fs], btype='bandstop')
            self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])
            #b, a = signal.butter(4, 2 * 125 / fs)
            #self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])

        self.fftdf['Freq'] = pandas.Series(np.linspace(0.0, fs / 2, 1000 // 2))
        for i in range(0, int((.004*size)//1), window):
            df = self.eegdf.loc[(self.eegdf.Time >= i) & (self.eegdf.Time < (i + window))]
            N = df.shape[0]
            for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
                if df[col].shape[0]:
                    fft = fftpack.fft(df[col])[0:N // 2 + 1]
                    fft = 1 / (fs * N) * np.abs(fft) ** 2
                    fft[2:-2] = [2 * x for x in fft[2:-2]]
                    self.fftdf[col + 'fft'] = pandas.Series(fft)
            if N:
                self.extractFeatures(self.fftdf, test)

        #if test == "Train":
            #self.traCSVtxt.delete(1.0, END)
            #self.traCSVtxt.insert(INSERT, self.traindf)
            #self.traCSVtxt.update_idletasks()
        #else:
            #self.tstCSVtxt.delete(1.0, END)
            #self.tstCSVtxt.insert(INSERT, self.testdf)
            #self.tstCSVtxt.update_idletasks()

    # -------------------------------------------------------------------------
    # getBands
    #
    # Description:
    #       This method splits the data in the bands of interest. Before
    # calculating the next band, the lower frequency bands are subtracted.
    #
    # -------------------------------------------------------------------------
    def getBands(self, test):
        fs = 250
        fband = [4, 8, 15, 32, 100]
        wband = [2 * x / fs for x in fband]

        self.eegdf = self.rawdf[['Marker', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].copy()
        self.eegdf = self.eegdf[(self.eegdf['Marker'] < 20)].copy()
        self.eegdf.reset_index(inplace=True)

        size = self.eegdf.shape[0]

        # Remove the mean offset about 800 Muse Units
        # Place a band stop filter from 55 Hz to 60 Hz
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            self.eegdf[col] -= self.eegdf[col].mean()
            self.eegdf.loc[:, col] *= 1.64498
            b, a = signal.butter(4, [2*55/fs, 2*60/fs], btype='bandstop')
            self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])
            #b, a = signal.butter(4, 2 * 125 / fs)
            #self.eegdf[col] = signal.filtfilt(b, a, self.eegdf[col])


        # Add a time column 250 Hz
        time = [0.004 * x for x in range(0, size)]
        self.eegdf.insert(0, "Time", time)
        self.widXaxsld1.config(to=self.eegdf["Time"].max())
        self.varXwidth.set(self.eegdf["Time"].max())

        # Separate the desired bands into EEG Bands
        for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
            # First EEG Band Delta 0-4 Hz
            b, a = signal.butter(4, wband[0])
            self.eegdf[col + 'Delta'] = self.eegdf[col]
            self.eegdf[col + 'Delta'] = signal.filtfilt(b, a, self.eegdf[col + 'Delta'])

            # Second EEG Band Theta 4-8 Hz
            b, a = signal.butter(4, wband[1])
            self.eegdf[col + 'Theta'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta'])
            self.eegdf[col + 'Theta'] = signal.filtfilt(b, a, self.eegdf[col + 'Theta'])

            # Third EEG Band Alpha 8-15 Hz
            b, a = signal.butter(4, wband[2])
            self.eegdf[col + 'Alpha'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta'])
            self.eegdf[col + 'Alpha'] = signal.filtfilt(b, a, self.eegdf[col + 'Alpha'])

            # Fourth EEG Band Beta 15-32 Hz
            b, a = signal.butter(4, wband[3])
            self.eegdf[col + 'Beta'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta']) \
                .subtract(self.eegdf[col + 'Alpha'])
            self.eegdf[col + 'Beta'] = signal.filtfilt(b, a, self.eegdf[col + 'Beta'])

            # Fifth EEG Band Gamma +32 Hz
            b, a = signal.butter(4, wband[4])
            self.eegdf[col + 'Gamma'] = self.eegdf[col] \
                .subtract(self.eegdf[col + 'Delta']) \
                .subtract(self.eegdf[col + 'Theta']) \
                .subtract(self.eegdf[col + 'Alpha']) \
                .subtract(self.eegdf[col + 'Beta'])
            self.eegdf[col + 'Gamma'] = signal.filtfilt(b, a, self.eegdf[col + 'Gamma'])

        # Plot the Time Domain
        self.y1 = []
        for i, band in enumerate(['', 'Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']):
            self.y1.append(self.eegdf[['Time', 'EEG1' + band, 'EEG2' + band, 'EEG3' + band, 'EEG4' + band]].copy())

        self.ys1 = itertools.cycle(self.y1)
        self.eegdf[['Time', 'EEG1', 'EEG2', 'EEG3', 'EEG4']] \
            .plot(kind='line', x='Time', legend=True, ax=self.axs1, linewidth=0.2)
        self.axs1.set_title('Time Domain:{}'.format(self.file))

        # Plot the Fourier Transform
        self.eegdf['Freqp'] = pandas.Series(np.linspace(0.0, fs / 2, size // 2))

        self.y2 = []
        for i, band in enumerate(['', 'Delta', 'Theta', 'Alpha', 'Beta', 'Gamma']):
            for col in ['EEG1', 'EEG2', 'EEG3', 'EEG4']:
                fft = fftpack.fft(self.eegdf[col+band].copy())[0:size // 2 + 1]
                fft = 1/(fs*size) * np.abs(fft)**2
                fft[2:-2] = [2 * x for x in fft[2:-2]]
                self.eegdf[col + band + 'fftp'] = pandas.Series(fft)
            self.y2.append(self.eegdf[['Freqp',
                                       'EEG1' + band + 'fftp',
                                       'EEG2' + band + 'fftp',
                                       'EEG3' + band + 'fftp',
                                       'EEG4' + band + 'fftp']].copy())
        self.ys2 = itertools.cycle(self.y2)
        self.axs2.set_title('Frequency Domain:{}'.format(self.file))

        self.eegdf[['Freqp', 'EEG1fftp', 'EEG2fftp', 'EEG3fftp', 'EEG4fftp']] \
            .plot(kind='line', x='Freqp', legend=True, ax=self.axs2, linewidth=0.2)

            # Call to update the time axis variables
        self.plotEEG()

    # -------------------------------------------------------------------------
    # plotEEG
    #
    # Description:
    #       This method draws the EEG data.
    #
    # -------------------------------------------------------------------------
    def plotEEG(self, *args):
        lowlim = self.varXoffset.get()
        upperlim = lowlim + self.varXwidth.get()
        #for ax in self.axs1:
        self.axs1.set_xlim(lowlim, upperlim)
        #self.fig1.tight_layout()
        self.fig1.canvas.draw()
        self.fig2.canvas.draw()

    # -------------------------------------------------------------------------
    # plotMarker
    #
    # Description:
    #       This method draws the EEG data.
    #
    # -------------------------------------------------------------------------
    def plotMarker(self, *args):
        self.axs3.cla()
        df = self.eegdf.loc[self.eegdf['Marker'] == self.varMrk.get()]
        df[['Time', 'EEG1', 'EEG2', 'EEG3', 'EEG4']].plot(kind='line', x='Time', legend=False, ax=self.axs3)

    # -------------------------------------------------------------------------
    # extractFeatures
    #
    # Description:
    #       This method extracts features from the data.
    #
    # -------------------------------------------------------------------------
    def extractFeatures(self, freqdf, test):
        deltadf = freqdf.loc[(freqdf['Freq'] >= 0) & (freqdf['Freq'] < 4)]
        thetadf = freqdf.loc[(freqdf['Freq'] >= 4) & (freqdf['Freq'] < 8)]
        alphadf = freqdf.loc[(freqdf['Freq'] >= 8) & (freqdf['Freq'] < 15)]
        betadf = freqdf.loc[(freqdf['Freq'] >= 15) & (freqdf['Freq'] < 32)]
        gammadf = freqdf.loc[(freqdf['Freq'] >= 32) & (freqdf['Freq'] < 100)]

        mean = {
            "delta": 0,
            "theta": 1,
            "alpha": 2,
            "beta": 3,
            "gamma": 4,
            "phi": 5,
        }
        feat = []
        for i, sensor in enumerate(['EEG1fft', 'EEG2fft', 'EEG3fft', 'EEG4fft']):
            meanlist = []
            for df in [deltadf, thetadf, alphadf, betadf, gammadf]:
                meanlist.append(df[sensor].mean())
            meanlist.append(freqdf[sensor].mean())

            delta = meanlist[mean['delta']]
            theta = meanlist[mean['theta']]
            alpha = meanlist[mean['alpha']]
            beta = meanlist[mean['beta']]
            gamma = meanlist[mean['gamma']]
            phi = meanlist[mean['phi']]
            if (delta * theta * alpha * beta * gamma * phi) == 0:
                return
            feat.append(delta)
            feat.append(theta)
            feat.append(alpha)
            feat.append(theta/beta)
            feat.append(theta/alpha)
            feat.append(theta/phi)
            feat.append(theta/(beta + alpha + gamma))
            feat.append(delta/(beta + alpha + gamma))
            feat.append(delta/alpha)
            feat.append(delta/phi)
            feat.append(delta/beta)
            feat.append(delta/theta)

        if test == "Train":
            mental = "Not Fatigued" if 'Early' in self.filename else "Fatigued"
            feat.append(mental)
            self.traindf.loc[self.n] = feat
            self.n += 1
        else:
            mental = "Not Fatigued" if 'Early' in self.filename else "Fatigued"
            feat.append(mental)
            self.testdf.loc[self.m] = feat
            self.m += 1

    # -------------------------------------------------------------------------
    # train
    #
    # Description:
    #       This method trains the classifier.
    #
    # -------------------------------------------------------------------------
    def train(self):
        self.traindf = self.traindf.dropna()
        self.X = self.traindf.loc[:, self.traindf.columns != 'Class'].copy()
        X = (self.X - self.X.mean())/self.X.std()

        X = X.to_numpy()
        y = self.traindf.loc[:, "Class"].to_numpy()
        self.clf.fit(X, y)

    # -------------------------------------------------------------------------
    # test
    #
    # Description:
    #       This method tests the classifier.
    #
    # -------------------------------------------------------------------------
    def test(self):
        self.workbook = xlsxwriter.Workbook(
            'D:/UVic/Term 3B/ECE 399/Test Data/Experiment{}_{}.xlsx'.format(self.p, self.file))
        self.worksheet = self.workbook.add_worksheet()
        self.p += 1

        self.testdf = self.testdf.dropna()
        X = self.testdf.loc[:, self.testdf.columns != 'Class'].copy()
        X = (X - self.X.mean()) / self.X.std()
        X = X.to_numpy()
        y = self.testdf.loc[:, "Class"].to_numpy()
        score = self.clf.score(X,y)
        print(self.file, score, self.testdf.shape[0])
        self.tstCSVtxt.insert(INSERT, "{}\t{}\t{}\n".format(self.file, score, self.testdf.shape[0]))
        self.tstCSVtxt.update_idletasks()
        y = self.clf.predict(X)
        self.testdf["Class"] = y

        for i, header in enumerate(self.trainheading):
            self.worksheet.write(0, i, header)
        for row, data in self.testdf.iterrows():
            for col, columnname in enumerate(self.testdf):
                self.worksheet.write(row, col, self.testdf.loc[row, columnname])
                col += 1
            row += 1

        self.worksheet.write(0, col, "=COUNTIF(AW:AW,\"Fatigued\")")
        self.worksheet.write(1, col, "=COUNTA(AW:AW)")
        self.workbook.close()
        self.testdf = self.testdf.iloc[0:0]
        self.m = 0


if __name__ == "__main__":
    #pr = cProfile.Profile()
    #pr.enable()
    root = Tk()
    game = EEG_GUI(root)
    root.mainloop()
    #pr.disable()
    #s = io.StringIO()
    #sortby = SortKey.CUMULATIVE
    #ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
    #ps.print_callees(.05)
    #print(s.getvalue())
    sys.exit(1)
