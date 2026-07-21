# Public Waste Dataset Research Plan

## Main Question

Find public waste / trash / recycling datasets that can be legally and practically combined with the customer RB field images to train a stronger YOLO model for the waste-vision demo.

## Subtopics

1. Detection and segmentation datasets
   - Need images with bounding boxes or masks that can be converted to YOLO detection or segmentation format.
   - Check license, dataset size, label taxonomy, and whether the visual domain resembles bins, litter, overflow, or waste scenes.

2. Classification datasets
   - Need image-level labels that can expand the current YOLO classification prototype.
   - Check whether labels can map into overflow, litter, dirty, normal, or broader waste categories.

3. Practical integration path
   - Decide which datasets should be downloaded now, which should only be referenced, and which are unsuitable.
   - Define how public data should be mixed with customer images without leaking customer data or confusing labels.

## Synthesis

Create a short recommendation with source URLs, license notes, YOLO suitability, and a concrete training-data plan for the current repo.
