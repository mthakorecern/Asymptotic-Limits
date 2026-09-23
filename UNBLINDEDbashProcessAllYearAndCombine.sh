#!/bin/bash
echo "Processing 2016APV"
python3 UNBLINDEDcombo_SR_SB_alsoChannelSplit_allSys_May5.py --histogram_path /afs/hep.wisc.edu/user/parida/public/HHbbtt_Analysis_Scripts/StatisticalToolsCombine/CMSSW_11_3_4/src/CombineHarvester/CombineTools/python/FinalizingResultsForPreApp_HHbbttDataCardMaker/2016APV/Oct1_2025_preCWR --year 2016APV --parent_dir 2016APV_unblinded_Oct1_2025_preCWR
echo "Processing 2016"
python3 UNBLINDEDcombo_SR_SB_alsoChannelSplit_allSys_May5.py --histogram_path /afs/hep.wisc.edu/user/parida/public/HHbbtt_Analysis_Scripts/StatisticalToolsCombine/CMSSW_11_3_4/src/CombineHarvester/CombineTools/python/FinalizingResultsForPreApp_HHbbttDataCardMaker/2016/Oct1_2025_preCWR --year 2016 --parent_dir 2016_unblinded_Oct1_2025_preCWR
echo "Processing 2017"
python3 UNBLINDEDcombo_SR_SB_alsoChannelSplit_allSys_May5.py --histogram_path /afs/hep.wisc.edu/user/parida/public/HHbbtt_Analysis_Scripts/StatisticalToolsCombine/CMSSW_11_3_4/src/CombineHarvester/CombineTools/python/FinalizingResultsForPreApp_HHbbttDataCardMaker/2017/Oct1_2025_preCWR --year 2017 --parent_dir 2017_unblinded_Oct1_2025_preCWR
echo "Processing 2018"
python3 UNBLINDEDcombo_SR_SB_alsoChannelSplit_allSys_May5.py --histogram_path /afs/hep.wisc.edu/user/parida/public/HHbbtt_Analysis_Scripts/StatisticalToolsCombine/CMSSW_11_3_4/src/CombineHarvester/CombineTools/python/FinalizingResultsForPreApp_HHbbttDataCardMaker/2018/Oct1_2025_preCWR --year 2018 --parent_dir 2018_unblinded_Oct1_2025_preCWR

echo "Now for the full Run2 Combination"
ulimit -s unlimited
python3 UNBLINDEDcombineAndrunLimitsForRun2.py

echo "Now for the full 2016 Combination"
ulimit -s unlimited
python3 UNBLINDEDcombineAndrunLimitsForFull2016.py