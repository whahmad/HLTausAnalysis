//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
// USAGE::
// .x run.cc(<multicrab_dir>, <sample_alias>, <text_to_append_to_output>, <numberOfEvents>);
//
// EXAMPLE (interactive):
// root -l
// root[0] .x run.cc("/eos/user/m/mtoumazo/multicrab_HLTaus_v1015_20180710T1650", "SingleNeutrino_L1TPU140", "", -1)
// 
// EXAMPLE (batch mode):
// sh
// root -l -b -q "run.cc(\"/eos/user/m/mtoumazo/multicrab_HLTaus_v1015_20180710T1650\", \"ChargedHiggs500_14TeV_L1TPU200\", \"\", -1)"
//////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
#include "../CaloTk.C+" // how to compile macro in ROOT6 (compatible with ROOT5 as well)
//#include <TROOT.h>
#include <TError.h>

void run(const std::string MulticrabDir = "", 
	 const std::string SampleName = "", 
	 const std::string text = "", 
	 const int maxEvents = -1)
{

  // Suppress ROOT warnings (https://root-forum.cern.ch/t/gerrorignorelevel-problem/13178/3)
  gErrorIgnoreLevel = kFatal; 

  CaloTk macro(MulticrabDir, SampleName, text, maxEvents);
  macro.Loop();
}
