#ifndef L1TkEGParticle_h
#define L1TkEGParticle_h

// System
#include <iostream>

// User
#include "../../Auxiliary/src/AuxTools.C"
#include "../../DataFormat/interface/TTTrack.h"
#include "../../DataFormat/src/L1EG.C"
#include "../../DataFormat/src/EG.C"
#include "../../DataFormat/interface/GenParticle.h"
//#include "../../DataFormat/interface/TTPixelTrack.h"

using namespace std;

class L1TkEGParticle{     
 public:
  // Constructors
  L1TkEGParticle();
  L1TkEGParticle(vector<TTTrack> tracks,
		 vector<EG> EGs, 
		 float sigCone_dRMin, 
		 float sigCone_dRMax, 
		 float isoCone_dRMin, 
		 float isoCone_dRMax,
		 GenParticle genTau,
		 bool match);

  L1TkEGParticle(double vtxIso,
		 double relIso,
		 double CHF,
		 double NHF, 
		 double shrinkConeConst,
		 double sigConeMaxOpen,
		 //double sigConeMin, 
		 //double sigConeMax, 
		 //double isoConeMin, 
		 //double isoConeMax,
		 vector<TTTrack> isoTracks,
		 vector<EG> signalEGs,
		 vector<EG> isoEGs);
  
  // Destructor
  ~L1TkEGParticle() {};
  
  // Function declarations
  void InitVars_(void);
  void PrintTTTracks();
  float CorrectedEta(float eta, float zTrack);
  void AddTrack(TTTrack trk) { theTracks.push_back(trk); }
  void AddEG(EG eg) { theEGs.push_back(eg); }
  TTTrack GetLeadingTrack() const { return theTracks[0]; } 
  vector<TTTrack> GetTracks() const {return theTracks; }
  vector<EG> GetEGs() const{ return theEGs;}
  bool HasMatchingGenParticle(void) const{return theMatching;}
  GenParticle GetMatchingGenParticle() const {return theGenTau;}
  TLorentzVector GetTracksP4();
  TLorentzVector GetEGsP4();
  TLorentzVector GetTotalP4();
  
  void SetShrinkingConeConst(double shrinkConeConst) {shrinkConeCons_ = shrinkConeConst;}
  void SetSigConeCutOffdR(double sigConeMaxOpen) {sigConeMaxOpen_ = sigConeMaxOpen;}
  double GetShrinkingConeConst() const {return shrinkConeCons_;}
  double GetSigConeMaxOpen() const {return sigConeMaxOpen_;}
  double GetSigConeMin() const {return theSigCone_dRMin;}
  double GetSigConeMax() const {return theSigCone_dRMax;}
  double GetIsoConeMin() const {return theIsoCone_dRMin;}
  double GetIsoConeMax() const {return theIsoCone_dRMax;}
  
  void FindIsoConeTracks(vector<TTTrack> TTTracks, bool useIsoCone=false);
  void SetIsoConeTracks(vector<TTTrack> isoTracks) {isoTracks_ = isoTracks;}
  vector<TTTrack> GetIsoConeTracks() const {return isoTracks_;}

  void FindSignalConeEGs(vector<EG> EGs);
  void SetSignalConeEGs(vector<EG> signalEGs) {signalEGs_ = signalEGs;}
  vector<EG> GetSignalConeEGs() const {return signalEGs_;}

  void FindIsoConeEGs(vector<EG> EGs, bool useIsoCone=false);
  void SetIsoConeEGs(vector<EG> isoEGs) {isoEGs_ = isoEGs;}
  vector<EG> GetIsoConeEGs() const {return isoEGs_;}
  
  double CalculateVtxIso(vector<TTTrack> TTTracks, bool useIsoCone=false); 
  double CalculateRelIso(vector<TTTrack> TTTracks, vector<EG> EGs, double deltaZ0_max=999.9, bool useIsoCone=false);
  double GetVtxIso()  const { return vtxIso_;}
  double GetRelIso()  const { return relIso_;}
  void SetVtxIso(double vtxIso) { vtxIso_ = vtxIso;}
  void SetRelIso(double relIso) { relIso_ = relIso;}
  double GetCHF() const { return CHF_;}
  void SetCHF(double CHF) { CHF_ = CHF;}
  double GetNHF() const { return NHF_;}
  void SetNHF(double NHF) { NHF_ = NHF;}

  double vtxIso_;
  double relIso_;
  double CHF_;
  double NHF_;
  double shrinkConeCons_;
  double sigConeMaxOpen_;
  vector<TTTrack> isoTracks_;
  vector<EG> signalEGs_;
  vector<EG> isoEGs_;

  double GetTrackBasedPt();  
  double GetTotalPt();
  double GetTrackInvMass();
  double GetEGInvMass();
  double GetGenTauPt();

  double GetTrackBasedEt();
  double GetEGBasedEt(); 
  double GetTotalEt();
  double GetGenTauEt();  
  
 private:
  AuxTools auxTools;
  vector<TTTrack> theTracks;
  vector<EG> theEGs;
  float theSigCone_dRMin;
  float theSigCone_dRMax;
  float theIsoCone_dRMin;
  float theIsoCone_dRMax;
  GenParticle theGenTau;
  bool theMatching;
};

#endif
