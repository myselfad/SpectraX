# Decision Log

## Decision 1: Sentinel-2 Focus
**Decision:** Focus prototype scope on Sentinel-2 imagery.  
**Reason:** Clear multispectral satellite use case and accessible Earth-observation workflow.  
**Status:** Project direction.

## Decision 2: RGB + NIR
**Decision:** Focus on four bands: Blue, Green, Red and NIR.  
**Reason:** Preserve multispectral information while keeping the prototype manageable.  
**Status:** Intended prototype scope.

## Decision 3: Reliability-Aware Output
**Decision:** Do not treat SR as only image sharpening.  
**Reason:** Generated detail can be visually plausible without being equally trustworthy.  
**Status:** Core project differentiator.

## Decision 4: Patch-Based Processing
**Decision:** Use tiling/patching for large scenes.  
**Reason:** Manage memory and make large imagery processing feasible.  
**Status:** Intended architecture.

## Decision 5: MC-Dropout Research Direction
**Decision:** Use MC-Dropout as the intended uncertainty method.  
**Reason:** Generate stochastic predictions without requiring expensive deep ensembles.  
**Status:** Intended; actual implementation requires verification.

## Decision 6: Observation Consistency
**Decision:** Compare degraded SR output with the original observation where implemented.  
**Reason:** Add reconstruction consistency evidence.  
**Status:** Intended validation strategy.
