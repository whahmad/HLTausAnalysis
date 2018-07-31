#!/usr/bin/env python
'''
Description:
Script that plots Data/MC for all histograms under a given folder (passsed as option to the script)
Good for sanity checks for key points in the cut-flow

Usage:
./plot_Folder.py -m <pseudo_mcrab_directory> [opts]

Examples:
./plot_Folder.py -m <mcrab> --folder ""
./plot_Folder.py -m FakeBMeasurement_GE2Medium_GE1Loose0p80_StdSelections_BDTm0p80_AllSelections_BDT0p90_RandomSort_171120_100657 --url --folder ForFakeBMeasurementEWKFakeB --nostack

Last Used:

'''

#================================================================================================ 
# Imports
#================================================================================================ 
import sys
import math
import copy
import os
import re
import array
from optparse import OptionParser

import ROOT
ROOT.gROOT.SetBatch(True)
from ROOT import *

import HLTausAnalysis.NtupleAnalysis.tools.dataset as dataset
import HLTausAnalysis.NtupleAnalysis.tools.histograms as histograms
import HLTausAnalysis.NtupleAnalysis.tools.counter as counter
import HLTausAnalysis.NtupleAnalysis.tools.tdrstyle as tdrstyle
import HLTausAnalysis.NtupleAnalysis.tools.styles as styles
import HLTausAnalysis.NtupleAnalysis.tools.plots as plots
import HLTausAnalysis.NtupleAnalysis.tools.crosssection as xsect
import HLTausAnalysis.NtupleAnalysis.tools.multicrabConsistencyCheck as consistencyCheck
import HLTausAnalysis.NtupleAnalysis.tools.ShellStyles as ShellStyles

#================================================================================================ 
# Function Definition
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
    Verbose("Luminosity = %s (pb)" % (lumi), True)
    return lumi

def GetListOfEwkDatasets():
    Verbose("Getting list of EWK datasets")
    if 0: # TopSelection
        return  ["TT", "WJetsToQQ_HT_600ToInf", "SingleTop", "DYJetsToQQHT", "TTZToQQ",  "TTWJetsToQQ", "Diboson", "TTTT"]
    else: # TopSelectionBDT
        return  ["TT", "noTop", "SingleTop", "ttX"]


def GetDatasetsFromDir(opts):
    Verbose("Getting datasets")
    
    if (not opts.includeOnlyTasks and not opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=opts.searchMode, 
                                                        analysisName=opts.analysisName,
                                                        optimizationMode=opts.optMode)
    elif (opts.includeOnlyTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=opts.searchMode,
                                                        analysisName=opts.analysisName,
                                                        includeOnlyTasks=opts.includeOnlyTasks,
                                                        optimizationMode=opts.optMode)
    elif (opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=opts.dataEra,
                                                        searchMode=opts.searchMode,
                                                        analysisName=opts.analysisName,
                                                        excludeTasks=opts.excludeTasks,
                                                        optimizationMode=opts.optMode)
    else:
        raise Exception("This should never be reached")
    return datasets
    
def main(opts):

    #optModes = ["", "OptChiSqrCutValue50", "OptChiSqrCutValue100"]
    optModes = [""]

    if opts.optMode != None:
        optModes = [opts.optMode]
        
    # For-loop: All opt Mode
    for opt in optModes:
        opts.optMode = opt

        # Setup & configure the dataset manager 
        datasetsMgr = GetDatasetsFromDir(opts)
        datasetsMgr.updateNAllEventsToPUWeighted() #marina
        if 0:
            datasetsMgr.loadLuminosities() # from lumi.json

        # Set/Overwrite cross-sections
        datasetsToRemove = []
        for d in datasetsMgr.getAllDatasets():
            datasetsMgr.getDataset(d.getName()).setCrossSection(1.0)

        if opts.verbose:
            datasetsMgr.PrintCrossSections()
            datasetsMgr.PrintLuminosities()

        # Custom Filtering of datasets 
        for i, d in enumerate(datasetsToRemove, 0):
            msg = "Removing dataset %s" % d
            Print(ShellStyles.WarningLabel() + msg + ShellStyles.NormalStyle(), i==0)
            datasetsMgr.remove(filter(lambda name: d in name, datasetsMgr.getAllDatasetNames()))
        #if opts.verbose:
            #datasetsMgr.PrintInfo()

        # Merge histograms (see NtupleAnalysis/python/tools/plots.py) 
        plots.mergeRenameReorderForDataMC(datasetsMgr) 
        
        # Get Luminosity
        if 0:
            intLumi = datasetsMgr.getDataset("Data").getLuminosity()

        # Re-order datasets (different for inverted than default=baseline)
        newOrder = []
        # For-loop: All MC datasets
        for d in datasetsMgr.getMCDatasets():
            newOrder.append(d.getName())
            
        # Apply new dataset order!
        datasetsMgr.selectAndReorder(newOrder)
        
        # Print dataset information
        #datasetsMgr.PrintInfo()
        
        # Apply TDR style
        style = tdrstyle.TDRStyle()
        #style.setOptStat(True)
        style.setGridX(opts.gridX)
        style.setGridY(opts.gridY)

        # Define signal and background datasets names
        datasetSignal = "ChargedHiggs200_14TeV_L1TPU140"#"TT_TuneCUETP8M2T4_14TeV_L1TPU140"#"GluGluHToTauTau_14TeV_L1TPU140"
        datasetBkg    = "SingleNeutrino_L1TPU140"

        # Plot Histograms
        effHistoLists  = [["Calo_Eff", "Tk_Eff", "VtxIso_Eff", "RelIso_Eff"], ["DiTau_Eff_Calo", "DiTau_Eff_Tk", "DiTau_Eff_VtxIso", "DiTau_Eff_RelIso"]]
        rateHistoLists = [["Calo_Rate", "Tk_Rate", "VtxIso_Rate", "RelIso_Rate"], ["DiTau_Rate_Calo", "DiTau_Rate_Tk", "DiTau_Rate_VtxIso", "DiTau_Rate_RelIso"]]


        for i in range(0, len(effHistoLists)):
            PlotRateVsEff(datasetsMgr, effHistoLists[i], rateHistoLists[i], datasetSignal, datasetBkg)
            
    return


def PlotRateVsEff(datasetsMgr, effHistoList, rateHistoList, datasetSignal, datasetBkg):
    tgraphs=[]
    legendDict = {}

    # Get Histogram name and its kwargs
    if "ditau" in effHistoList[0].lower():
        saveName = "DiTau_RateVsEff_"+ datasetSignal.split("_")[0]
    else:
        saveName = "SingleTau_RateVsEff_"+ datasetSignal.split("_")[0]
    kwargs_  = GetHistoKwargs(saveName, opts)

    for i in range (0, len(effHistoList)):
        if (i==0) :
            g0 = convert2RateVsEffTGraph(datasetsMgr, effHistoList[i], rateHistoList[i], datasetSignal, datasetBkg)
            g0.SetName("Calo")
        elif (i==1):
            g1 = convert2RateVsEffTGraph(datasetsMgr, effHistoList[i], rateHistoList[i], datasetSignal, datasetBkg)
            g1.SetName("Tk")
        elif (i==2):
            g2 = convert2RateVsEffTGraph(datasetsMgr, effHistoList[i], rateHistoList[i], datasetSignal, datasetBkg)
            g2.SetName("VtxIso")
        elif (i==3):
            g3 = convert2RateVsEffTGraph(datasetsMgr, effHistoList[i], rateHistoList[i], datasetSignal, datasetBkg)
            g3.SetName("RelIso")

    # Create & draw the plot
    p = plots.ComparisonManyPlot(g0, [g1,g2, g3], saveFormats=[])
    
    # Set individual styles
    for index, h in enumerate(p.histoMgr.getHistos()):
        hName = h.getName()
        legendDict[hName] = styles.getCaloLegend(index)
        p.histoMgr.forHisto(hName, styles.getCaloStyle(index))

        p.histoMgr.setHistoDrawStyle(h.getName(), "PX")                                                                                                     
        p.histoMgr.setHistoLegendStyle(h.getName(), "LP")

    # Set legend labels
    p.histoMgr.setHistoLegendLabelMany(legendDict)

    # Get the x and y axis title
    #binWidthX = p.histoMgr.getHistos()[0].getRootHisto().GetXaxis().GetBinWidth(0)
    #binWidthY = p.histoMgr.getHistos()[0].getRootHisto().GetYaxis().GetBinWidth(0)
    #xlabel = kwargs_["xlabel"] + " / %s" % (GetBinwidthDecimals(binWidthX) % (binWidthX))
    #kwargs_["xlabel"] = xlabel
    #ylabel = kwargs_["ylabel"] + " / %s" % (GetBinwidthDecimals(binWidthY) % (binWidthY))
    #kwargs_["ylabel"] = ylabel



    # Draw and save the plot
    plots.drawPlot(p, saveName, **kwargs_) #the "**" unpacks the kwargs_ dictionary

    # Additional text                                                                                                                                                    
    histograms.addText(0.65, 0.38, plots._legendLabels[datasetSignal], 17)
    if "ditau" in saveName.lower():
        histograms.addText(0.77, 0.89,"DoubleTau", 20)
    else:
        histograms.addText(0.77, 0.89,"SingleTau", 20)
    # Save the plots in custom list of saveFormats
    SavePlot(p, saveName, os.path.join(opts.saveDir, opts.optMode, opts.folder), [".pdf",".png"] )          


    return

def convert2RateVsEffTGraph(datasetsMgr, effHistoName, rateHistoName, datasetSignal, datasetBkg):

    hEff  = datasetsMgr.getDataset(datasetSignal).getDatasetRootHisto(effHistoName).getHistogram()
    hRate = datasetsMgr.getDataset(datasetBkg).getDatasetRootHisto(rateHistoName).getHistogram()
    
    # Sanity Checks
    if (hEff.GetXaxis().GetBinWidth(0) != hRate.GetXaxis().GetBinWidth(0)):
        Print("Efficiency histogram '%s' and rate histogram '%s' have different binning." % (effHistoName,rateHistoName), True)
        sys.exit()
    if (hEff.GetNbinsX() != hRate.GetNbinsX()):
        Print("Efficiency histogram '%s' and rate histogram %s have different number of bins." % (effHistoName,rateHistoName), True)
        sys.exit()
    
    # Lists for values                                                                                                                                         
    x     = []
    y     = []
    xerrl = []
    xerrh = []
    yerrl = []
    yerrh = []
    
    nBinsX = hEff.GetNbinsX()

    for i in range (0, nBinsX):
        # Get values
        xVal  = hEff.GetBinContent(i)
        xLow  = hEff.GetBinError(i)
        xHigh = xLow
        yVal  = hRate.GetBinContent(i)
        yLow  = hRate.GetBinError(i)
        yHigh = yLow            
        
        # Store values
        x.append(xVal)
        xerrl.append(xLow)
        xerrh.append(xHigh)
            
        # Force error bars to not be above (belo) 1.0 (0.0)
        if 0:
            if abs(yVal + yHigh) > 1.0:
                yHigh = 1.0-yVal
            if yVal - yLow < 0.0:
                yLow = yVal

        
        # WARNING! Ugly trick so that zero points are not visible on canvas
        if 1:
            if yVal == 0.0:
                yVal  = -0.1
                yLow  = +0.0001
                yHigh = +0.0001
        
        # Save final values
        y.append(yVal)
        yerrl.append(yLow)
        yerrh.append(yHigh)
        
    # Create the TGraph with asymmetric errors
    tgraph = ROOT.TGraphAsymmErrors(nBinsX,
                                    array.array("d",x),
                                    array.array("d",y),
                                    array.array("d",xerrl),
                                    array.array("d",xerrh),
                                    array.array("d",yerrl),
                                    array.array("d",yerrh))
    

    # Construct info table (debugging)
    table  = []
    align  = "{0:>6} {1:^10} {2:>10} {3:>10} {4:>10} {5:^3} {6:<10}"
    header = align.format("#", "xLow", "Efficiency", "xUp", "Rate", "+/-", "Error") #Purity = 1-EWK/Data
    hLine  = "="*70
    table.append("")
    table.append(hLine)
    table.append("{0:^70}".format(effHistoName))
    table.append(header)
    table.append(hLine)
    
    # For-loop: All values x-y and their errors
    for i, xV in enumerate(x, 0):
        row = align.format(i+1, "%.4f" % xerrl[i], "%.4f" %  x[i], "%.4f" %  xerrh[i], "%.5f" %  y[i], "+/-", "%.5f" %  yerrh[i])
        table.append(row)
    table.append(hLine)

    if 0:#printValues:
        for i, line in enumerate(table, 1):
            Print(line, False) #i==1)        
   
    return tgraph

def GetHistoKwargs(h, opts):
    _moveLegend = {"dx": -0.1, "dy": -0.55, "dh": -0.15}
    logY    = True
    yMin    = 0.0
    if logY:
        yMin = 1
        yMaxF = 10
    else:
        yMaxF = 1.2
        
    _kwargs = {
        "xlabel"           : "Efficiency",
        "ylabel"           : "Rate (kHz)",
        "addMCUncertainty" : False, 
        "addLuminosityText": False,
        "addCmsText"       : True,
        "cmsExtraText"     : "Phase-2 Simulation",
        "cmsTextPosition"  : "outframe",
        "opts"             : {"xmin": 0.0, "xmax": 0.7, "ymin": yMin, "ymax":1000, "ymaxfactor": yMaxF},
        "opts2"            : {"ymin": 0.59, "ymax": 1.41},
        "log"              : logY,
        "moveLegend"       : _moveLegend,
        "xtitlesize"       : 0.1,#xlabelSize,
        "ytitlesize"       : 0.1,#ylabelSize,
        "cutBoxY"           : {"cutValue": 50, "fillColor": 16, "box": False, "line": True, "cutGreaterThan"   : False}
        }

    kwargs = copy.deepcopy(_kwargs)
    
    if "ditau" in h.lower():
        kwargs["opts"]   = {"xmin": 0.0, "xmax": 0.6, "ymin": yMin, "ymax":2000, "ymaxfactor": yMaxF}


    return kwargs

    
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


def getHistos(datasetsMgr, histoName):

    h1 = datasetsMgr.getDataset("Data").getDatasetRootHisto(histoName)
    h1.setName("Data")

    h2 = datasetsMgr.getDataset("EWK").getDatasetRootHisto(histoName)
    h2.setName("EWK")
    return [h1, h2]


def PlotHistograms(datasetsMgr, histoName):
    Verbose("Plotting Data-MC Histograms")

    # Get Histogram name and its kwargs
    saveName = histoName.rsplit("/")[-1]
    kwargs_  = GetHistoKwargs(saveName, opts)
    
    
    # Create the plotting object
    p = plots.MCPlot(datasetsMgr, histoName, saveFormats=[], normalizeToOne=True)
    # p = plots.ComparisonManyPlot(FakeB_inverted, compareHistos, saveFormats=[])

    # For-loop: All histos                                                                                                                                               
    for index, h in enumerate(p.histoMgr.getHistos()):
        if index == 0:
            continue
        else:
            #p.histoMgr.setHistoDrawStyle(h.getName(), "L")
            p.histoMgr.setHistoLegendStyle(h.getName(), "L")

    # Set default dataset style to all histos                                                                                                                            
    for index, h in enumerate(p.histoMgr.getHistos()):
        plots._plotStyles[p.histoMgr.getHistos()[index].getDataset().getName()].apply(p.histoMgr.getHistos()[index].getRootHisto())

    # Draw and save the plot
    plots.drawPlot(p, saveName, **kwargs_) #the "**" unpacks the kwargs_ dictionary

    # Save the plots in custom list of saveFormats
    SavePlot(p, saveName, os.path.join(opts.saveDir, opts.optMode, opts.folder), [".pdf"])#, ".png"] )
    return


def SavePlot(plot, plotName, saveDir, saveFormats = [".png", ".pdf"]):
    Verbose("Saving the plot in %s formats: %s" % (len(saveFormats), ", ".join(saveFormats) ) )

    # Check that path exists
    if not os.path.exists(saveDir):
        os.makedirs(saveDir)

    # Create the name under which plot will be saved
    saveName = os.path.join(saveDir, plotName.replace("/", "_").replace(" ", "").replace("(", "").replace(")", "") )
    # For-loop: All save formats
    for i, ext in enumerate(saveFormats):
        saveNameURL = saveName + ext
        #saveNameURL = saveNameURL.replace("/publicweb/a/aattikis/", "http://home.fnal.gov/~aattikis/")
        saveNameURL = saveNameURL.replace("/afs/cern.ch/user/m/mtoumazo/public/html/hltaus/", "https://cmsdoc.cern.ch/~mtoumazo/hltaus/")
        if opts.url:
            Print(saveNameURL, 1)
        else:
            Print(saveName + ext, 1)
        plot.saveAs(saveName, formats=saveFormats)
    return


#================================================================================================ 
# Main
#================================================================================================ 
if __name__ == "__main__":
    '''
    https://docs.python.org/3/library/argparse.html
 
    name or flags...: Either a name or a list of option strings, e.g. foo or -f, --foo.
    action..........: The basic type of action to be taken when this argument is encountered at the command line.
    nargs...........: The number of command-line arguments that should be consumed.
    const...........: A constant value required by some action and nargs selections.
    default.........: The value produced if the argument is absent from the command line.
    type............: The type to which the command-line argument should be converted.
    choices.........: A container of the allowable values for the argument.
    required........: Whether or not the command-line option may be omitted (optionals only).
    help............: A brief description of what the argument does.
    metavar.........: A name for the argument in usage messages.
    dest............: The name of the attribute to be added to the object returned by parse_args().
    '''
    
    # Default Settings
    ANALYSISNAME = None #"FakeBMeasurement"
    SEARCHMODE   = None #"80to1000"
    DATAERA      = None #"ID2017"
    GRIDX        = True
    GRIDY        = True
    OPTMODE      = None
    BATCHMODE    = True
    PRECISION    = 3
    INTLUMI      = -1.0
    SUBCOUNTERS  = False
    LATEX        = False
    URL          = True
    NOERROR      = True
    SAVEDIR      = "/afs/cern.ch/user/m/mtoumazo/public/html/hltaus/CaloTk/RateVsEff/" #os.getcwd()
    VERBOSE      = False
    FOLDER       = ""
    RATIO        = False
    NOSTACK      = False

    # Define the available script options
    parser = OptionParser(usage="Usage: %prog [options]")

    parser.add_option("-m", "--mcrab", dest="mcrab", action="store", 
                      help="Path to the multicrab directory for input")

    parser.add_option("-o", "--optMode", dest="optMode", type="string", default=OPTMODE, 
                      help="The optimization mode when analysis variation is enabled  [default: %s]" % OPTMODE)

    parser.add_option("-b", "--batchMode", dest="batchMode", action="store_false", default=BATCHMODE, 
                      help="Enables batch mode (canvas creation does NOT generate a window) [default: %s]" % BATCHMODE)

    parser.add_option("--analysisName", dest="analysisName", type="string", default=ANALYSISNAME,
                      help="Override default analysisName [default: %s]" % ANALYSISNAME)

    parser.add_option("--intLumi", dest="intLumi", type=float, default=INTLUMI,
                      help="Override the integrated lumi [default: %s]" % INTLUMI)

    parser.add_option("--searchMode", dest="searchMode", type="string", default=SEARCHMODE,
                      help="Override default searchMode [default: %s]" % SEARCHMODE)

    parser.add_option("--dataEra", dest="dataEra", type="string", default=DATAERA, 
                      help="Override default dataEra [default: %s]" % DATAERA)

    parser.add_option("--gridX", dest="gridX", action="store_true", default=GRIDX, 
                      help="Enable the x-axis grid lines [default: %s]" % GRIDX)

    parser.add_option("--gridY", dest="gridY", action="store_true", default=GRIDY, 
                      help="Enable the y-axis grid lines [default: %s]" % GRIDY)

    parser.add_option("--saveDir", dest="saveDir", type="string", default=SAVEDIR, 
                      help="Directory where all pltos will be saved [default: %s]" % SAVEDIR)

    parser.add_option("--url", dest="url", action="store_true", default=URL, 
                      help="Don't print the actual save path the histogram is saved, but print the URL instead [default: %s]" % URL)
    
    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=VERBOSE, 
                      help="Enables verbose mode (for debugging purposes) [default: %s]" % VERBOSE)

    parser.add_option("-i", "--includeOnlyTasks", dest="includeOnlyTasks", action="store", 
                      help="List of datasets in mcrab to include")

    parser.add_option("-e", "--excludeTasks", dest="excludeTasks", action="store", 
                      help="List of datasets in mcrab to exclude")

    parser.add_option("--folder", dest="folder", type="string", default = FOLDER,
                      help="ROOT file folder under which all histograms to be plotted are located [default: %s]" % (FOLDER) )

    parser.add_option("--ratio", dest="ratio", action="store_true", default = RATIO,
                      help="Draw ratio canvas for Data/MC curves? [default: %s]" % (RATIO) )

    parser.add_option("--nostack", dest="nostack", action="store_true", default = NOSTACK,
                      help="Do not stack MC histograms [default: %s]" % (NOSTACK) )

    (opts, parseArgs) = parser.parse_args()

    # Require at least two arguments (script-name, path to multicrab)
    if len(sys.argv) < 2:
        parser.print_help()
        sys.exit(1)

    if opts.mcrab == None:
        Print("Not enough arguments passed to script execution. Printing docstring & EXIT.")
        parser.print_help()
        #print __doc__
        sys.exit(1)

    # Sanity check
    allowedFolders = [""]

    if opts.folder not in allowedFolders:
        Print("Invalid folder \"%s\"! Please select one of the following:" % (opts.folder), True)
        for m in allowedFolders:
            Print(m, False)
        sys.exit()
    
    # Call the main function
    main(opts)

    if not opts.batchMode:
        raw_input("=== plot_Folder.py: Press any key to quit ROOT ...")