#!/bin/bash
echo "Processing 2024"
export PYTHONNOUSERSITE=1
python3 UNBLINDEDcombo_SR_SB_alsoChannelSplit_allSys_May5.py --histogram_path /afs/hep.wisc.edu/home/mithakor/HH_bb_tautau_Analysis/StatisticalAnalysis/CMSSW_16_0_0/src/CombineHarvester/CombineTools/python/Rootfiles_Maker_for_Datacards/2024 --year 2024 --parent_dir 2024 &> processing_2024.log &

# echo "Now for the full Run2 Combination"
# ulimit -s unlimited
# python3 UNBLINDEDcombineAndrunLimitsForRun2.py

# echo "Now for the full 2016 Combination"
# ulimit -s unlimited
# python3 UNBLINDEDcombineAndrunLimitsForFull2016.py