# 📚 Case Study Reproducibility Guide

This document is intended to help reviewers and researchers **reproduce the case studies** presented in our paper using the provided artifact.  
We have carefully automated most steps to make the reproduction process as seamless as possible, without compromising transparency or flexibility.

> ⚠️ **Important Note**: While this guide allows for convenient end-to-end execution of each case study, we strongly encourage readers to first consult the [main tool usage guide](../README.md) to understand how PathFault works internally.  
> The case study scripts are primarily designed for reproduction purposes and may abstract away some internal logic for brevity.

---

## ⚙️ Requirements

The case studies were evaluated on the following hardware and software configuration:

- **CPU**: 11th Gen Intel(R) Core(TM) i5-11600K @ 3.90GHz  
- **Memory**: 16GB RAM  
- **Operating System**: Ubuntu 20.04.6 LTS

> 📝 These specifications reflect the official evaluation environment used in the paper.  
> However, **PathFault is fully portable** and can be run on any platform that supports Docker and Python 3.12+, including macOS and other Linux distributions.

For setup instructions, please refer to the [main README](../README.md#Requirements), which covers:

- Installing Docker and Docker Compose  
- Creating a Python virtual environment  
- Installing dependencies from `requirements.txt`

---

## 🧪 Case Studies

All case studies are organized in increasing order of complexity.  
We recommend following them in sequence for the smoothest experience:

- **Case Study 1**: [Authentication Bypass: CVE-2025-0108](./authentication_bypass_cve-2025-0108/README.md)  
  Explores how PathFault discovers and exploits a real-world authentication bypass vulnerability.

- **Case Study 2**: [Web Cache Deception: ChatGPT Account Takeover](./chatgpt_account_takeover/README.md)  
  Demonstrates how inconsistencies in cache handling enable unauthorized access to sensitive content.

- **Case Study 3**: [Enhancing Heuristic Payloads from Prior Work](./enhancing_heuristic_from_prior_work/README.md)  
  Re-evaluates legacy heuristic payloads with PathFault, showing how deeper modeling improves exploit precision.

- **Case Study 4**: [Arbitrary Web Cache Deception in CDN Configurations](./arbitrary_wcd_in_cdn_configuration_guide/README.md)  
  Applies PathFault to discover the arbitrary web cache deception and analyze a vulnerable CDN misconfiguration.

Each case directory includes its own README with step-by-step instructions, execution scripts, and expected outputs.  
If you encounter any issues, please ensure your environment matches the [listed requirements](../README.md#️-requirements).

---

We hope this guide facilitates straightforward validation of our results and encourages further exploration based on our methodology.