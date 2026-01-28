# Add Frame Annotation Proposal

## Summary
Add frame visualization/annotation capabilities to assist in human auditing of detection events. The system will generate annotated versions of captured frames that overlay motion detection visualization and LLM analysis results.

## Motivation
Currently, the CamOpsAI system captures frames, detects motion, and analyzes them with LLMs, but there is no visual way to audit and verify detection events. Human operators cannot easily see:
- What motion was detected in the frame
- Which areas triggered the motion detection
- What the LLM found in the image
- The confidence levels of both detection and analysis

Adding annotated frames will:
- Improve transparency and trust in the detection system
- Enable faster auditing of events
- Help troubleshoot false positives/negatives
- Provide visual documentation for incident review

## Scope
This change adds frame annotation capabilities that:
1. Generate annotated versions of all processed frames
2. Overlay motion detection information:
   - Motion score and threshold
   - Motion mask showing detected areas
   - Motion status indicator
3. Overlay LLM analysis results:
   - Detected keywords
   - Confidence score
   - Provider and model information
4. Store annotated frames as separate files (e.g., `cameraid_timestamp_annotated.jpg`)
5. Add configuration to enable/disable annotation
6. Provide API endpoint to retrieve annotated frames

## Out of Scope
- Real-time annotation display in UI (this is a separate frontend feature)
- Annotation of filtered frames (frames that don't pass motion detection)
- Video annotation (only still frames)
- Advanced visualization like bounding boxes or object detection (unless LLM provides coordinates)

## Success Criteria
- All processed frames have an annotated version generated
- Annotated frames include all motion detection and LLM information as specified
- Annotation does not significantly impact processing performance (<100ms overhead per frame)
- Configuration allows enabling/disabling annotation
- Annotated frames are retrievable via API
- Storage is managed (cleanup of old annotated frames)

## Risks & Mitigations
| Risk | Impact | Likelihood | Mitigation |
|------|--------|------------|------------|
| Increased storage usage | High | High | Implement automatic cleanup of old annotated frames, add configuration for retention period |
| Performance degradation | Medium | Medium | Benchmark annotation overhead, add warning if annotation takes >100ms |
| Disk I/O bottleneck | Medium | Medium | Async saving of annotated frames, queue-based storage |
| Annotations obscure important details | Low | Low | Use semi-transparent overlays and careful placement, provide original frame alongside |

## Alternatives Considered
1. **Store annotation data separately**: Keep original frames and store annotation metadata in database
   - *Rejected*: Requires frontend to reconstruct annotations, adds complexity

2. **On-demand annotation**: Generate annotations only when requested via API
   - *Rejected*: Would add latency to event review, not proactive

3. **Browser-side annotation**: Send annotation data to frontend and render there
   - *Rejected*: Not applicable yet (no frontend), adds network overhead

## Dependencies
- Existing motion detection infrastructure (MotionDetector)
- Existing LLM analysis infrastructure (LLMVisionFactory)
- Existing frame storage (settings.frames_storage_path)
- OpenCV for image manipulation

## Open Questions
1. What retention policy for annotated frames? (TBD - will use same as original frames for now)
2. Should annotated frames be compressed differently? (TBD - will use same quality as originals)
3. Should there be a maximum number of annotated frames per camera? (TBD - will implement disk-based cleanup)
