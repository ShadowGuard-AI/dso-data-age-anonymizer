import argparse
import datetime
import logging
import random
import re
import os
import chardet
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_argparse():
    """
    Sets up the argument parser for the command-line interface.
    """
    parser = argparse.ArgumentParser(description='Shifts dates in data by a random interval to anonymize them.')
    parser.add_argument('input_file', help='Path to the input file.')
    parser.add_argument('output_file', help='Path to the output file.')
    parser.add_argument('--max_shift_days', type=int, default=365, help='Maximum number of days to shift dates by. Defaults to 365.')
    parser.add_argument('--seed', type=int, default=None, help='Random seed for reproducibility. Defaults to None.')
    parser.add_argument('--date_format', type=str, default='%Y-%m-%d', help='Date format to search for. Defaults to %%Y-%%m-%%d.')
    parser.add_argument('--encoding', type=str, default=None, help='Encoding of the input file. If not specified, it will be detected automatically.')
    return parser.parse_args()

def detect_encoding(file_path):
    """
    Detects the encoding of a file.
    """
    try:
        with open(file_path, 'rb') as f:
            raw_data = f.read()
            result = chardet.detect(raw_data)
            return result['encoding']
    except Exception as e:
        logging.error(f"Error detecting encoding: {e}")
        return None

def shift_date(date_str, shift_days, date_format):
    """
    Shifts a date by a random interval.

    Args:
        date_str (str): The date string to shift.
        max_shift_days (int): The maximum number of days to shift.
        date_format (str): The format of the date string.
        random_state (random.Random): Random number generator.

    Returns:
        str: The shifted date string, or None if an error occurred.
    """
    try:
        date_obj = datetime.datetime.strptime(date_str, date_format).date()
        shifted_date = date_obj + datetime.timedelta(days=shift_days)
        return shifted_date.strftime(date_format)
    except ValueError as e:
        logging.warning(f"Invalid date format or value: {date_str}. Error: {e}")
        return None
    except Exception as e:
        logging.error(f"Error shifting date {date_str}: {e}")
        return None

def pattern_from_format(date_format):
    """Build a search pattern from a strptime style date format.

    Each directive becomes the digit or name shape it matches, and
    every other character is matched literally, so a run with
    --date_format %d/%m/%Y searches for dates written that way.
    """
    directives = {
        'Y': r'\d{4}', 'y': r'\d{2}', 'm': r'\d{2}', 'd': r'\d{2}',
        'H': r'\d{2}', 'M': r'\d{2}', 'S': r'\d{2}', 'j': r'\d{3}',
        'b': r'[A-Za-z]+', 'B': r'[A-Za-z]+', 'a': r'[A-Za-z]+',
        'A': r'[A-Za-z]+', 'p': r'[A-Za-z]+', '%': '%',
    }
    # The pattern built here has no boundaries on either side, and I have
    # watched what that does: in the text 12023-02-20 the pattern finds
    # 2023-02-20 starting one digit in, and shifts that, producing
    # 12023-02-17. It also demands exactly two digits for month and day,
    # so a real date written 2023-1-5 is never found at all.
    parts = []
    i = 0
    while i < len(date_format):
        ch = date_format[i]
        if ch == '%' and i + 1 < len(date_format) and date_format[i + 1] in directives:
            parts.append(directives[date_format[i + 1]])
            i += 2
        else:
            parts.append(re.escape(ch))
            i += 1
    return ''.join(parts)

def anonymize_data(input_file, output_file, max_shift_days, seed, date_format, encoding=None):
    """
    Anonymizes dates in the input file and writes the result to the output file.

    Args:
        input_file (str): Path to the input file.
        output_file (str): Path to the output file.
        max_shift_days (int): Maximum number of days to shift dates by.
        seed (int): Random seed for reproducibility.
        date_format (str): Date format to search for.
        encoding (str, optional): Encoding of the input file. If None, autodetect.
    """

    if not os.path.exists(input_file):
        logging.error(f"Input file not found: {input_file}")
        return False

    if os.path.realpath(output_file) == os.path.realpath(input_file):
        logging.error("Refusing to run: output path resolves to the input file.")
        return False

    if encoding is None:
        encoding = detect_encoding(input_file)
        if encoding is None:
            logging.error("Could not detect file encoding. Please specify it using --encoding.")
            return False

    try:
        # The input is read in full and closed before any output is
        # opened, so a failed or refused run leaves the input intact.
        # errors='ignore' is the sharp edge in this read: bytes that do
        # not decode in the detected encoding are dropped silently, so a
        # file can lose characters that have nothing to do with its dates
        # and no log line records the loss.
        with open(input_file, 'r', encoding=encoding, errors='ignore') as infile:
            content = infile.read()

        random_state = random.Random(seed)  # Initialize random number generator
        date_regex = re.compile(pattern_from_format(date_format))

        # One shift is drawn for the whole file, not one per date. The
        # point of the tool is hiding absolute dates while keeping the
        # gaps between them, and a fresh draw per date scrambles those
        # gaps and can reorder events that were days apart.
        shift_days = random_state.randint(-max_shift_days, max_shift_days)

        shifted_count = [0]
        # Two honest notes on this draw and this counter. The range
        # includes zero, so a run can shift every date by nothing and
        # still count them all as shifted, and the count below reflects
        # that. And a text that matches the pattern's shape but is not a
        # real date, like 2023-13-45, fails strptime inside shift_date and
        # is returned unchanged without counting, so it sits in the output
        # as it was while the run succeeds on the dates around it.

        def replace_date(match):
            date_str = match.group(0)
            shifted_date = shift_date(date_str, shift_days, date_format)
            if shifted_date:
                shifted_count[0] += 1
                return shifted_date
            else:
                return date_str  # Return original date if shifting fails

        anonymized = date_regex.sub(replace_date, content)

        if shifted_count[0] == 0:
            logging.info("No dates shifted.")
            print("No dates shifted.")
            return False

        with open(output_file, 'w', encoding=encoding) as outfile:
            outfile.write(anonymized)
        logging.info(f"Successfully anonymized data from {input_file} to {output_file}")
        return True

    except Exception as e:
        logging.error(f"An error occurred during anonymization: {e}")
        return False

def main():
    """
    Main function to parse arguments and run the anonymization process.
    """
    args = setup_argparse()

    # Input validation: Ensure max_shift_days is a positive integer
    if args.max_shift_days <= 0:
        logging.error("max_shift_days must be a positive integer.")
        sys.exit(1)

    if not anonymize_data(args.input_file, args.output_file, args.max_shift_days, args.seed, args.date_format, args.encoding):
        sys.exit(1)


if __name__ == "__main__":
    main()