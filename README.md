# Camera Trap Assistant

Camera Trap Assistant is a free, non-commercial, open-source desktop
application for detecting and classifying wildlife in camera-trap images and
videos. It can organize results, create CSV and PDF reports, and work with GPS
metadata.

It uses AI models and selected source code from
[DeepFaune](https://deepfaune.pages.math.cnrs.fr/software/), a CNRS project.
Camera Trap Assistant is an independent project and is not affiliated with or
endorsed by CNRS or the DeepFaune authors.

## Choose Your Path

### Install and Use

You want to analyze camera-trap media without installing Python or developer
tools.

- [Install the Windows application](#install-on-windows)
- [Install the macOS application](#install-on-macos)
- [Run your first analysis](#run-your-first-analysis)
- [Understand files and results](#files-and-results)
- [Get help](#get-help)

### Develop and Contribute

You want to run the source code, fix a bug, add a feature, improve another
platform, or prepare a release.

- [Set up a development environment](dev/README.md#development-setup)
- [Run the application from source](dev/README.md#run-from-source)
- [Run and write tests](tests/README.md)
- [Understand the repository](dev/README.md#repository-architecture)
- [Prepare a pull request](dev/README.md#prepare-a-pull-request)
- [Build the Windows installer](packaging/windows/README.md)
- [Build the macOS disk image](packaging/macos/README.md)

## Install and Use

### Install on Windows

Supported public packages are the 64-bit Windows installer and the macOS disk
image. Linux does not yet have a supported installer, although the application
can be run from source for development.

1. Open the
   [GitHub Releases page](https://github.com/noebernigaud/CameraTrapAssistant/releases).
2. Under the release's **Assets**, download
   `CameraTrapAssistant-<version>-Windows-x64-Setup.exe`.
3. Run the downloaded installer.
4. Open **Camera Trap Assistant** from the Windows Start menu.

The installer includes Python, the AI models, and ExifTool. You do not need to
install Python, Git, or Git LFS.

Each release also provides `SHA256SUMS.txt` for users who want to verify the
download:

```powershell
Get-FileHash .\CameraTrapAssistant-<version>-Windows-x64-Setup.exe -Algorithm SHA256
```

The displayed hash must match the installer entry in `SHA256SUMS.txt`.

### Install on macOS

1. Open the
   [GitHub Releases page](https://github.com/noebernigaud/CameraTrapAssistant/releases).
2. Under the release's **Assets**, download
   `CameraTrapAssistant-<version>-macOS-arm64.dmg` for an Apple silicon Mac, or
   `CameraTrapAssistant-<version>-macOS-x86_64.dmg` for an Intel Mac. The Apple
   menu, then **About This Mac**, shows which one you have.
3. Open the downloaded disk image.
4. Drag **Camera Trap Assistant** onto the **Applications** folder shown next
   to it.
5. Eject the disk image and open **Camera Trap Assistant** from Launchpad or
   the Applications folder.

The disk image includes Python, the AI models, and ExifTool. You do not need to
install Python, Git, or Git LFS.

The first time you select a folder on your Desktop, in Documents, in Downloads,
or on a memory card, macOS asks whether the application may read it. Analysis
cannot start until you allow it. You can change these permissions later in
**System Settings**, then **Privacy & Security**, then **Files and Folders**.

The disk image is signed and notarized by Apple. If macOS reports that the
application cannot be opened because the developer cannot be verified, the file
did not come from the official Releases page; delete it and download it again.

Each release also provides `SHA256SUMS.txt` for users who want to verify the
download:

```bash
shasum -a 256 ~/Downloads/CameraTrapAssistant-<version>-macOS-arm64.dmg
```

The displayed hash must match the disk image entry in `SHA256SUMS.txt`.

### Run Your First Analysis

> **Be aware of permanent files modifications.** Some options rename original files,
> move them into `empty` or `undefined` subfolders, or overwrite GPS metadata.
> Review the checked options before every run.

1. Launch Camera Trap Assistant.
2. Click **Choose Folder** and select the folder containing your camera-trap
   images or videos. Subfolders are included.
3. Review the options. Hover over an option to see a detailed explanation.
4. Click **Run**.
5. Follow progress in the **Logs** area. Processing time depends on the number
   of files and the computer's hardware.

AI classifications can be wrong. Review important results rather than treating
predictions as verified observations.

### Files and Results

The application recognizes common camera-trap formats:

- Videos: AVI, MP4, MPEG, MOV, and M4V
- Images: PNG, JPG, JPEG, TIFF, BMP, and GIF

Depending on the selected options, the application can create or change:

| Option | Result |
| --- | --- |
| **CSV file** | Creates `data/deepFaune_results.csv`. |
| **Statistics file** | Creates `data/stats.pdf`. |
| **Empty results to subfolder** | Moves matching original files to `empty/`. |
| **Undefined results to subfolder** | Moves low-confidence original files to `undefined/`. |
| **Rename with date and info** | Renames original files. |
| **Add GPS location** | Writes the selected coordinates into original files. |
| **Use added GPS data without updating files** | Uses coordinates in reports without changing media metadata. |
| **Combine data results with existing CSV** | Creates `data/deepFaune_combined_results.csv`. |

The selected folder and its subfolders are scanned recursively. Generated
`data`, `empty`, and `undefined` folders are placed inside the selected folder.

Classification runs locally. Features using maps, address lookup, or weather
data contact the third-party online services listed in
[Third-Party Notices](THIRD_PARTY_NOTICES.md).

### Get Help

If the application reports an error:

1. Read the last messages in the **Logs** area.
2. Retry with a small copied folder and options that do not modify files.
3. Check the
   [open issues](https://github.com/noebernigaud/CameraTrapAssistant/issues).
4. If the problem is new, create an issue with the application version, your
   Windows or macOS version, steps to reproduce, and relevant log messages.

## Develop and Contribute

Contributions to code, documentation, testing, user experience, and packaging
are welcome. Start with the [developer and contributor guide](dev/README.md).
It contains the cross-platform Python setup, source launch commands, project
architecture, coding expectations, and pull-request checklist.

Useful references:

- [Developer and contributor guide](dev/README.md)
- [Test guide](tests/README.md)
- [Windows packaging guide](packaging/windows/README.md)
- [macOS packaging guide](packaging/macos/README.md)
- [Third-party notices](THIRD_PARTY_NOTICES.md)
- [Issue tracker](https://github.com/noebernigaud/CameraTrapAssistant/issues)

Platform-specific distribution work belongs under `packaging/<platform>`, and
bundled native dependencies belong under
`CameraTrapAssistant/resources/third_party/<platform>`.

## License and Attribution

Project-original source code is copyright (c) 2025-2026 Noe Bernigaud and is
distributed under the [CeCILL v2.1 license](LICENSE). Adapted DeepFaune source
files retain their CNRS copyright and CeCILL notices.

The bundled DeepFaune model weights are licensed separately under
[CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/). Dependencies,
bundled software, services, and brand assets have their own terms. Review
[Third-Party Notices](THIRD_PARTY_NOTICES.md) before redistributing the
application.

Citation metadata is provided in [CITATION.cff](CITATION.cff). Research and
publications using the AI models should also acknowledge and cite DeepFaune
according to its official documentation.
