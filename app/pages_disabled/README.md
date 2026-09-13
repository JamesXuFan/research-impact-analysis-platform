Pages here are temporarily withdrawn from the platform, not deleted.

Streamlit's classic multipage mode (`streamlit/runtime/scriptrunner/script_runner.py`,
`_mpa_v1`) auto-generates the sidebar from every `*.py` file directly inside
`app/pages/` — there's no per-file "hidden" flag, and a leading underscore on the
filename does **not** exclude it (only a leading `.` does). Moving a file out of
`app/pages/` into this folder is the only reliable way to keep it out of the
sidebar/URL routing while keeping the code in the repo.

To bring a page back: `git mv app/pages_disabled/<file>.py app/pages/<file>.py`.

Currently withdrawn:

- `5_Impact_Drivers.py` (README item 14)
- `6_Scenario_Analysis.py` (README item 17)
