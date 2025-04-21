# dso-data-age-anonymizer
Shifts dates in data by a random interval, preserving relative time relationships while anonymizing specific date information. Can be configured with a maximum shift interval. - Focused on Tools for sanitizing and obfuscating sensitive data within text files and structured data formats

## Install
`git clone https://github.com/ShadowStrikeHQ/dso-data-age-anonymizer`

## Usage
`./dso-data-age-anonymizer [params]`

## Parameters
- `-h`: Show help message and exit
- `--max_shift_days`: Maximum number of days to shift dates by. Defaults to 365.
- `--seed`: Random seed for reproducibility. Defaults to None.
- `--date_format`: Date format to search for. Defaults to %Y-%m-%d.
- `--encoding`: Encoding of the input file. If not specified, it will be detected automatically.

## License
Copyright (c) ShadowStrikeHQ
