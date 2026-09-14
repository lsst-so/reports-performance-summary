# RSO-63 — Site Seeing / DIMM study — handoff note

**Ticket:** RSO-63 — *Create Time Square notebook to support RINGSS, Tower DIMM and
Portable DIMM comparisons.*
**Goal:** one place to put analysis tools for understanding site seeing, comparing
RINGSS, the Tower DIMM and the Portable DIMM.

_Written 2026-09-14 to reconstruct where the work stood after a long pause._

---

## TL;DR — what I was doing

Building the site-seeing comparison tooling. The work is **split across two branches**
plus some uncommitted scratch. Nothing is lost, but it's scattered:

| Where | Notebook(s) | What it does | State |
|-------|-------------|--------------|-------|
| `tickets/SITCOM-2292` | `DIMMS_and_RINGGS_nightly_summary.ipynb` (+`.yaml`) | **The actual "Time Square notebook" the ticket asks for.** Queries `lsst.sal.DIMM.status`, uses DBSCAN clustering to find on-sky tracking, matches **shared targets** between Tower DIMM (`salIndex==1`) and Portable DIMM (`salIndex==2`). | Committed. RINGSS *not yet* integrated (title only). Has debug cruft in last commits. |
| `tickets/SITCOM-2292` | `dimm_single_night.ipynb` (+`.py`,`.yaml`) | Single-night DIMM target-reliability analysis. | Committed. |
| `tickets/RSO-63` (this branch) | `fwhm_vs_dimms_single_dayobs.ipynb`, `fwhm_vs_dimms_many_dayobs.ipynb` (+`.yaml`s) | Compare LSSTCam median **FWHM** against both DIMMs' seeing, single & many nights. | Committed. Last commit is WIP "splitting plots using wind threshold". |
| `tickets/RSO-63` working tree | `DualDimm.ipynb` (**untracked**) | Earliest scratch: DIMM1−DIMM2 FWHM difference vs wind speed/direction (quiver + polar plots). Precursor to the shared-target analysis. | Uncommitted, untracked. |
| `tickets/RSO-63` working tree | `wind_rose.py`, `wind_rose_bokeh.py` (**untracked**) | Wind-rose plotting helpers (matplotlib + bokeh) for ESS airflow data. | Uncommitted, untracked. |
| `tickets/RSO-63` working tree | `data/*.csv`, `*.png` | Cached DIMM EFD pulls (Oct/Nov 2025) + `shared_targets_*.csv` outputs + figures. | Untracked; `data/`+`plots/` are gitignored on the 2292 branch. |

There is also `stash@{0}: WIP on tickets/SITCOM-2292` — leftover WIP from that branch.

## Key facts to remember

- **DIMM identification:** `salIndex == 1` → **Tower DIMM**, `salIndex == 2` → **Portable DIMM**.
- **Wind/ESS:** `lsst.sal.ESS.airFlow`, `salIndex == 301`. Average wind *direction* via
  sin/cos components (do NOT `.mean()` degrees directly — 0/360° wraparound bug; the
  correct handling is already in `DualDimm.ipynb` cell 9).
- **`motionState` in `DIMM.status` was unreliable** at time of writing — that's *why* DBSCAN
  clustering is used to detect on-sky tracking. Revisit once `motionState` is trustworthy.
- **RINGSS is still TODO** — despite the notebook title, no RINGSS topic is queried yet.

## Immediate next steps (pick up here)

1. Decide the home for RSO-63: probably **consolidate** the 2292 `DIMMS_and_RINGGS_nightly_summary`
   notebook and the RSO-63 `fwhm_vs_dimms_*` notebooks onto one branch, since they're the same study.
2. Add the actual **RINGSS** data source and comparison (the missing third leg).
3. Clean the debug commits on 2292 (`drop!`, `fixup!`, "print CWD for debugging imports").
4. Fold the useful bits of `DualDimm.ipynb` / `wind_rose.py` into the summary notebook, then
   retire the scratch.

## Housekeeping done / to do before switching branches

Unrelated notebooks were left dirty in the RSO-63 working tree — **not part of this ticket**,
just re-executed outputs from other work (and one stray date edit). They should be discarded
so they don't follow a branch switch:

- `sst/calsys/Daily_CalSys-TimeSquare.ipynb`, `sst/calsys/Electrometer_Data_Viewer-TimeSquare.ipynb`
- `sst/mthexapod/mthexapod_faults_list.ipynb`, `sst/mtm1m3/hardpoint_breakaway_test.ipynb`
- `sst/mtmount/encoder_failures_vs_azel.ipynb` (stray `DAY_OBS_START=20260423` edit)

`create_dot_env.py` (top level, untracked) is a generic VS Code env helper — unrelated to RSO-63.
