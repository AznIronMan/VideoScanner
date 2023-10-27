# VideoScanner

VideoScanner is an application for scanning video libraries and determining audio language and subtitle existence and language. The output is put into a SQLite database.

## Author

Mr. Clark of ClarkTribeGames, LLC

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Supported File Types](#supported-file-types)
- [Contributing](#contributing)
- [License](#license)

## Installation

Clone this repository and navigate to the project folder. Then run the following command to install the required packages:

```bash
pip install -r requirements.txt
```

## Usage

Run the program from the command line (for individual file scan):

```bash
python . -f <file_path>
```

Run the program from the command line (for directory scan):

```bash
python . -s 1 -f <directory_path>
```

Run the program from the command line (for directory reconcile):

```bash
python . -r 1 -f <directory_path>
```

(Command Line Arguments for Reference)

- `-f, --file`: Path to the video/audio file (individual file scan) or root directory (directory scan/reconcile).
  String, use quotes if path contains spaces.
- `-r, --reconcile`: Boolean for reconciling or not. Use 0 for False and 1 for True. (default: 0)
- `-s, --search`: Boolean for searching or not. Use 0 for False and 1 for True. (default: 0)

## Notes

- SQLite database is created in the same directory as the program within the `assets` folder.
- The file name for the SQLite database is generated based on host machine it is run on. This is to prevent multiple instances of the program from overwriting the database.
- Supported video file types are .mkv, .mp4, and .avi. This application is designed for Plex libraries.
- Files are marked `Completed` if they meet the criteria of being a .mkv file, having at least one audio track (any language), and at least one English subtitle track. These all should be embedded into the .mkv file to be considered `Completed`. (This will be customizable in the future.)
- If marked `Completed`, the file is not scanned again unless the database is deleted.
- If there are duplicate versions of the same video, the duplicate will be marked in the database, referencing the other file.
- If the file is a .mp4 or .avi and there is an accompanying .srt file, the record will be noted in the database but not marked `Completed`.

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request

## License

This project is licensed under the MIT License.

## Contact

For any queries or concerns, please contact Geoff Clark at geoff @ clarktribegames . com.
