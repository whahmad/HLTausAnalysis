#!/usr/bin/env python
'''
DESCRIPTION:
Basic plotting script for making plots for CaloTk analyzer.


USAGE:
./plotL1TkTau.py -m <multicrab_directory> [opts]
./plotL1TkTau.py -m multicrab_CaloTkSkim_v92X_20180801T1203/ -i "SingleNeutrino_L1TPU140|TT_TuneCUETP8M2T4_14TeV_L1TnoPU" -n
./plotL1TkTau.py -m multicrab_CaloTkSkim_v92X_20180801T1203/ -i "SingleNeutrino_L1TPU140|TT_TuneCUETP8M2T4_14TeV_L1TnoPU|TT_TuneCUETP8M2T4_14TeV_L1TPU140" -n
./plotL1TkTau.py -m multicrab_CaloTk_v92X_IsoConeRMax0p4_VtxIso1p0_08h09m41s_23Aug2018 -e "TT|Glu|SingleTau|Higgs1000|Higgs500" -n
./plotL1TkTau.py -m multicrab_CaloTk_v92X_IsoConeRMax0p4_VtxIso1p0_08h09m41s_23Aug2018 -e "TT|SingleTau|Higgs" -n 

LAST USED:
./plotL1TkTau.py -m multicrab_CaloTk_v92X_IsoConeRMax0p4_VtxIso1p0_08h09m41s_23Aug2018 -e "TT|Glu|Higgs" -n

'''
#================================================================================================
# Imports
#================================================================================================
import os
import sys
from optparse import OptionParser
import getpass
import socket
import json
import copy

import HLTausAnalysis.NtupleAnalysis.tools.dataset as dataset
import HLTausAnalysis.NtupleAnalysis.tools.tdrstyle as tdrstyle
import HLTausAnalysis.NtupleAnalysis.tools.styles as styles
import HLTausAnalysis.NtupleAnalysis.tools.plots as plots
import HLTausAnalysis.NtupleAnalysis.tools.histograms as histograms
import HLTausAnalysis.NtupleAnalysis.tools.aux as aux
import HLTausAnalysis.NtupleAnalysis.tools.ShellStyles as ShellStyles

import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import *

#================================================================================================
# Variable definition
#================================================================================================
ss = ShellStyles.SuccessStyle()
ns = ShellStyles.NormalStyle()
ts = ShellStyles.NoteStyle()
hs = ShellStyles.HighlightAltStyle()
ls = ShellStyles.HighlightStyle()
es = ShellStyles.ErrorStyle()
cs = ShellStyles.CaptionStyle()

#================================================================================================
# Main
#================================================================================================
def Print(msg, printHeader=False):
    fName = __file__.split("/")[-1]
    if printHeader==True:
        print "=== ", fName
        print "\t", msg
    else:
        print "\t", msg
    return

def Verbose(msg, printHeader=True, verbose=False):
    if not opts.verbose:
        return
    Print(msg, printHeader)
    return

def GetLumi(datasetsMgr):
    Verbose("Determininig Integrated Luminosity")

    lumi = 0.0
    for d in datasetsMgr.getAllDatasets():
        if d.isMC():
            continue
        else:
            lumi += d.getLuminosity()
    Verbose("Luminosity = %s (pb)" % (lumi), True )
    return lumi

def GetDatasetsFromDir(opts):
    Verbose("Getting datasets")
    
    if (not opts.includeOnlyTasks and not opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=None,
                                                        analysisName=opts.analysis)
    elif (opts.includeOnlyTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=None,
                                                        analysisName=opts.analysis,
                                                        includeOnlyTasks=opts.includeOnlyTasks)
    elif (opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=None,
                                                        analysisName=opts.analysis,
                                                        excludeTasks=opts.excludeTasks)
    else:
        raise Exception("This should never be reached")
    return datasets
    
    
def PlotHisto(datasetsMgr, h):
    dsetsMgr = datasetsMgr.deepCopy()

    if "_eff" in h.lower():
        dsetsMgr.remove("SingleNeutrino_L1TPU140", close=False) 
        dsetsMgr.remove("SingleNeutrino_L1TPU200", close=False) 
        opts.normalizeToOne = False
    elif "_deltargenp" in h.lower():
        dsetsMgr.remove("SingleNeutrino_L1TPU140", close=False) 
        dsetsMgr.remove("SingleNeutrino_L1TPU200", close=False) 
    elif "_resolution" in h.lower():
        dsetsMgr.remove("SingleNeutrino_L1TPU140", close=False) 
        dsetsMgr.remove("SingleNeutrino_L1TPU200", close=False) 
    elif "_rate" in h.lower():
        opts.normalizeToOne = False
        for d in dsetsMgr.getAllDatasetNames():
            if "SingleNeutrino" in d:
                continue
            else:
                dsetsMgr.remove(d, close=False)
    else:
        pass

    # Create the plot with selected normalization ("normalizeToOne", "normalizeByCrossSection", "normalizeToLumi")
    kwargs = {}
    hList  = getHistoList(dsetsMgr, h)

    if opts.normalizeToOne:
        if 1:
            p = plots.ComparisonManyPlot(hList[0], hList[1:], saveFormats=[], **kwargs)
            p.histoMgr.forEachHisto(lambda h: h.getRootHisto().Scale(1.0/h.getRootHisto().Integral()))
        else:
            # p = plots.MCPlot(dsetsMgr, h, normalizeToOne=True, saveFormats=[], **kwargs)
            p = plots.PlotSameBase(dsetsMgr, h, normalizeToOne=True, saveFormats=[], **kwargs)
    else:
        if 1:
            p = plots.ComparisonManyPlot(hList[0], hList[1:], saveFormats=[], **kwargs) #FIXME
        else:
            # p = plots.MCPlot(dsetsMgr, h, normalizeToLumi=opts.intLumi, saveFormats=[], **kwargs)
            p = plots.PlotSameBase(dsetsMgr, h, saveFormats=[], **kwargs)
            
    
    # Set default styles (Called by default in MCPlot)
    p._setLegendStyles()
    p._setLegendLabels()
    p._setPlotStyles()

    # Customise legend
    for d in dsetsMgr.getAllDatasetNames():
        if "SingleNeutrino" in d:
            p.histoMgr.setHistoLegendStyle(d, "F")
        else:
            p.histoMgr.setHistoLegendStyle(d, "L")

    # Create legend
    if 0:
        p.setLegend(histograms.createLegend(0.18, 0.86-0.04*len(dsetsMgr.getAllDatasetNames()), 0.42, 0.92))
    else:
        p.setLegend(histograms.createLegend(0.58, 0.86-0.04*len(dsetsMgr.getAllDatasetNames()), 0.92, 0.92))

    # Draw a customised plot
    plots.drawPlot(p, h, **GetHistoKwargs(h, opts) )

    # Remove legend?
    if 0:
        p.removeLegend()

    # Save in all formats chosen by user
    aux.SavePlot(p, opts.saveDir, h, opts.saveFormats, opts.url)
    return

def getHistoList(datasetsMgr, histoName):
    hList = []
    # For-loop: All dataset names
    for d in datasetsMgr.getAllDatasetNames():
        h = datasetsMgr.getDataset(d).getDatasetRootHisto(histoName)
        hList.append(h)
    return hList

def GetHistoKwargs(h, opts):
    
    hName   = h.lower()
    _xLabel = ""
    if opts.normalizeToOne:
        _yNorm = "Arbitrary Units"
    else:
        _yNorm = "Events"
    _yLabel = _yNorm + " / %.2f "
    _rebinX = 1
    _rebinY = None
    _units  = ""
    _format = "%0.0f " + _units
    _cutBox = {"cutValue": 10.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
    _leg   = {"dx": -0.5, "dy": -0.3, "dh": -0.4}
    _ratio = True
    _log   = False
    _yMin  = 0.0
    _yMaxF = 1.25 #1.2
    _xMin  = None
    _xMax  = None

    if "_eff" in hName:
        _units  = "GeV"
        _format = "%0.0f " + _units
        _xLabel = "E_{T} (%s)" % (_units)
        _cutBox = {"cutValue": 20.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = "Efficiency / %.0f " + _units
    elif "counters" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "counters"
        _rebinX = 1
        #_xMax   = +10.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_turnon" in hName:
        _units  = "GeV"
        _format = "%0.0f " + _units
        _xLabel = "#tau_{h} E_{T} (%s)" % (_units)
        _cutBox = {"cutValue": 20.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = "Efficiency / %.0f " + _units
        _xMax   = 200.0
    elif "_rate" in hName:
        _units  = "GeV"
        _format = "%0.0f " + _units
        _xLabel = "E_{T} (%s)" % (_units)
        _cutBox = {"cutValue": 20.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = "Rate (kHz) / %.0f " + _units
        _log    = True
        _yMin   = 1e+0
        _xMax   = 250.0
    elif "_rtau" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "R_{#tau}"# (%s)" % (_units)
        _cutBox = {"cutValue": 1.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        # _log    = True
        # _yMin   = 1e+0
        _xMin   = +0.0
        _xMax   = +1.2
    elif "_chf" in hName:
        _units  = ""
        _format = "%0.1f " + _units
        _xLabel = "charged hadron fraction"
        _cutBox = {"cutValue": 1.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _xMax   = 2.0
    elif "_nhf" in hName:
        _units  = ""
        _format = "%0.1f " + _units
        _xLabel = "neutral hadron fraction"
        _cutBox = {"cutValue": 1.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _xMin   = -1.0
        _xMax   = +1.5
        if "abs" in hName:
            _xLabel = "|neutral hadron fraction|" 
            _xMin   = 0.0
    elif "_charge" in hName:
        _units  = "e"
        _format = "%0.1f " + _units
        _xLabel = "charge (%s)" % (_units)
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _xMin   = -2.0
        _xMax   = +2.0
    elif "_deltargenp" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "#DeltaR" #(%s)" % (_units)
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _xMin   = +0.0
        _xMax   = +1.0
    elif "_invmass" in hName:
        _units  = "GeV/c^{2}"
        _format = "%0.1f " + _units
        _xLabel = "m (%s)" % (_units)
        _cutBox = {"cutValue": 1.776, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 2
        _yLabel = _yNorm + " / " + _format
        _log    = True
        #_xMin   = +0.0
        #_xMax   = +1.0
    elif "_sigconermin" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "R_{min}^{sig}"
        _cutBox = {"cutValue": 1.776, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _log    = False
        _xMin   = +0.0
        _xMax   = +0.3
        _log    = False
    elif "_sigconermax" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "R_{max}^{sig}"
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _log    = False
        _xMin   = +0.0
        _xMax   = +0.3
    elif "_isoconermin" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "R_{min}^{iso}"
        _cutBox = {"cutValue": 1.776, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _log    = False
        _xMin   = +0.0
        _xMax   = +0.2
        _log    = False
    elif "_isoconermax" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "R_{max}^{iso}"
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _log    = False
        _xMin   = +0.0
        _xMax   = +1.0
    elif "_chisquared" in hName:
        _units  = ""
        _format = "%0.1f " + _units
        _xLabel = "#chi^{2}"
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 1
        _yLabel = _yNorm + " / " + _format
        _log    = True
        _xMax   = 400.0
    elif "_redchisquared" in hName:
        _units  = ""
        _format = "%0.1f " + _units
        #_xLabel = "#chi^{2} / #nu"
        _xLabel = "#chi^{2}_{#nu}"
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 10 #5
        _yLabel = _yNorm + " / " + _format
        _log    = True
        _xMax   = 200.0
    elif "_deltapocaz" in hName:
        _units  = "cm"
        _format = "%0.2f " + _units
        _xLabel = "#Deltaz_{0} (%s)" % (_units)
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 4
        _yLabel = _yNorm + " / " + _format
        _log    = True
    elif "_deltar" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "#DeltaR"# (%s)" % (_units)
        _cutBox = {"cutValue": 0.15, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 1
        _xMin   = +0.0
        _xMax   = +0.4
        _yLabel = _yNorm + " / " + _format
        _log    = True
    elif "_eta" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "#eta"
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 5
        _xMin   = -2.4
        _xMax   = +2.4
        _yLabel = _yNorm + " / " + _format
        _log    = False
        ROOT.gStyle.SetNdivisions(6, "X")
    elif "_nstubs" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "stubs multiplicity"
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 2
        _xMax   = +11.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_pocaz" in hName:
        _units  = "cm"
        _format = "%0.1f " + _units
        _xLabel = "z_{0} (%s)" % (_units)
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 5
        _xMin   = -25.0
        _xMax   = +25.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
        ROOT.gStyle.SetNdivisions(6, "X")
    elif "_d0" in hName:
        _units  = "cm"
        _format = "%0.1f " + _units
        _xLabel = "d_{0} (%s)" % (_units)
        _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _rebinX = 5
        _xMin   = +0.0
        _xMax   = +35.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
        if "_d0sig" in hName:
            _units  = "cm"
            _format = "%0.1f " + _units
            _xLabel = "d_{0}/#sigma_{d_{0}} (%s)" % (_units)
            _cutBox = {"cutValue": 0.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
            _rebinX = 5
            _xMin   = +0.0
            _xMax   = +10.0
            _yLabel = _yNorm + " / " + _format
            _log    = False
            ROOT.gStyle.SetNdivisions(6, "X")
    elif "_pt" in hName:
        _units  = "GeV/c"
        _format = "%0.0f " + _units
        _xLabel = "p_{T} (%s)" % (_units)
        _cutBox = {"cutValue": 2.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
        _rebinX = 5
        _xMax   = +200.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
        if "_ptrel" in hName: # matchTk.p3().Perp(caloTau_p4.Vect()) =  transverse component (R in cylindrical coordinate system)
            _units  = "GeV/c"
            _format = "%0.2f " + _units
            _xLabel = "p_{T}^{rel} (%s)" % (_units)
            _cutBox = {"cutValue": 2.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
            _rebinX = 10
            _xMax   = +10.0
            _yLabel = _yNorm + " / " + _format
            _log    = True
        if "_ptminuscaloet" in hName:
            _units  = "GeV"
            _format = "%0.0f " + _units
            _xLabel = "p_{T}^{tk} - E_{T}^{calo} (%s)" % (_units)
            _cutBox = {"cutValue": 2.0, "fillColor": 16, "box": False, "line": False, "greaterThan": True}
            _rebinX = 1
            _xMax   = +10.0
            _yLabel = _yNorm + " / " + _format
            _log    = True
    elif "_iscombinatoric" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "is combinatoric"
        _rebinX = 1
        _xMax   = +2.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_isgenuine" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "is genuine"
        _rebinX = 1
        _xMax   = +2.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_isunknown" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "is unknown"
        _rebinX = 1
        _xMax   = +2.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_multiplicity" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "tau candidate multiplicity"
        _rebinX = 1
        _xMax   = +12.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_nisotks" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "track multiplicity (isolation)"
        _rebinX = 1
        _xMax   = +15.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_nsigtks" in hName:
        _units  = ""
        _format = "%0.0f " + _units
        _xLabel = "track multiplicity (signal)"
        _rebinX = 1
        _xMax   = +15.0
        _yLabel = _yNorm + " / " + _format
        _log    = False
    elif "_reliso" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        _xLabel = "relative isolation"
        #_xLabel = "#sum#limits_{i}^{iso tks} p_{T,i}/p_{T}^{m}"
        #_xLabel = "#Sigma_{i}^{iso tks} p_{T,i}/p_{T}^{m}"#"relative isolatin"
        _rebinX = 1
        _xMax   = +5.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
        _cutBox = {"cutValue": 0.2, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
    elif "_vtxiso" in hName:
        _units  = "cm"
        _format = "%0.2f " + _units
        #_xLabel = "vertex isolation"
        _xLabel = "min(z_{0}^{m} - z_{0}^{iso}) (%s)" % (_units)
        _rebinX = 1
        _xMax   = +10.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
        #_cutBox = {"cutValue": 1.0, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
        _cutBox = {"cutValue": 0.5, "fillColor": 16, "box": False, "line": True, "greaterThan": True}
    elif "_viset" in hName:
        _units  = "GeV"
        _format = "%0.0f " + _units
        _xLabel = "#tau_{h} E_{T} (%s)" % (_units)
        _rebinX = 1
        _xMax   = +200.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
    elif "_resolutioncaloet" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        #_xLabel = "(E_{T}^{calo} - p_{T}^{vis}) / p_{T}^{vis}"
        _xLabel = "#deltaE_{T} / p_{T}^{vis}"
        _rebinX = 1
        _xMin   = -1.5
        _xMax   = +5.5 #+10.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
        if "_resolutioncaloeta" in hName:
            #_xLabel = "(#eta^{calo} - #eta^{vis}) / #eta^{vis}"
            _xLabel = "#delta#eta / #eta^{vis}"
            _xMin   = -1.5
            _xMax   = +5.5
            _yLabel = _yNorm + " / " + _format
            _log    = True
    elif "_resolutioncalophi" in hName:
        _units  = ""
        _format = "%0.2f " + _units
        #_xLabel = "#phi^{calo} - #phi^{vis} / #phi^{vis}"
        _xLabel = "#delta#phi / #phi^{vis}"
        _rebinX = 1
        _xMin   = -5.0
        _xMax   = +5.0
        _yLabel = _yNorm + " / " + _format
        _log    = True
    else:
        ROOT.gStyle.SetNdivisions(8, "X")

    if _log:
        if _yMin == 0.0:
            if opts.normalizeToOne:
                _yMin = 0.9e-4
            else:
                _yMin = 1e0
        _yMaxF = 10

    _opts = {"ymin": _yMin, "ymaxfactor": _yMaxF}
    if _xMax != None:
        _opts["xmax"] = _xMax
    if _xMin != None:
        _opts["xmin"] = _xMin

    _opts2 = {"ymin": 0.0, "ymax": 2.3}

    _kwargs = {
        "xlabel"           : _xLabel,
        "ylabel"           : _yLabel,
        "rebinX"           : _rebinX,
        "rebinY"           : _rebinY,
        "ratioYlabel"      : "1/Ratio ", #"Ratio "
        "ratio"            : _ratio, # only plots.ComparisonManyPlot(). Eitherwise comment out
        "stackMCHistograms": False,
        "ratioInvert"      : True,
        "addMCUncertainty" : True,
        "addLuminosityText": False,
        "addCmsText"       : True,
        "cmsExtraText"     : "Phase-2 Simulation",
        "cmsTextPosition"  : "outframe",
        "opts"             : _opts,
        "opts2"            : _opts2,
        "log"              : _log,
        "cutBox"           : _cutBox,
        "createLegend"     : None #_leg,
        }
    return _kwargs

def GetBinwidthDecimals(binWidth):                                                                                                                                        
    dec =  " %0.0f"
    if binWidth < 1:
        dec = " %0.1f"
    if binWidth < 0.1:
        dec = " %0.2f"
    if binWidth < 0.01:
        dec =  " %0.3f"
    if binWidth < 0.001:
        dec =  " %0.4f"
    if binWidth < 0.0001:
        dec =  " %0.5f"
    if binWidth < 0.00001:
        dec =  " %0.6f"
    if binWidth < 0.000001:
        dec =  " %0.7f"
    return dec

def ReorderDatasets(datasets):
    newOrder =  datasets
    
    for i, d in enumerate(datasets, 0):
        if "PU200" in d:
            newOrder.remove(d)
            newOrder.insert(0, d)
            #newOrder.insert(0, newOrder.pop(i))
    for j, d in enumerate(datasets, 0):
        if "PU140" in d:
            newOrder.remove(d)
            newOrder.insert(0, d)
    for k, d in enumerate(datasets, 0):
        if "noPU" in d:
            newOrder.remove(d)
            newOrder.insert(0, d)
    
    mb140 = "SingleNeutrino_L1TPU140"
    mb200 = "SingleNeutrino_L1TPU200"
    if mb140 in datasets:
        newOrder.remove(mb140)
        newOrder.insert(len(newOrder), mb140)
    if mb200 in datasets:
        newOrder.remove(mb200)
        newOrder.insert(len(newOrder), mb200)
    return newOrder


def main(opts):
    
    # Set the ROOTeError verbosity
    ROOT.gErrorIgnoreLevel=3000 # kUnset=-1, kPrint=0, kInfo=1000, kWarning=2000, kError=3000, kBreak=4000

    # Apply TDR style
    style = tdrstyle.TDRStyle()
    style.setGridX(opts.gridX)
    style.setGridY(opts.gridY)
    style.setOptStat(False)


    # Obtain dsetMgrCreator and register it to module selector
    dsetMgrCreator = dataset.readFromMulticrabCfg(directory=opts.mcrab)

    # Setup & configure the dataset manager
    datasetsMgr = GetDatasetsFromDir(opts)
    datasetsMgr.updateNAllEventsToPUWeighted()

    if opts.verbose:
        datasetsMgr.PrintCrossSections()
        datasetsMgr.PrintInfo()

    # Setup & configure the dataset manager (no collision data => not needed)
    if 0:
        datasetsMgr.loadLuminosities()
        datasetsMgr.updateNAllEventsToPUWeighted()

    # Print information
    if opts.verbose:
        datasetsMgr.PrintCrossSections()
        # datasetsMgr.PrintLuminosities()

    # Print dataset information (before merge)        
    datasetsMgr.PrintInfo()
        
    # Merge histograms (see NtupleAnalysis/python/tools/plots.py)    
    plots.mergeRenameReorderForDataMC(datasetsMgr)

    # Get Luminosity
    if 0:
        intLumi = datasetsMgr.getDataset("Data").getLuminosity()

    # Apply new dataset order?
    newOrder = ReorderDatasets(datasetsMgr.getAllDatasetNames())
    datasetsMgr.selectAndReorder(newOrder)

    # Print dataset information (after merge)
    if 0:
        datasetsMgr.PrintInfo() #Requires python 2.7.6 or 2.6.6

    # Plot Histograms
    histoList  = datasetsMgr.getDataset(datasetsMgr.getAllDatasetNames()[0]).getDirectoryContent(opts.folder)
    histoPaths = [os.path.join(opts.folder, h) for h in histoList]
    histoType  = type(datasetsMgr.getDataset(datasetsMgr.getAllDatasetNames()[0]).getDatasetRootHisto(h).getHistogram())
    plotCount  = 0
    skipList   = ["L1TkTau_MatchTk_d0", "L1TkTau_MatchTk_d0Abs", "L1TkTau_SigTks_d0", 
                  "L1TkTau_SigTks_d0Abs", "L1TkTau_SigTks_d0Sig", "L1TkTau_SigTks_d0SigAbs",
                  "L1TkTau_IsoTks_d0", "L1TkTau_IsoTks_d0Abs", "L1TkTau_IsoTks_d0Sig", "L1TkTau_IsoTks_d0SigAbs",
                  "L1TkTau_ResolutionCaloEt_F", "L1TkTau_ResolutionCaloEta_F", "L1TkTau_ResolutionCaloPhi_F", 
                  "DiTau_Rate_Calo_F", "DiTau_Rate_Tk_F", "DiTau_Rate_VtxIso_F", "DiTau_Rate_RelIso_F",
                  "Calo_Rate_F", "Tk_Rate_F", "VtxIso_Rate_F", "RelIso_Rate_F"]

    # For-loop: All histos in opts.folder
    for i, h in enumerate(histoPaths, 1):
        
        # Obsolete quantity
        if h in skipList:
            continue

        histoType  = str(type(datasetsMgr.getDataset(datasetsMgr.getAllDatasetNames()[0]).getDatasetRootHisto(h).getHistogram()))
        if "TH1" not in histoType:
            continue
        
        aux.PrintFlushed(h, plotCount==0)
        plotCount += 1
        PlotHisto(datasetsMgr, h)

    print
    Print("All plots saved under directory %s" % (ShellStyles.NoteStyle() + aux.convertToURL(opts.saveDir, opts.url) + ShellStyles.NormalStyle()), True)
    return

#================================================================================================
# Main
#================================================================================================
if __name__ == "__main__":

    # Default Settings 
    ANALYSIS    = "HLTausAnalysis"
    BATCHMODE   = True
    DATAERA     = "TDR2019"
    FOLDER      = ""
    GRIDX       = False
    GRIDY       = False    
    INTLUMI     = 1.0
    NORMTOONE   = False
    SAVEDIR     = None
    SAVEFORMATS = [".C", ".png", ".pdf"]
    VERBOSE     = False

    parser = OptionParser(usage="Usage: %prog [options]" , add_help_option=False,conflict_handler="resolve")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=VERBOSE, 
                      help="Enables verbose mode (for debugging purposes) [default: %s]" % VERBOSE)

    parser.add_option("-b", "--batchMode", dest="batchMode", action="store_false", default=BATCHMODE, 
                      help="Enables batch mode (canvas creation  NOT generates a window) [default: %s]" % BATCHMODE)

    parser.add_option("-m", "--mcrab", dest="mcrab", action="store", default=None,
                      help="Path to the multicrab directory for input")

    parser.add_option("-n", "--normalizeToOne", dest="normalizeToOne", action="store_true", default=NORMTOONE,
                      help="Normalise all histograms to unit area? [default: %s]" % (NORMTOONE) )

    parser.add_option("--intLumi", dest="intLumi", type=float, default=INTLUMI,
                      help="Override the integrated lumi [default: %s]" % INTLUMI)

    parser.add_option("-i", "--includeOnlyTasks", dest="includeOnlyTasks", action="store", 
                      help="List of datasets in mcrab to include")

    parser.add_option("-e", "--excludeTasks", dest="excludeTasks", action="store", 
                      help="List of datasets in mcrab to exclude")

    parser.add_option("--saveDir", dest="saveDir", type="string", default=SAVEDIR,
                      help="Directory where all pltos will be saved [default: %s]" % SAVEDIR)

    parser.add_option("--gridX", dest="gridX", action="store_true", default=GRIDX,
                      help="Enable x-axis grid? [default: %s]" % (GRIDX) )
    
    parser.add_option("--gridY", dest="gridY", action="store_true", default=GRIDY,
                      help="Enable y-axis grid? [default: %s]" % (GRIDY) )

    parser.add_option("--url", dest="url", action="store_true", default=False,
                      help="Don't print the actual save path the histogram is saved, but print the URL instead [default: %s]" % False)

    parser.add_option("--formats", dest="formats", default = None,
                      help="Formats in which all plots will be saved in. Provide as list of comma-separated (NO SPACE!) formats. [default: None]")

    parser.add_option("--analysis", dest="analysis", type="string", default=ANALYSIS,
                      help="Override default analysis [default: %s]" % ANALYSIS)

    parser.add_option("--dataEra", dest="dataEra", default = DATAERA,
                      help="Formats in which all plots will be saved in. Provide as list of comma-separated (NO SPACE!) formats. [default: %s]" % (DATAERA))

    parser.add_option("--folder", dest="folder", type="string", default = FOLDER,
                      help="ROOT file folder under which all histograms to be plotted are located [default: %s]" % (FOLDER) )

    (opts, parseArgs) = parser.parse_args()

    # Require at least two arguments (script-name, path to multicrab)
    if opts.mcrab == None:
        Print("Not enough arguments passed to script execution. Printing docstring & EXIT.")
        print __doc__
        sys.exit(0)
    
    # Determine path for saving plots
    if opts.saveDir == None:
        opts.saveDir = aux.getSaveDirPath(opts.mcrab, prefix="", postfix="L1TkTau")
    else:
        print "opts.saveDir = ", opts.saveDir

    # Overwrite default save formats?
    if opts.formats != None:
        opts.saveFormats = opts.formats.split(",")
    else:
        opts.saveFormats = SAVEFORMATS

    # Inform user of compatibility issues
    pyV1  =  sys.version_info[0]
    pyV2  =  sys.version_info[1]
    pyV3  =  sys.version_info[2]
    pyVer = "%d.%d.%d" % (pyV1, pyV2, pyV3)
    if pyV2 < 7 or pyV3 < 6:
        Print("Recommended %sPython 2.7.6%s or later (using %sPython %s). EXIT!" % (hs, ns, es, pyVer + ns), True)
        #sys.exit()
    else:
        Print("Recommended %sPython 2.7.6%s or later (using %sPython %s)" % (hs, ns, ss, pyVer + ns), True)

    # Call the main function
    main(opts)

    if not opts.batchMode:
        raw_input("=== plotL1TkTau.py: Press any key to quit ROOT ...")
