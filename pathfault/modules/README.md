# Modules Overview

The `modules/` directory organizes the implementation of PathFault into two major parts: core modules and utility modules.  
Each module is designed to ensure modularity, clarity, and ease of experimentation.

## Core Modules

The core modules implement the primary functionalities of PathFault, which are essential for reproducing the main results described in the paper.  
These modules form the foundation of the system's detection and exploitation capabilities.

- **Exploit Payload Generator**  
  Generates exploit payloads based on identified path parsing inconsistencies.

- **Inconsistency Detector**  
  Detects discrepancies in how different web application components interpret input paths.

- **Surrogate Model Generator**  
  Constructs surrogate models to simulate the behavior of real-world web components, facilitating efficient vulnerability analysis.

All core modules are mandatory for validating the claims made in the paper.

## Utility Modules

The utility modules provide supportive tools that facilitate experimentation and setup but are not critical to the core detection and exploitation logic.  
They are designed to assist users in preparing realistic evaluation environments and preprocessing inputs.

- **Mimic Environment Creator**  
  Assists in constructing mimic environments that replicate web infrastructure setups, simplifying experimental validation.

Utility modules are optional but highly recommended to streamline experimental workflows and extend the system's applicability.

## Summary

- **Core modules** are essential for reproducing PathFault’s primary contributions.
- **Utility modules** enhance usability and experimentation but do not modify core logic.

All modules are organized for easy extension, supporting both quick validation and broader experimental exploration.

Additional utility modules may be introduced in the future to support broader experimental use cases.