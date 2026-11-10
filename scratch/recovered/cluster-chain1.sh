#!/bin/bash
D=$HOME/workspace/pdlvds-v6run
bash $D/run-cluster.sh u4  hw/pdlvds_rx.fr5.kicad_pcb hw/pdlvds_rx.fr6.kicad_pcb  52 52 4.2 KEEP_NONE +3V3D_CDR:U4.12,U4.18 CDR_CLKP:U4.26 CDR_DATN:U4.28 CDR_LOS:U4.22 CDR_NIN:U4.4 CDR_VREF:U4.3 REFCLK:U4.10
bash $D/run-cluster.sh u13 hw/pdlvds_rx.fr6.kicad_pcb hw/pdlvds_rx.fr7.kicad_pcb  48 62 3.6 KEEP_NONE +5V:U13.1,U13.3 +VA:U13.9,U13.10 SET_P:U13.7
bash $D/run-cluster.sh u7f hw/pdlvds_rx.fr7.kicad_pcb hw/pdlvds_rx.fr8.kicad_pcb  30 61 4.5 KEEP_NONE PHY_1V8:U7.26,U7.15 PHY_1V8A:U7.29 ULPI_D0:U7.24 ULPI_D2:U7.22 ULPI_D3:U7.21 ULPI_D4:U7.20 ULPI_D6:U7.18 ULPI_DIR:U7.12 USB_RST:U7.9 XI:U7.28 XO:U7.27 RBIAS:U7.32 +3V3A:U7.25,U7.30,U7.31
bash $D/run-cluster.sh u10 hw/pdlvds_rx.fr8.kicad_pcb hw/pdlvds_rx.fr9.kicad_pcb  16 10 3.6 KEEP_NONE HV_FBX:U10.2 HV_GATE:U10.7 HV_SHDN:U10.9
bash $D/run-cluster.sh u9  hw/pdlvds_rx.fr9.kicad_pcb hw/pdlvds_rx.fr10.kicad_pcb 8 48 3.4 KEEP_NONE +3V3A:U9.5 I2C_SCL:U9.1 I2C_SDA:U9.6 TMP_ALERT:U9.3
echo "CHAIN1 DONE $(date -u +%H:%M:%S)" >> $HOME/workspace/photodiode-lvds-rx/results/cluster-chain1.log
