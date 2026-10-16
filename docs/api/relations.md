# `dsp_props.relations`

One class per relation. `verify` runs, for a declaration, every relation of the
matching list (`TRANSFORM_RELATIONS`, `LTI_RELATIONS`, `MULTIRATE_RELATIONS`,
`STREAMING_RELATIONS`) whose `applies(spec)` returns true. Every class below is
also importable from `dsp_props.relations`.

::: dsp_props.relations.base

::: dsp_props.relations.transforms

::: dsp_props.relations.lti

::: dsp_props.relations.multirate

::: dsp_props.relations.streaming
