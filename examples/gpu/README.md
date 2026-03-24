# Optional GPU Extension Point

This template keeps GPU or Jetson-specific bootstrap logic out of the default install path.

If a real project needs CUDA, TensorRT, Jetson, or vendor-specific wheel setup, add those steps here or in dedicated project scripts and document them separately from the default `pip install -e .[dev]` workflow.
