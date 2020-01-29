#!/bin/bash
LOGFILE=exec_log.log
echo '!-!-!-!-!' >> $LOGFILE
date >> $LOGFILE
echo 'RUNNING With arguments: ' "$*" >> $LOGFILE
python run.py --ov-csv /Users/erwinoegema/Downloads/transacties_*.csv $* | tee -a $LOGFILE
echo 'RAN With arguments: ' "$*" >> $LOGFILE
echo -n '!! Last run ' >> $LOGFILE
date >> $LOGFILE
echo '!-!-!-!-!' >> $LOGFILE
