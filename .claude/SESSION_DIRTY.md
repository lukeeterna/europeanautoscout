# SESSION DIRTY — chiusura senza commit auto

Sessione: `15471767-64d2-476d-8165-041d1bf8a936`  Timestamp: `2026-06-13T11:31:52Z`

Motivo: `git diff --check` fail (whitespace errors o conflict markers).

## Output git diff --check
```
tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf:45: trailing whitespace.
+/Author (\(anonymous\)) /CreationDate (D:20260612171355+02'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260612171355+02'00') /Producer (ReportLab PDF Library - \(opensource\)) 
tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf:45: trailing whitespace.
+/Author (\(anonymous\)) /CreationDate (D:20260612171355+02'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260612171355+02'00') /Producer (ReportLab PDF Library - \(opensource\)) 
```

## Status
```
 M .claude/NEXT_SESSION_PROMPT.md
 M STATE.md
 M state/rings.json
 M tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf
 M tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf
 M tools/scrapers/autoscout_scraper.py
 M tools/scripts/build_it_fixture.py
 M vos-out/decisions.jsonl
?? .claude/REPORT_S273_cont.txt
?? .claude/SESSION_DIRTY.md
```

Risolvi manualmente, poi commit. Sessione successiva legge questo file.
