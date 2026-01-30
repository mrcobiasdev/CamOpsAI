# Change: Reorganize Documentation and Create Final Project Report

## Why

The current documentation structure is scattered and lacks organization:
- `/docs` contains 9 flat markdown files with no clear categorization
- Multiple overlapping documents (e.g., multiple motion detection files, troubleshooting files)
- No clear separation between user guides, technical specs, and implementation notes
- README.md is a comprehensive technical guide but not formatted as an academic project report
- Openspec contains 12 archived proposals with no summary of what was implemented and why

To submit this project as a final course project (Disciplina de EII - Visão Computacional: Interpretando o Mundo Através de Imagens - Computer Vision Master), we need:
1. A coherent documentation structure following technical writing standards
2. A README.md formatted as a short article/technical report
3. A summary of archived proposals showing evolution and decisions made
4. Clear traceability of all changes and documentation

## What Changes

### Documentation Reorganization

Reorganize `/docs` into a hierarchical structure:
```
docs/
├── overview/              # Project overview and introduction
│   ├── project-overview.md (new - from README overview)
│   └── getting-started.md (new - from README setup sections)
├── architecture/          # System architecture and design
│   ├── system-architecture.md (new - from README architecture)
│   └── components.md (new - detailed component descriptions)
├── features/              # Feature-specific documentation
│   ├── motion-detection.md (move from docs/MOTION_DETECTION.md)
│   ├── whatsapp-notifications.md (consolidate WHATSAPP_SESSION_PERSISTENCE.md)
│   └── video-file-capture.md (new - from README video file section)
├── guides/                # User guides and tutorials
│   ├── troubleshooting.md (consolidate TROUBLESHOOTING.md + other fix docs)
│   └── calibration-guide.md (extract from MOTION_DETECTION.md tools section)
├── development/           # Developer documentation
│   ├── implementation-notes.md (consolidate implementation docs)
│   └── api-reference.md (from README API section)
└── appendix/              # Appendices and reference materials
    ├── changelog.md (move from docs/CHANGELOG.md)
    └── archived-proposals-summary.md (new - summary of openspec archives)
```

### README.md Transformation

Transform README.md into a formal technical report with sections:
1. Title, Abstract, Keywords (academic format)
2. Introduction/Context (problem statement, objectives)
3. Background/Related Work (brief context)
4. Methodology (tools used: OpenCode, OpenSpec, workflow)
5. System Architecture (overview, components, Mermaid diagram)
6. Implementation (key features, algorithms)
7. Results and Evaluation
8. Limitations and Future Work
9. Conclusions
10. References
11. Documentation Map (table of all docs)
12. Change Traceability (list of file moves and changes)

### Archive Proposal Summary

Create `docs/appendix/archived-proposals-summary.md` with table:
| Proposal ID | Date | Title | Status | Reason for Archive |
|-------------|------|-------|--------|-------------------|
| 2026-01-19-update-frame-interval-defaults | 2026-01-19 | Make FRAME_INTERVAL_SECONDS work as global default | Implemented | Feature completed and merged |
| 2026-01-20-fix-h264-decoding-errors | 2026-01-20 | Fix H.264 RTSP Stream Decoding Errors | Implemented | Error handling improved |
| ... | ... | ... | ... | ... |

### Consolidation Actions

- **Motion Detection docs**: Consolidate MOTION_DETECTION.md, MOTION_DETECTION_FIX.md, DIAGNOSTICO_MOTION_SCORE_ZERO.md, IMPLEMENTACAO_THRESHOLD_HOT_RELOAD.md into `docs/features/motion-detection.md`
- **WhatsApp docs**: Consolidate WHATSAPP_SESSION_PERSISTENCE.md into `docs/features/whatsapp-notifications.md`
- **Troubleshooting**: Consolidate TROUBLESHOOTING.md, BUG_FIX_FLUSH_VS_COMMIT.md, IMPLEMENTACAO_PERSISTENCIA.md into `docs/guides/troubleshooting.md`
- **Remove**: Files that are now fully integrated into the main documentation

## Impact

### Affected Specs

- **NEW SPEC**: `documentation` - documentation structure and standards (new spec)
- No existing specs modified (this is documentation-only change)

### Affected Code

- `/docs/*` - Move/rename/consolidate all documentation files
- `/README.md` - Transform into academic report format
- `openspec/changes/archive/*` - Read and summarize (no modifications)
- No source code changes

### Affected Workflows

- Documentation workflow becomes more structured
- Easier to find information by topic/audience
- Better support for academic submission requirements

## Risks and Mitigations

### Risk 1: Broken Links in Repository
- **Mitigation**: Update all internal markdown links after reorganization
- **Validation**: Use link checker or manual review

### Risk 2: Loss of Information During Consolidation
- **Mitigation**: Carefully review all content before consolidation, preserve all important information
- **Validation**: Compare original and consolidated documents

### Risk 3: README.md Becomes Too Long
- **Mitigation**: Keep concise sections, reference detailed docs for deep dives
- **Validation**: Ensure readability and academic formatting

## Success Criteria

1. All existing documentation is preserved or consolidated (no information loss)
2. New folder structure is logical and easy to navigate
3. README.md is formatted as a technical report suitable for academic submission
4. Archived proposals summary clearly shows project evolution
5. All internal links work correctly
6. Documentation map table is complete and accurate
7. Change traceability section lists all file moves and renames

## Out of Scope

- Writing new technical content (only reorganizing existing content)
- Updating source code comments or docstrings
- Modifying openspec specs (only reading/archived proposals for summary)
- Creating new features or functionality
- Testing actual system functionality (documentation-only change)
