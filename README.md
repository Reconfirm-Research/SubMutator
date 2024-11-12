# SubMutator

## Subdomain Pattern Analyzer

A simple Python script for analyzing and generating subdomain variations based on common patterns found in URLs. This tool is especially useful for security researchers and penetration testers who need to discover potential subdomains.

## Features

- Pattern Detection and Variation Generation:
  - Single digits (0-9)
  - Double digits (10-99)
  - Environment words (prod, dev, test, etc.)
  - Cloud region patterns (eu-west-1, us-east-1, etc.)
  - Two-character combinations

- Smart Pattern Recognition:
  - Preserves domain structure
  - Maintains original dot notation
  - Intelligent environment word handling

- Cloud Region Support:
  - AWS region format detection
  - Region name variations (east, west, central, etc.)
  - Region prefix variations (us, eu, ap, etc.)

- Output Features:
  - Clean variations output (one URL per line)
  - Detailed pattern analysis logs
  - Progress bar with ETA
  - Colorized console output

## Installation

1. Clone the repository

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Basic usage:
```bash
python3 submutator.py -iL subdomains.txt
```

With verbose output:
```bash
python3 submutator.py -iL subdomains.txt -v
```

Custom maximum variations:
```bash
python3 submutator.py -iL subdomains.txt --max-variations 2000
```

### Command Line Arguments

- `-iL, --input-list`: Input file containing list of subdomains (required)
- `-v, --verbose`: Enable verbose output
- `--max-variations`: Maximum number of variations per subdomain (default: 1000)

### Example Input/Output

Input file (subdomains.txt):
```
sample-node6-el7.api-management.test.api.example.com
app.eu-central-1.example.com
```

Output will generate variations like:
```
sample-node0-el0.api-management.test.api.example.com
sample-node1-el1.api-management.prod.api.example.com
sample-node2-el2.api-management.dev.api.example.com
...
app.eu-west-1.example.com
app.us-central-1.example.com
app.ap-east-1.example.com
```

## Output Files

The tool generates two files in the `pattern_analysis_results` directory:

1. `pattern_analysis_[timestamp].txt`: Detailed analysis of patterns found
2. `variations_[timestamp].txt`: Generated subdomain variations

## Environment Words

The tool recognizes and varies the following environment words:
- prod, production
- dev, development
- test, testing
- stage, staging
- acc, acceptance
- uat
- qa
- int, integration
- demo, beta
- sandbox, sbox
- experimental, exp

Feel free to add extra.


## Cloud Region Patterns

Supports common cloud provider region formats:
- Region directions: east, west, north, south, central
- Complex regions: northeast, northwest, southeast, southwest
- Region prefixes: us, eu, ap, sa, af, ca

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is intended for security research and penetration testing with proper authorization. Users are responsible for complying with applicable laws and regulations.
