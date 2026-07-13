# Waste Vision Demo Design Brief

## Audience

DenseMatrix team members, potential industry partners, and technical evaluators who need to see whether image-based waste recognition can become a working demo quickly.

## Primary Workflow

Upload or use a sample image, choose a model provider, run detection, inspect bounding boxes, review category/confidence evidence, and copy the unified JSON contract for backend adapter work.

## Information Hierarchy

1. Image workspace with bounding boxes.
2. Detection controls and category legend.
3. Object cards with confidence, category, rationale, and coordinates.
4. Raw JSON output for engineering validation.

## Visual Direction

Operational, precise, and technical. The UI should feel like an inspection console, not a marketing page.

## Density

Moderately dense desktop layout with a three-column work surface. Mobile stacks controls, image, and results in order.

## Constraints

Static HTML demo, Docker-served, no external assets or build step. Current detector is a mock adapter that preserves the target schema and overlay behavior.
