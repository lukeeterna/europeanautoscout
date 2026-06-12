# SESSION DIRTY — chiusura senza commit auto

Sessione: `292be5af-85e2-44af-9749-4f583e11672e`  Timestamp: `2026-06-12T14:33:16Z`

Motivo: `git diff --check` fail (whitespace errors o conflict markers).

## Output git diff --check
```
tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf:45: trailing whitespace.
+/Author (\(anonymous\)) /CreationDate (D:20260612161844+02'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260612161844+02'00') /Producer (ReportLab PDF Library - \(opensource\)) 
tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf:80: trailing whitespace.
+0000004449 00000 n 
tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf:45: trailing whitespace.
+/Author (\(anonymous\)) /CreationDate (D:20260612161844+02'00') /Creator (\(unspecified\)) /Keywords () /ModDate (D:20260612161844+02'00') /Producer (ReportLab PDF Library - \(opensource\)) 
tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf:80: trailing whitespace.
+0000004381 00000 n 
```

## Status
```
 M .claude/NEXT_SESSION_PROMPT.manual.md
 M .claude/NEXT_SESSION_PROMPT.md
 M STATE.md
 M state/rings.json
 M tests/dossiers_s268/ARGOS_DEMO_S268_320d_xDrive.pdf
 M tests/dossiers_s268/ARGOS_DEMO_S268_330i.pdf
 M tools/scripts/build_s268_dossier.py
 M tools/scripts/pdf_generator_enterprise.py
?? .claude/REPORT_S269.txt
?? .claude/REPORT_S270.txt
?? .claude/SESSION_DIRTY.md
```

Risolvi manualmente, poi commit. Sessione successiva legge questo file.
