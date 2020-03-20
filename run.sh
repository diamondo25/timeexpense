#!/bin/bash

LOGFILE=exec_log.log
echo '!-!-!-!-!' >> $LOGFILE
date >> $LOGFILE
echo 'RUNNING With arguments: ' "$*" >> $LOGFILE
./prp run.py --rabo-csv input/rabobank-bymonth-*.csv --pm-csv input/parkmobile-clean.csv --ov-csv input/transacties_*.csv $* | tee -a $LOGFILE
echo 'RAN With arguments: ' "$*" >> $LOGFILE
echo -n '!! Last run ' >> $LOGFILE
date >> $LOGFILE
echo '!-!-!-!-!' >> $LOGFILE
