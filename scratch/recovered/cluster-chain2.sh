#!/bin/bash
R=$HOME/workspace/photodiode-lvds-rx
D=$HOME/workspace/pdlvds-v6run
cd $R
bash $D/run-cluster.sh u4b  hw/pdlvds_rx.fr22.kicad_pcb hw/pdlvds_rx.fr24.kicad_pcb 52 52 4.2 KEEP_NONE +3V3D_CDR:U4.24 CDR_CLKN:U4.25 CDR_LOL:U4.16 CDR_PIN:U4.5 CDR_SQUELCH:U4.27 I2C_SCL:U4.20 THRADJ:U4.9 CDR_DATP:U4.29 CDR_NIN:U4.4
bash $D/run-cluster.sh u7b  hw/pdlvds_rx.fr24.kicad_pcb hw/pdlvds_rx.fr25.kicad_pcb 30 61 4.5 KEEP_NONE +3V3A:U7.16,U7.25 DP_PHY:U7.7 ULPI_D5:U7.19 ULPI_NXT:U7.11 ULPI_STP:U7.13 XI:U7.28
bash $D/run-cluster.sh u10b hw/pdlvds_rx.fr25.kicad_pcb hw/pdlvds_rx.fr26.kicad_pcb 16 10 3.6 KEEP_NONE HV_INTVCC:U10.8 HV_SS:U10.3
bash $D/run-cluster.sh u6b  hw/pdlvds_rx.fr26.kicad_pcb hw/pdlvds_rx.fr27.kicad_pcb 83 44 3.5 KEEP_NONE USB_RST:U6.40
bash $D/run-cluster.sh u13b hw/pdlvds_rx.fr27.kicad_pcb hw/pdlvds_rx.fr28.kicad_pcb 48 62 3.6 KEEP_NONE ILIM_P:U13.5
echo "CHAIN2 DONE $(date -u +%H:%M:%S)" >> $R/results/cluster-chain2.log
