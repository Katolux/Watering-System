# GardenHub Planner Object Library

This document is the working backlog for **non-plant objects in the GardenHub Planner**. It defines the object families the Planner should eventually support, the main variants worth creating, and a few visual rules that should stay consistent as the library grows.

It is primarily an asset and Planner catalogue reference. Some object families, especially irrigation, will later connect to deeper backend logic, but that behaviour is outside the scope of this file.

## Visual direction

Planner objects should be clean, credible and easy to read from above. They do not need the same level of realism as the botanical plant artwork, but they should sit comfortably beside it and avoid the flat, cartoon-like look of some of the early prototype assets.

The main priorities are:

- top-down readability;
- scalable SVG artwork;
- consistent line weight, perspective and shading within each object family;
- enough detail to make materials and object types recognisable;
- clarity over photorealism.

Objects should support the Planner rather than compete with plants, labels, spacing information or measurements.

### Raised beds

Raised-bed interiors should stay visually open or shallow. Heavy soil textures or dark fills make planted content harder to read, so the frame should carry most of the visual identity.

## Asset behaviour

Each family should use whichever sizing model makes sense for the real object:

- fixed standard sizes;
- several predefined sizes;
- a scalable base object;
- or a combination of fixed and scalable variants.

Where possible, one reusable scalable family is preferable to many near-identical one-off assets.

Each object should eventually have enough metadata to describe:

- name;
- category;
- variant;
- material;
- size behaviour;
- Planner role;
- visual notes;
- interaction notes where relevant.

Planner roles currently include objects, structures, boundaries, surfaces, overlays and irrigation components.

# Object families

## Hanging and plant supports

### Hanging baskets
- hanging basket;
- wall-mounted basket.

They should clearly read as plant containers even at small Planner sizes.

### Bamboo supports
- individual bamboo canes;
- grouped bamboo support;
- small, medium and tall variants where useful.

### General supports
- obelisk;
- arch;
- pergola-style plant support.

These are intended for climbing plants rather than as full landscape structures.

## Animal and wildlife infrastructure

### Beehives
- classic wooden hive;
- one or more modern hive variants;
- optional size variations.

### Chicken infrastructure
- wooden coop;
- plastic coop;
- small, medium and large versions;
- ramp and no-ramp variants where useful;
- feeder;
- drinker;
- chicken run.

A representative set is enough initially; this does not need to become a specialist poultry-planning library.

## Protected growing and season extension

### Cold frames
Should be visually distinct from both greenhouses and polytunnels.

### Raised-bed covers
A small protective structure placed directly over a raised bed.

### Plant houses
Smaller or more localised protection than a full greenhouse.

### Greenhouses
- four or five common fixed sizes;
- one scalable version.

### Polytunnels
- several common sizes;
- one scalable version.

### Heated polytunnels
Should be visually distinguishable from the standard version without becoming overly detailed.

## Compost, waste and leaf mould

### Compost
- tumbler;
- open compost heap;
- square wooden bin;
- round black bin;
- round green bin.

### Leaf mould
- square leaf-mould bin;
- round leaf-mould bin.

### Stands and supports
A general bin stand/support can be added if it proves useful in real layouts.

## Containers and planters

### Round pots
A small material/colour range is enough:
- terracotta;
- green;
- dark/black;
- grey/stone.

### Square containers
A few representative shapes and materials.

### Grow bags
One or two recognisable forms.

### Fabric pots / planter bags
Should remain visually distinct from rigid containers.

### Potato planters
A representative purpose-built potato planter.

### Potato sacks
A sack-style growing container.

### Stepped planters
The different planting levels should still be understandable in a top-down view.

### Tower planters
Useful for vertical-growing layouts.

### Reservoir / self-watering containers
Should be identifiable as a reservoir-based container where possible without needing explanatory decoration.

## Raised beds

Core material families:
- brick;
- wood;
- metal;
- plastic;
- wicker;
- simple/basic raised bed.

Later variants can include:
- corner beds;
- different frame thicknesses;
- longer or deeper proportions.

The open-interior rule applies to every raised-bed asset.

## Boundaries, edging and fences

### Edging
- brick edging.

### Fences
- wooden fence;
- concrete fence;
- wood-panel fence;
- picket fence;
- stone or gabion-style fence.

Boundary materials have a large effect on how a garden looks, so these should be visually distinct without becoming too heavy.

## Paths and surfaces

Material families:
- stone, with several stone/colour variants;
- asphalt;
- brick, with a few representative brick patterns;
- paving;
- gravel;
- pebble;
- wood or wood-chip.

These may work as path assets, scalable surfaces or material fills depending on the Planner implementation. The material should remain recognisable at normal zoom.

## Water and rain collection

### Ponds
- square;
- rectangular;
- octagonal;
- natural/organic shape.

### Rainwater collection
- water butt / rain barrel;
- larger tank or rain collector.

Rain collection will later be useful to irrigation planning, so these objects should be suitable for linking into that system rather than remaining purely decorative.

## Sheds and utility structures

### Sheds
- metal;
- wooden;
- painted;
- several common fixed sizes;
- one scalable version.

### Garden trugs
One clear representative garden trug is probably enough initially.

## Netting and protection

Netting is better treated as an overlay or coverage area than as a solid object.

The first version only needs to let a user mark an area as protected. More detailed protection behaviour can come later.

## Irrigation

Irrigation is a separate, system-oriented Planner family.

The visible catalogue is expected to include:

### Tubing
- standard supply tubing;
- drip line variants.

### Connectors and junctions
- connector/barb fittings;
- couplers;
- elbows;
- T-junctions;
- starters;
- end caps;
- repair plugs.

### Water-delivery components
- emitters;
- hose feeders;
- pressure regulators;
- filters where required.

### Sources and controls
- tap / water connection;
- valves;
- timer/controller markers later.

These objects will eventually carry real planning information rather than acting as decorative symbols. Pipe length, type and diameter will matter for hydraulic calculations and material planning, while junctions, valves and other components will form part of the connected irrigation network.

The hydraulic model, bucket-test input, pressure/flow calculations, friction loss, zones and shopping calculations belong to the wider irrigation feature and should be specified separately when that work begins.

# Priority

The library should grow in small batches rather than being produced all at once.

## First priority

These cover the largest share of normal gardens:

1. Raised beds
2. Containers and planters
3. Paths and surfaces
4. Fence and boundary variants
5. Greenhouses, polytunnels and cold frames

## Second priority

6. Rainwater collection
7. Compost and leaf-mould bins
8. Obelisks, arches and bamboo supports
9. Grow bags, fabric pots, potato containers, stepped planters and tower planters

## Third priority

10. Chicken infrastructure
11. Beehives
12. Ponds
13. Sheds
14. Hanging baskets
15. Garden trugs
16. Plant houses and other specialist protection structures

## Separate system passes

17. Irrigation
18. Netting and protection overlays

# Production approach

New object families should be built and reviewed in small groups. A useful order for the first visual pass is:

1. raised beds;
2. containers and planters;
3. paths and surfaces;
4. fences and boundaries;
5. greenhouses, polytunnels and cold frames.

Before expanding the catalogue substantially, the Planner should also move toward a single object-definition/metadata source so that size, layer, variant and renderer information do not have to be maintained independently in several places.

The object library can then expand gradually as the rest of the Planner develops. The aim is not to have every possible garden object, but to cover the things people actually need while keeping the Planner clear and visually coherent.
