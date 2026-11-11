# USB VID/PID — registration path (researched 2026-11-10)

The firmware enumerates as VID **0x1209** / PID **0xD723**
(`firmware/src/usb_descriptors_data.h`). 0x1209 is the community VID
administered by **pid.codes** for open-source hardware; PIDs under it
are real assignments, not squatting space. Until an assignment is
granted, this pair is an **unregistered placeholder**: fine on the
bench, not to be distributed on hardware given to anyone else.

## Status of D723

Checked 2026-11-10 against both the pid.codes site and its registry
repository: **0xD723 is not assigned to anyone** (no page at
pid.codes/1209/D723/, no entry in the 1209 table, no 1209/D723
directory in the registry). It also sits outside both reserved
ranges (0x0000–0x0FFF, common/testing; 0x1000–0x1FFF, InterBiometrics),
so it is an ordinary requestable PID. Nothing needs to change in the
firmware if the request is granted as-is.

## The request, step by step

There is no web form and no fee. Registration is a GitHub pull
request to **github.com/pidcodes/pidcodes.github.com** (the registry
repo the pid.codes site links to):

1. **Organisation**: the requester registers an organisation (a
   project or GitHub identity) — either inside the same PR or by
   emailing pid-admin@pid.codes. The org must be the device's own
   project; one org per device.
2. **File**: in a fork, on a branch, create `1209/D723/index.md`:

   ```
   ---
   layout: pid
   title: PDLVDS-RX photodiode LVDS receiver
   owner: <assigned org identifier>
   license: <the repo's open-source license>
   site: https://github.com/sneakers-the-rat/lvds-receiver-official
   source: https://github.com/sneakers-the-rat/lvds-receiver-official
   ---

   USB-CDC programming, control and verification interface for the
   PDLVDS-RX, an open-source photodiode (APD) receiver board that
   replaces the FPGA-based optical receiver of the Miniscope Zero:
   STM32H723 + USB3300 ULPI PHY, TinyUSB CDC ACM.
   ```

3. **Open the PR.** A maintainer reviews; on acceptance the device
   appears at pid.codes/1209/D723 and the placeholder becomes a real
   assignment. No firmware change is needed at that point — the
   descriptors already carry the requested pair.

## The one open prerequisite

Eligibility requires the design files and/or firmware to be
published under a **recognised open-source license**, and projects
using VID 1209 must be so licensed. This repository currently
declares **no license at all** (no LICENSE file; checked
2026-11-10). Choosing one is the project owner's decision — common
fits for a mixed hardware/firmware repo are CERN-OHL-S for the
hardware with MIT or GPL for the firmware, but the choice is not
this document's to make. Once a license is in the repo, the PR above
is a ten-minute filing.

## Interim rule

Until the assignment lands: bench and development use only. The
reserved testing PIDs are for private in-house testing and must not
ship on redistributed devices either, so there is no interim pair
that makes redistribution clean — register first, then distribute.
