#ifndef L1TkTauParticle_cxx
#define L1TkTauParticle_cxx

// User
#include "../../Auxiliary/interface/constants.h"
#include "../interface/L1TkTauParticle.h"

//****************************************************************************
L1TkTauParticle::L1TkTauParticle()
//****************************************************************************
{

  theVtxIsolation = 999.9;
  theRelIsolation = 0.0;
  theRelIsolationDeltaZ0 = 0.0;
  theMatchingGenParticle_dR = 0.0;
  theNProngs = 0;


}

//****************************************************************************
L1TkTauParticle::L1TkTauParticle(double matchCone_dRMin,
				 double matchCone_dRMax,
				 double sigCone_dRMin,
				 double sigCone_dRMax,
				 double isoCone_dRMin,
				 double isoCone_dRMax)
//****************************************************************************
{

  theMatchCone_dRMin  = matchCone_dRMin;
  theMatchCone_dRMax  = matchCone_dRMax;
  theSigCone_dRMin    = sigCone_dRMin;
  theSigCone_dRMax    = sigCone_dRMax;
  theIsoCone_dRMin    = isoCone_dRMin;
  theIsoCone_dRMax    = isoCone_dRMax;
  SetVtxIsolation(9999.9);
  SetRelIsolation(0.0);
  SetMatchGenp(-1.0, 9999.9);

  InitVars_();

}


//****************************************************************************
void L1TkTauParticle::InitVars_(void)
//****************************************************************************
{
  theMatchingGenParticle_dR = 999.9;
  return;
}

				 
//****************************************************************************
L1TkTauParticle::L1TkTauParticle(int caloTau_Index, 
				 int matchTk_Index, 
				 double matchTk_deltaR, 
				 vector<int> sigTks_Index, 
				 vector<int> isoTks_Index,
				 double vtxIso, 
				 double relIso,
				 double sigCone_minDeltaR, 
				 double sigCone_maxDeltaR, 
				 double isoCone_minDeltaR, 
				 double isoCone_maxDeltaR)
//****************************************************************************
{
  
  SetCaloTau(caloTau_Index);
  SetMatchTk(matchTk_Index);
  SetMatchTkDeltaR(matchTk_deltaR);
  SetSigConeTks(sigTks_Index);
  SetIsoConeTks(isoTks_Index);
  SetVtxIsolation(vtxIso);
  SetRelIsolation(relIso);
  SetMatchGenp(-1.0, 9999.9);
  SetSignalConeSize(sigCone_minDeltaR,  sigCone_maxDeltaR);
  SetIsolationConeSize(isoCone_minDeltaR, isoCone_maxDeltaR);
}



//****************************************************************************
void L1TkTauParticle::SetSignalConeSize(double deltaR_min, double deltaR_max)
//****************************************************************************
{
  sigCone_minDeltaR_ = deltaR_min;
  sigCone_maxDeltaR_ = deltaR_max;
  
  return;
}



//****************************************************************************
void L1TkTauParticle::SetIsolationConeSize(double deltaR_min, double deltaR_max)
//****************************************************************************
{
  isoCone_minDeltaR_ = deltaR_min;
  isoCone_maxDeltaR_ = deltaR_max;
  
  return;
}



//============================================================================
double L1TkTauParticle::CalculateRelIso(const double relIso_dZ0,
					bool bStoreValue,
					bool bInvert_deltaZ0,
					bool bUseIsoCone)

//============================================================================
{
  
  // 
  if (bStoreValue) SetRelIsolation(0.0);

  // Return not Tk-Confirmed
  if (!HasMatchingTk()) return 0.0; 

  // If no tracks found in the isoalation cone return
  vector<TTTrack> isoTks;
  if (bUseIsoCone) isoTks = GetIsoConeTTTracks();
  else isoTks = GetIsoAnnulusTTTracks();

  // Sanity
  if ( (isoTks.size() < 1) )  return 0.0;

  // Initialise variables
  TTTrack matchTk = GetMatchingTk();
  double isoTks_scalarSumPt  = 0.0;
  double deltaZ0 = 999.9;
  double relIso  = 0.0;
  
  // For-loop: All Tracks in isolation cone 
  for (size_t i = 0; i < isoTks.size(); i++)
    {
      TTTrack isoConeTk = isoTks.at(i);
      
      // Find the track closest in Z0
      deltaZ0 = abs(matchTk.getZ0() - isoConeTk.getZ0());

      // Decide on type of calculation
      bool considerTk  = false;
      bool considerTk_default = (deltaZ0 < relIso_dZ0);
      bool considerTk_invert  = (deltaZ0 > relIso_dZ0);
      if (bInvert_deltaZ0) considerTk = considerTk_invert;
      else considerTk = considerTk_default;
      
      // Add-up the pT of alltracks in isolation cone/annulus
      if (considerTk) isoTks_scalarSumPt += isoConeTk.getPt();
    }

  // Calculated + Assign value of relative isolation
  relIso = isoTks_scalarSumPt/matchTk.getPt();
  if (bStoreValue)
    {
      SetRelIsolationDeltaZ0(relIso_dZ0);
      SetRelIsolation(relIso);
    }
  
  return relIso;
}


//============================================================================
double L1TkTauParticle::CalculateVtxIso(bool bStoreValue,
					bool bUseIsoCone)
//============================================================================
{

  // Store default values
  double deltaZ0 = 999.9;
  double deltaZ0_tmp = 999.9;
  if (bStoreValue) SetVtxIsolation(deltaZ0);
  
  // Return not Tk-Confirmed
  if (!HasMatchingTk()) return 999.9; 

  // If no tracks found in the isoalation cone return
  vector<TTTrack> isoTks; // = GetIsoConeTTTracks();
  if (bUseIsoCone) isoTks = GetIsoConeTTTracks();
  else isoTks = GetIsoAnnulusTTTracks();

  // Return large value if no isolation track exists
  if ( (isoTks.size() < 1) )  return 999.9;

  // Initialise variables
  TTTrack matchTk = GetMatchingTk();
  
  // For-loop: All Tracks in isolation cone 
  for (size_t i = 0; i < isoTks.size(); i++)
    {
      TTTrack isoConeTk = isoTks.at(i);
      
      // Find the track closest in Z0
      deltaZ0_tmp = abs(matchTk.getZ0() - isoConeTk.getZ0());
      
      if (deltaZ0_tmp < deltaZ0)
      	{
	  deltaZ0 = deltaZ0_tmp;
      	  if (bStoreValue) SetVtxIsolation(deltaZ0);
	  if (bStoreValue) SetVtxIsolationTrack(isoConeTk);
      	}
    }

  // Calculated + Assign value of relative isolation
  return deltaZ0;
}


//****************************************************************************
void L1TkTauParticle::SetMatchGenp(int matchGenp_Index, double matchGenp_deltaR) 
//****************************************************************************
{ 
  matchGenp_Index_  = matchGenp_Index;
  matchGenp_deltaR_ = matchGenp_deltaR;
  
  return;
}


//****************************************************************************
TTTrack L1TkTauParticle::GetSigConeLdgTk(void)
//****************************************************************************
{
  
  // Temporarily set the leading track
  vector<TTTrack> theTracks = GetSigConeTTTracks();
  TTTrack ldgTk = theTracks.at(0);
  
  // For-loop: All Tracks
  for (size_t i = 0; i < theTracks.size(); i++)
    {
      
      TTTrack tk = theTracks.at(i);
      // ldgTk = tk; //marina : this shouldn't be here

      // Find new leading track
      if (tk.getPt() > ldgTk.getPt() ) ldgTk = tk;
      
    }

  return ldgTk;  
}



//****************************************************************************
TTTrack L1TkTauParticle::GetIsoConeLdgTk(void)
//****************************************************************************
{

  // Temporarily set the leading track
  vector<TTTrack> theTracks = GetIsoConeTTTracks();
  TTTrack ldgTk = theTracks.at(0);
  
  // For-loop: All Tracks
  for (size_t i = 0; i < theTracks.size(); i++)
    {

      TTTrack tk = theTracks.at(i);
      ldgTk = tk;

      // Find new leading track
      if (tk.getPt() > ldgTk.getPt() ) ldgTk = tk;
      
    }
  
  return ldgTk;  
}

//****************************************************************************
TTTrack L1TkTauParticle::GetIsoAnnulusLdgTk(void)
//****************************************************************************
{

  // Temporarily set the leading track
  vector<TTTrack> theTracks = GetIsoAnnulusTTTracks();
  TTTrack ldgTk = theTracks.at(0);
  
  // For-loop: All Tracks
  for (size_t i = 0; i < theTracks.size(); i++)
    {

      TTTrack tk = theTracks.at(i);
      ldgTk = tk;

      // Find new leading track
      if (tk.getPt() > ldgTk.getPt() ) ldgTk = tk;
      
    }
  
  return ldgTk;  
}


//****************************************************************************
void L1TkTauParticle::PrintProperties(bool bPrintCaloTau,
				      bool bPrintMatchTk,
				      bool bPrintSigConeTks,
				      bool bPrintIsoConeTks,
				      bool bPrintMatchGenParticle,
				      bool bPrintHeaders)
//****************************************************************************
{
  
  Table info("Match-Cone | Sig-Cone | Iso-Cone | Calo-Et | Calo-Eta | Tk-Pt | Tk-Eta | Tk-dR | Gen-Pt | Gen-Eta | Gen-dR | Sig-Tks | Iso-Tks (Cone) | Iso-Tks (Annulus) | VtxIso | RelIso dZ0 (cm) | RelIso (Cone) | RelIso (Annulus) | RelIso", "Text");
  info.AddRowColumn(0, auxTools.ToString( GetMatchConeMin(), 2) + " < dR < " + auxTools.ToString( GetMatchConeMax(), 2) );
  info.AddRowColumn(0, auxTools.ToString( GetSigConeMin()  , 2) + " < dR < " + auxTools.ToString( GetSigConeMax()  , 2) );
  info.AddRowColumn(0, auxTools.ToString( GetIsoConeMin()  , 2) + " < dR < " + auxTools.ToString( GetIsoConeMax()  , 2) ); 
  info.AddRowColumn(0, auxTools.ToString( GetCaloTau().et()       ,3  ) );
  info.AddRowColumn(0, auxTools.ToString( GetCaloTau().eta()      ,3  ) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingTk().getPt() ,3  ) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingTk().getEta(),3  ) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingTkDeltaR()   ,3  ) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingGenParticle().pt() , 3) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingGenParticle().eta(), 3) );
  info.AddRowColumn(0, auxTools.ToString( GetMatchingGenParticleDeltaR(), 3) );  
  info.AddRowColumn(0, auxTools.ToString( GetSigConeTTTracks().size() ) );
  info.AddRowColumn(0, auxTools.ToString( GetIsoConeTTTracks().size() ) );
  info.AddRowColumn(0, auxTools.ToString( GetIsoAnnulusTTTracks().size() ) );
  info.AddRowColumn(0, auxTools.ToString( GetVtxIsolation(), 3) );
  double relIso_cone    = CalculateRelIso(GetRelIsolationDeltaZ0(), false, false, true );
  double relIso_annulus = CalculateRelIso(GetRelIsolationDeltaZ0(), false, false, false);
  info.AddRowColumn(0, auxTools.ToString( GetRelIsolationDeltaZ0(), 3) );
  info.AddRowColumn(0, auxTools.ToString( relIso_cone, 3) );
  info.AddRowColumn(0, auxTools.ToString( relIso_annulus, 3) ); 
  info.AddRowColumn(0, auxTools.ToString( GetRelIsolation(), 3) ); 
  info.Print(bPrintHeaders);
  
  if (bPrintCaloTau) GetCaloTau().PrintProperties();
  if (bPrintMatchTk && HasMatchingTk()) GetMatchingTk().PrintProperties();

  if (bPrintSigConeTks)
    {
      PrintTTTracks(GetSigConeTTTracks(), "Sig-Cone Tks");
      // PrintTTPixelTracks(GetSigConeTTPixelTracks(), "Sig-Cone Tks");
    }
  
  if (bPrintIsoConeTks)
    {
      PrintTTTracks(GetIsoConeTTTracks(), "Iso-Cone Tks");
      PrintTTTracks(GetIsoAnnulusTTTracks(), "Iso-Annulus Tks");
    }

  if (bPrintMatchGenParticle) GetMatchingGenParticle().PrintProperties();

      
  return;
}


//****************************************************************************
void L1TkTauParticle::PrintTTTracks(vector<TTTrack> theTracks,
				    string theTrackType)
//****************************************************************************
{

Table table(theTrackType + " # | Pt | Eta | Phi | z0 (cm) | dZ0 (cm) | d0 (cm) | Q | Chi2 | DOF | Chi2Red | Stubs (PS)", "Text");

// For-loop: All Tracks
 for (size_t i = 0; i < theTracks.size(); i++)
   {
     
     TTTrack tk = theTracks.at(i);
     
     // Fill table
     table.AddRowColumn(i, auxTools.ToString(i+1) );
     table.AddRowColumn(i, auxTools.ToString( tk.getPt() , 3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getEta(), 3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getPhi(), 3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getZ0() , 3  ) );
     table.AddRowColumn(i, auxTools.ToString( abs(GetMatchingTk().getZ0()- tk.getZ0()) , 3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getD0() , 3  ) );
     // table.AddRowColumn(i, auxTools.ToString( tk.getQ()  , 3  ) );
     table.AddRowColumn(i, auxTools.ToString( "N/A", 3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getChi2(),3  ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getDOF()     ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getChi2Red(), 3 ) );
     table.AddRowColumn(i, auxTools.ToString( tk.getNumOfStubs()) );// + " (" + auxTools.ToString(tk.getNumOfStubsPS()) + ")");
   }
  
if (theTracks.size() > 0) table.Print();
  
return;
}


//****************************************************************************
void L1TkTauParticle::PrintTTPixelTracks(vector<TTPixelTrack> theTracks,
					 string theTrackType)
//****************************************************************************
{

Table table(theTrackType + " # | Pt | Eta | Phi | z0 | d0 | Q | Chi2 | RedChi2 | Hits | Hit-Pattern | Hit-Type | Hit-R | Hit-Z", "Text");

// For-loop: All Tracks
for (size_t i = 0; i < theTracks.size(); i++)
  {

TTPixelTrack tk = theTracks.at(i);

// Fill table
table.AddRowColumn(i, auxTools.ToString(i+1) );
table.AddRowColumn(i, auxTools.ToString( tk.getPt()  , 3) );
table.AddRowColumn(i, auxTools.ToString( tk.getEta() , 3) );
table.AddRowColumn(i, auxTools.ToString( tk.getPhi() , 3) );
table.AddRowColumn(i, auxTools.ToString( tk.getZ0()  , 3) );
table.AddRowColumn(i, auxTools.ToString( tk.getD0()  , 3) );
table.AddRowColumn(i, tk.getQ() );
table.AddRowColumn(i, auxTools.ToString( tk.getChi2()   , 3 ) );
table.AddRowColumn(i, auxTools.ToString( tk.getChi2Red(), 3) );
table.AddRowColumn(i, auxTools.ToString( tk.getNhit()) + " (" + auxTools.ToString(tk.getCandidatePixelHits().size()) + ")" );
table.AddRowColumn(i, auxTools.ToString( tk.getPixelHitsPattern()) );
table.AddRowColumn(i, auxTools.ConvertIntVectorToString( tk.getPixHitsType()) );
table.AddRowColumn(i, auxTools.ConvertIntVectorToString( tk.getPixHitsR() )   );
}
  
if (theTracks.size() > 0) table.Print();
  
return;
}


//****************************************************************************
void L1TkTauParticle::SetSigConeTTTracksP4_(void)
//****************************************************************************
{

  // Variables
  vector<TTTrack> TTTracks = GetSigConeTTTracks();
  TLorentzVector sigTks_p4(0, 0, 0, 0);
  for (vector<TTTrack>::iterator t = TTTracks.begin(); t != TTTracks.end(); t++)
    {
      TLorentzVector p4;
      p4.SetPtEtaPhiM(t->getPt(), t->getEta(), t->getPhi(), pionMass); // assume track is a pion (most likely true!)
      sigTks_p4 += p4;
    }

  theSigConeTTTracksP4 = sigTks_p4;
  return;
}


//****************************************************************************
void L1TkTauParticle::SetIsoConeTTTracksP4_(void)
//****************************************************************************
{

  // Variables
  vector<TTTrack> TTTracks = GetIsoConeTTTracks();
  TLorentzVector isoTks_p4(0, 0, 0, 0);
  for (vector<TTTrack>::iterator t = TTTracks.begin(); t != TTTracks.end(); t++)
    {
      TLorentzVector p4;
      p4.SetPtEtaPhiM(t->getPt(), t->getEta(), t->getPhi(), pionMass); // assume track is a pion (most likely true!)
      isoTks_p4 += p4;
    }

  theIsoConeTTTracksP4 = isoTks_p4;
  return;
}

//****************************************************************************
void L1TkTauParticle::SetIsoAnnulusTTTracksP4_(void)
//****************************************************************************
{

  // Variables
  vector<TTTrack> TTTracks = GetIsoAnnulusTTTracks();
  TLorentzVector isoTks_p4(0, 0, 0, 0);
  for (vector<TTTrack>::iterator t = TTTracks.begin(); t != TTTracks.end(); t++)
    {
      TLorentzVector p4;
      p4.SetPtEtaPhiM(t->getPt(), t->getEta(), t->getPhi(), pionMass); // assume track is a pion (most likely true!)
      isoTks_p4 += p4;
    }

  theIsoAnnulusTTTracksP4 = isoTks_p4;
  return;
}


//****************************************************************************
TLorentzVector L1TkTauParticle::GetSigConeTTTracksP4(void)
//****************************************************************************
{
  SetSigConeTTTracksP4_();
  return theSigConeTTTracksP4;
 
}

//****************************************************************************
TLorentzVector L1TkTauParticle::GetIsoConeTTTracksP4(void)
//****************************************************************************
{

  SetIsoConeTTTracksP4_();
  return theIsoConeTTTracksP4;
}

//****************************************************************************
TLorentzVector L1TkTauParticle::GetIsoAnnulusTTTracksP4(void)
//****************************************************************************
{

  SetIsoAnnulusTTTracksP4_();
  return theIsoAnnulusTTTracksP4;
}

#endif
