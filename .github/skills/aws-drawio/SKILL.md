---
name: aws-drawio
description: Create or update accurate AWS architecture and network diagrams as editable draw.io files. Use for AWS services, VPCs, subnets, Availability Zones, traffic flows, or diagrams that must export to SVG.
---

# AWS draw.io diagrams

Create native, editable `.drawio` diagrams for AWS architectures. Treat the
repository's requirements as the source of truth; never invent components,
network paths, ports, or high-availability topology to make a diagram look
more complete.

Read `docs/diagrams/AGENTS.md` before editing a diagram. Its repository rules
override this Skill where they conflict.

## Workflow

1. Read the architecture input and list boundaries, resources, and directional
   flows before producing XML.
2. Find every AWS icon using the AWS4 draw.io library. Use the official draw.io
   shape search when available; do not guess stencil names.
3. Build boundaries first, then resources, then directional connectors.
4. Use an orthogonal connector and an explicit arrowhead. Label each required
   network flow with its protocol and port.
5. Save uncompressed draw.io XML and export the companion SVG with draw.io
   Desktop. Do not hand-edit the SVG.
6. Inspect the rendered export. Repair any empty icon, overlapping text,
   ambiguous arrow, clipped label, or line crossing an unrelated icon.

## AWS4 icon rules

- Prefer the AWS4 `resourceIcon` pattern for service-level icons:
  `shape=mxgraph.aws4.resourceIcon;resIcon=mxgraph.aws4.<verified-name>`.
- Use an AWS service color as `fillColor` and `strokeColor=#ffffff` for a
  service-level icon.
- Use standalone AWS4 shapes only where they are the verified representation
  for the resource, such as Application Load Balancer.
- A blank coloured square means the stencil name is invalid. Look it up and
  regenerate; never keep a blank icon as a placeholder.

## Quality gates

Before completing the task, verify all of the following:

- The `.drawio` file parses and opens in draw.io.
- Every connector has both a source and a target.
- Every requested resource and flow is present exactly once unless a deliberate
  repeated visual representation is explicitly required.
- The rendered SVG matches the `.drawio` file and is readable at normal scale.

## Reference sources

- Use the AWS Architecture Icons for AWS icon meaning and current branding:
  https://aws.amazon.com/architecture/icons/
- Use the official draw.io plugin/MCP for XML guidance and exact shape search:
  https://github.com/jgraph/drawio-mcp
- For a wider verified AWS4 stencil catalogue, consult:
  https://github.com/vidanov/aws-architecture-diagram-skill
