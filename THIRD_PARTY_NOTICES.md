# Third-Party Notices

Camera Trap Assistant combines project-owned code with third-party software,
model weights, data services, and trademarks. Each component remains subject
to its own license. This file is an attribution and release-audit record, not
legal advice and not a replacement for the applicable license texts.

## Project and DeepFaune source code

Project-original source code is copyright (c) 2025-2026 Noe Bernigaud and is
distributed under the CeCILL Free Software License Agreement v2.1. See
`LICENSE`.

The files below are derived from the CNRS DeepFaune project and retain their
upstream copyright and CeCILL notices:

- `CameraTrapAssistant/src/models/classifTools.py`
- `CameraTrapAssistant/src/models/detectTools.py`
- `CameraTrapAssistant/src/models/fileManager.py`
- `CameraTrapAssistant/src/models/predictTools.py`

DeepFaune is a CNRS project by Simon Chamaille-Jammes and Vincent Miele:
https://deepfaune.pages.math.cnrs.fr/software/

Camera Trap Assistant is an independent project. It is not affiliated with,
sponsored by, or endorsed by CNRS or the DeepFaune authors.

## Model weights

Model files are data assets, not project-owned source code.

The full CeCILL v2.1 and CC BY-SA 4.0 texts supplied by DeepFaune are retained
in `CameraTrapAssistant/src/models/LICENSE.txt`. DeepFaune model details:
https://deepfaune.pages.math.cnrs.fr/software/

MegaDetector source code is published under the MIT License:
https://github.com/agentmorris/MegaDetector

Sorrel provenance is described in the MegaDetector v1000 release notes:
https://github.com/agentmorris/MegaDetector/blob/main/docs/release-notes/mdv1000-release.md

## Bundled software

The Windows distribution includes ExifTool 13.36 by Phil Harvey and a portable
Strawberry Perl runtime. ExifTool is available under the same terms as Perl
(Artistic License or GNU GPL). The portable package also includes a launcher
by Oliver Betz under CC0.

The package's notices and license bundle are preserved under:

- `CameraTrapAssistant/resources/third_party/windows/exiftool/README.txt`
- `CameraTrapAssistant/resources/third_party/windows/exiftool/exiftool_files/readme_windows.txt`
- `CameraTrapAssistant/resources/third_party/windows/exiftool/exiftool_files/windows_exiftool.txt`
- `CameraTrapAssistant/resources/third_party/windows/exiftool/exiftool_files/LICENSE`
- `CameraTrapAssistant/resources/third_party/windows/exiftool/exiftool_files/Licenses_Strawberry_Perl.zip`

ExifTool project: https://exiftool.org/

## Python dependencies

The application declares the following direct dependencies. License names are
a review aid based on current upstream package metadata; an exact release must
be audited against the versions actually resolved and distributed.

| Dependency | Upstream license |
| --- | --- |
| PyTorch | BSD 3-Clause |
| torchvision | BSD 3-Clause |
| Ultralytics | AGPL-3.0 |
| NumPy | BSD 3-Clause |
| OpenCV Python | Apache-2.0 |
| Pillow | HPND / MIT-CMU |
| pandas | BSD 3-Clause |
| Matplotlib | PSF-based |
| ReportLab | BSD |
| Hachoir | GPL-2.0 |
| geopy | MIT |
| tzlocal | MIT |
| openmeteo-requests | MIT |
| requests-cache | BSD 2-Clause |
| retry-requests | GPL-3.0-or-later |
| dill | BSD 3-Clause |
| timm | Apache-2.0 |
| TkinterMapView | CC0-1.0 |

Ultralytics licensing is especially relevant because the bundled YOLO model
runtime uses it: https://www.ultralytics.com/license

## Maps, geocoding, and weather data

The application uses TkinterMapView (CC0) and, by default, OpenStreetMap tiles
and Nominatim geocoding. OpenStreetMap data is available under ODbL and must be
credited as required by:

- https://www.openstreetmap.org/copyright
- https://operations.osmfoundation.org/policies/tiles/
- https://operations.osmfoundation.org/policies/nominatim/

Weather data is requested from Open-Meteo. Its free/open-access data requires
attribution to Open-Meteo and the relevant source providers under CC BY 4.0:
https://open-meteo.com/en/terms

These public services have usage policies and availability limits; their
inclusion here does not grant permission to exceed those policies.

## Icons and trademarks

`github-mark.png` is a GitHub trademark asset and must be used under GitHub's
logo guidelines: https://github.com/logos

`kofi_symbol.png` depicts the Ko-fi trademark. Ko-fi is not affiliated with or
an endorser of this project.

GitHub, Ko-fi, DeepFaune, CNRS, MegaDetector, OpenStreetMap, and Open-Meteo
names and marks belong to their respective owners.
