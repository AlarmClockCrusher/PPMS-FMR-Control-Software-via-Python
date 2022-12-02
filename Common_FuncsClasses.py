import numpy as np
import pandas as pd

"""Lineshape fitting"""
#amp, linewidth, centerfield
#Has two Lorentzians. Each has a symmetric and antisymmetric component.
def doubleLorentzians(H, Hr1, Hr2, Sym1, AntiSym1, Sym2, AntiSym2, dH1, dH2, C):
    return (Sym1-AntiSym1*(H-Hr1))/((H-Hr1)**2+(dH1/2)**2)**2 + (Sym2-AntiSym2*(H-Hr2))/((H-Hr2)**2+(dH2/2)**2)**2 + C

def doubleLorentzian_NoSym(H, Hr1, Hr2, AntiSym1, AntiSym2, dH1, dH2, C):
    return -AntiSym1*(H-Hr1) / ((H-Hr1)**2+(dH1/2)**2)**2 - AntiSym2*(H-Hr2)/((H-Hr2)**2+(dH2/2)**2)**2 + C

def singleLorentzian(H, Hr1, Sym1, AntiSym1, dH1, C):
    return (Sym1-AntiSym1*(H-Hr1))/((H-Hr1)**2+(dH1/2)**2)**2 + C

def singleLorentz_LinBg(H, Hr1, Sym1, AntiSym1, dH1, C, slope):
    return (Sym1-AntiSym1*(H-Hr1))/((H-Hr1)**2+(dH1/2)**2)**2 + C + slope * H

def singleLorentz_AsymBg(H, Hr1, Sym1, AntiSym1, dH1, Hr2, AntiSym2, dH2, C):
    return (Sym1-AntiSym1*(H-Hr1))/((H-Hr1)**2+(dH1/2)**2)**2 - AntiSym2*(H-Hr2)/((H-Hr2)**2+(dH2/2)**2)**2 + C

"""Dependence fitting"""
gamma_0 = 0.0176

def resFreq_vs_Field(H, gamma, Meff):
    return gamma/(2*np.pi) * np.sqrt(H * (H + 4 * np.pi * Meff))

def resFreq_vs_Field_FixedGamma(H, Meff):
    return gamma_0/(2*np.pi) * np.sqrt(H * (H + 4 * np.pi * Meff))

def linewidth_Linear(freq, alpha, gamma, dH0):
    return dH0 + 4*np.pi* alpha * freq / gamma

def linewidth_Linear_FixedGamma(freq, alpha, dH0):
    return dH0 + 4*np.pi* alpha * freq / gamma_0

def linewidth_LinearandNonlinear(freq, alpha, gamma, dH0, A, tau):
    return dH0 + 4*np.pi* alpha * freq / gamma + 2*np.pi* A * (freq * tau) / (1 + (2*np.pi * freq * tau) ** 2)

def linewidth_LinearandNonlinear_FixedGamma(freq, alpha, dH0, A, tau):
    return dH0 + 4*np.pi* alpha * freq / gamma_0 + 2*np.pi* A * (freq * tau) / (1 + (2*np.pi * freq * tau) ** 2)

def linewidth_Nonlinear_Subtracted(freq, A, tau):
    return 2*np.pi* A * (freq * tau) / (1 + (2*np.pi * freq * tau) ** 2)

def linewidth_Parabolic_Subtracted(freq, a, center):
    return a * (freq - center) ** 2


def loadCSVandPreprocess(path, file):
    print("Handling file {}".format(file), end=" \t")
    fileNameWords = file.split('.')[0].split('_')  # fiel = LSC313_YIG35_GGG_2K_10p0GHz_0dBm_100p0mA
    """FILENAMES MIGHT CHANGE, NEED TO ADJUST THE INDEX OF THE WORD ACCORDINGLY"""
    freq = next(s for s in fileNameWords if "GHz" in s).replace("GHz", "").replace('p', '.')
    temp = next(s for s in fileNameWords if "K" in s and s.replace("K", '').isnumeric()).replace('K', '')
    print("Freq&Temp:", freq, temp)
    filename = path + '\\' + file
    df = pd.read_csv(filename)
    fields = df["Field(G)"].values
    lockin = df["Lockin_X_Ave"].values
    if not len(fields): print("Empty field data:", fields)
    if not len(lockin): print("Empty lockin data:", lockin)

    Hres = 0.5 * (fields[lockin.argmax()] + fields[lockin.argmin()])
    H1, H2 = fields[lockin.argmax()], fields[lockin.argmin()]
    dH = np.sqrt(3) * abs(H2 - H1)
    """CSV files could have lines that only have ,,,, which is not visible in spreadsheet"""
    signal_max, signal_min = lockin.max(), lockin.min()
    peakCenter = 0.5 * (signal_max + signal_min)
    antiSym = (signal_max - peakCenter) * dH ** 3 * 2 / (3 * np.sqrt(3))
    sym = (signal_max - peakCenter) * dH ** 4 / 16

    return freq, temp, fields, lockin, Hres, sym, antiSym, dH, H1, H2, signal_max, signal_min


class Line2D:
    def __init__(self, ax, temp, x, y, **kwargs):
        self.plotLine, = ax.plot(x, y, **kwargs)
        self.temp = temp