#!/usr/bin/env python
'''

Usage (single plot):
./plotL1TkTau.py -m <multicrab_directory> <jsonfile> [opts]

Usage (multiple plots):
./plotL1TkTau.py -m <pseudo_mcrab_directory> json/*.json
./plotL1TkTau.py -m <pseudo_mcrab_directory> json/*.json json/L1TkTau/*.json

Last Used:
./plotL1TkTau.py -m multicrab_CaloTkSkim_v910pre2_20170522T1611/ json/L1TkTau*/* -i "SingleNeutrino_PU140|TT_TuneCUETP8M1_14TeV_PU140"
./plotL1TkTau.py -m multicrab_CaloTkSkim_v910pre2_20170522T1611/ json/L1TkTau*/* -i "SingleNeutrino_PU200|TT_TuneCUETP8M1_14TeV_PU200"
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

def GetDatasetsFromDir(opts, json):
    Verbose("Getting datasets")
    
    if (not opts.includeOnlyTasks and not opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=json["dataEra"],
                                                        searchMode=None,
                                                        includeOnlyTasks="|".join(json["datasets"]),
                                                        analysisName=json["analysis"])
    elif (opts.includeOnlyTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=json["dataEra"],
                                                        searchMode=None,
                                                        analysisName=json["analysis"],
                                                        includeOnlyTasks=opts.includeOnlyTasks)
    elif (opts.excludeTasks):
        datasets = dataset.getDatasetsFromMulticrabDirs([opts.mcrab],
                                                        dataEra=json["dataEra"],
                                                        searchMode=None,
                                                        analysisName=json["analysis"],
                                                        excludeTasks=opts.excludeTasks)
    else:
        raise Exception("This should never be reached")
    return datasets
    
    
def Plot(jsonfile, opts):

    with open(os.path.abspath(jsonfile)) as jfile:
        j = json.load(jfile)
        Verbose("Plotting %s. Will save under \"%s\"" % (j["saveName"], opts.saveDir), True)

        # Setup & configure the dataset manager
        datasetsMgr = GetDatasetsFromDir(opts, j)
        if 0:
            datasetsMgr.loadLuminosities()
        #datasetsMgr.updateNAllEventsToPUWeighted()

        # Print information
        if opts.verbose:
            datasetsMgr.PrintCrossSections()
            datasetsMgr.PrintLuminosities()

        # Set/Overwrite cross-sections
        for d in datasetsMgr.getAllDatasets():
            if "ChargedHiggs" in d.getName():
                datasetsMgr.getDataset(d.getName()).setCrossSection(1.0)

        ## Print dataset information (before merge)        
        if 0:
            datasetsMgr.PrintInfo()
        
        # Merge histograms (see NtupleAnalysis/python/tools/plots.py)    
        plots.mergeRenameReorderForDataMC(datasetsMgr)

        # Print dataset information (after merge)
        if 0:
            datasetsMgr.PrintInfo()

        # Plot the histogram
        doPlots(datasetsMgr, j)
        return


def doPlots(datasetsMgr, json):

    # Create the MC Plot with selected normalization ("normalizeToOne", "normalizeByCrossSection", "normalizeToLumi")
    ylabel_ = json["ylabel"]
    if json["normalization"]=="normalizeToLumi":
        kwargs = {}
        p = plots.MCPlot(datasetsMgr, json["histograms"][0], normalizeToLumi=opts.intLumi, saveFormats=[]) #**kwargs)

    elif json["normalization"]=="normalizeToOne":
        ylabel_ = ylabel_.replace(json["ylabel"].split(" /")[0], "Arbitrary Units")
        kwargs  = {json["normalization"]: True}
        p = plots.MCPlot(datasetsMgr, json["histograms"][0], saveFormats=[], normalizeToOne=True)

        # Customize binwidth on y axis title
        binWidth = p.histoMgr.getHistos()[0].getRootHisto().GetXaxis().GetBinWidth(0)
        ylabel_ = ylabel_.replace(json["ylabel"].split(" /")[-1], GetBinwidthDecimals(binWidth)) 

    else:
        raise Exception("Invalid normalization \"%s\"" % (json["normalization"]) )

    # Label size (optional. Commonly Used in counters)
    xlabelSize = None
    if "xlabelsize" in json:
        xlabelSize = json["xlabelsize"]
    ylabelSize = None
    if "ylabelsize" in json:
        ylabelSize = json["ylabelsize"]

    # For-loop: All histos
    for index, h in enumerate(p.histoMgr.getHistos()):
        if index == 0:
            p.histoMgr.setHistoDrawStyle(h.getName(), "HIST")
            p.histoMgr.setHistoLegendStyle(h.getName(), "L")
            #    continue
        else:
            p.histoMgr.setHistoDrawStyle(h.getName(), "AP")
            p.histoMgr.setHistoLegendStyle(h.getName(), "AP")

    # Set default dataset style to all histos
    for index, h in enumerate(p.histoMgr.getHistos()):
        plots._plotStyles[p.histoMgr.getHistos()[index].getDataset().getName()].apply(p.histoMgr.getHistos()[index].getRootHisto())
       #plots._plotStyles[dataset.getName()].apply(p)

    # Additional text
    histograms.addText(json["extraText"].get("x"), json["extraText"].get("y"), json["extraText"].get("text"), json["extraText"].get("size") )
    
    # Draw a customised plot
    saveName = json["saveName"]

    # Draw the plot
    plots.drawPlot(p, 
                   saveName,                  
                   xlabel            = json["xlabel"], 
                   ylabel            = ylabel_,
                   rebinX            = json["rebinX"],
                   stackMCHistograms = json["stackMCHistograms"]=="True", 
                   addMCUncertainty  = json["addMCUncertainty"]=="True" and json["normalization"]!="normalizeToOne",
                   addLuminosityText = json["addLuminosityText"]=="True",
                   addCmsText        = json["addCmsText"]=="True",
                   cmsExtraText      = json["cmsExtraText"],
                   cmsTextPosition   = "outframe", 
                   opts              = json["opts"],
                   #opts2             = json["ratioOpts"],
                   log               = json["logY"]=="True", 
                   errorBarsX        = json["errorBarsX"]=="True", 
                   moveLegend        = {"dx": -0.11, "dy": -0.01, "dh": -0.13},
                   cutBox            = {"cutValue": json["cutValue"], "fillColor": json["cutFillColour"], "box": json["cutBox"]=="True", "line": json["cutLine"]=="True", "greaterThan": json["cutGreaterThan"]=="True"},
                   #ratio             = json["ratio"]=="True",
                   #ratioInvert       = json["ratioInvert"]=="True",
                   #ratioYlabel       = json["ratioYlabel"],
                   xlabelsize        = xlabelSize,
                   ylabelsize        = ylabelSize,
                   )

    # Remove legend?
    if json["removeLegend"] == "True":
        p.removeLegend()

    # Save in all formats chosen by user
    aux.SavePlot(p, opts.saveDir, saveName, opts.saveFormats, opts.url)
    return


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


def main(opts):
    
    # The available ROOT options for the Error-Ignore-Level are (const Int_t):  
    ROOT.gErrorIgnoreLevel=0 # kUnset=-1, kPrint=0, kInfo=1000, kWarning=2000, kError=3000, kBreak=4000

    # Apply TDR style
    style = tdrstyle.TDRStyle()
    style.setGridX(opts.gridX)
    style.setGridY(opts.gridY)
    style.setOptStat(False)

    jsonFiles = []
    # For-loop: All system script arguments
    for arg in sys.argv[1:]:

        # Skip if not a json file
        if ".json" not in arg:
            continue

        # Sanity check - File exists
        if not os.path.exists(arg):
            Print("The JSON file \"%s\" does not seem to be a valid path.. Please check that the file exists. Exit" % (arg), True)
            sys.exit()

        # Load & append json file
        with open(os.path.abspath(arg)) as jsonFile:
            try:
                json.load(jsonFile)
                jsonFiles.append(arg)
            except ValueError, e:
                Print("Problem loading JSON file %s. Please check the file" % (arg))
                sys.exit()

    # Sanity check - At least 1 json file found
    if len(jsonFiles) == 0:
        Print("No JSON files found. Please read the script instructions. Exit", True)
        print __doc__
        sys.exit()    

    # For-loop: All json files
    for j in jsonFiles:
        Print("Processing JSON file \"%s\"" % (j), True)
        Plot(j, opts) 

    Print("All plots saved under directory %s" % (ShellStyles.NoteStyle() + aux.convertToURL(opts.saveDir, opts.url) + ShellStyles.NormalStyle()), True)
    return


#================================================================================================
# Main
#================================================================================================
if __name__ == "__main__":

    # Default Settings 
    global opts
    BATCHMODE   = True
    VERBOSE     = False
    INTLUMI     = 1.0
    SAVEDIR     = None
    SAVEFORMATS = [".C", ".png", ".pdf"]
    GRIDX       = False
    GRIDY       = False    

    parser = OptionParser(usage="Usage: %prog [options]" , add_help_option=False,conflict_handler="resolve")

    parser.add_option("-v", "--verbose", dest="verbose", action="store_true", default=VERBOSE, 
                      help="Enables verbose mode (for debugging purposes) [default: %s]" % VERBOSE)

    parser.add_option("-b", "--batchMode", dest="batchMode", action="store_false", default=BATCHMODE, 
                      help="Enables batch mode (canvas creation  NOT generates a window) [default: %s]" % BATCHMODE)

    parser.add_option("-m", "--mcrab", dest="mcrab", action="store", 
                      help="Path to the multicrab directory for input")

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


    (opts, parseArgs) = parser.parse_args()

    # Require at least two arguments (script-name, path to multicrab)
    if opts.mcrab == None:
        Print("Not enough arguments passed to script execution. Printing docstring & EXIT.")
        print __doc__
        sys.exit(0)

    # Determine path for saving plots
    if opts.saveDir == None:
        opts.saveDir = aux.getSaveDirPath(opts.mcrab, prefix="", postfix="Test")

    # Overwrite default save formats?
    if opts.formats != None:
        opts.saveFormats = opts.formats.split(",")
    else:
        opts.saveFormats = SAVEFORMATS

    # Call the main function
    main(opts)

    if not opts.batchMode:
        raw_input("=== plotL1TkTau.py: Press any key to quit ROOT ...")
