#!/usr/bin/env python3
import re
from datetime import datetime
import os
from typing import List, Set, Dict, Tuple
from collections import defaultdict
import argparse
import sys
from pathlib import Path
import time

class ColorOutput:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print_success(message): print(f"{ColorOutput.GREEN}[+] {message}{ColorOutput.ENDC}")
    @staticmethod
    def print_info(message): print(f"{ColorOutput.BLUE}[*] {message}{ColorOutput.ENDC}")
    @staticmethod
    def print_warning(message): print(f"{ColorOutput.WARNING}[!] {message}{ColorOutput.ENDC}")
    @staticmethod
    def print_error(message): print(f"{ColorOutput.FAIL}[-] {message}{ColorOutput.ENDC}")

class ProgressBar:
    def __init__(self, total, prefix='Progress:', length=50):
        self.total = total
        self.prefix = prefix
        self.length = length
        self.current = 0
        self.start_time = time.time()
        self.spinner = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.spinner_idx = 0

    def update(self, current):
        self.current = current
        percentage = (current / self.total) * 100
        filled_length = int(self.length * current // self.total)
        bar = '█' * filled_length + '─' * (self.length - filled_length)
        spinner = self.spinner[self.spinner_idx]
        self.spinner_idx = (self.spinner_idx + 1) % len(self.spinner)
        
        elapsed_time = time.time() - self.start_time
        if current > 0:
            eta = elapsed_time * (self.total - current) / current
            eta_str = f"ETA: {eta:.1f}s"
        else:
            eta_str = "ETA: --"

        sys.stdout.write(f'\r{self.prefix} |{bar}| {percentage:6.2f}% {spinner} {current}/{self.total} {eta_str}')
        if current == self.total:
            sys.stdout.write('\n')
        sys.stdout.flush()

class SubdomainPatternAnalyzer:
    def __init__(self, verbose=False):
        self.verbose = verbose
        self.env_words = {
            'prod', 'production', 'dev', 'development', 
            'test', 'testing', 'stage', 'staging',
            'acc', 'acceptance', 'uat', 'qa',
            'int', 'integration', 'demo', 'beta',
            'sandbox', 'sbox', 'experimental', 'exp'
        }
        
        # Cloud region patterns
        self.cloud_regions = {
            'regions': {
                'east': ['west', 'central', 'north', 'south'],
                'west': ['east', 'central', 'north', 'south'],
                'central': ['east', 'west', 'north', 'south'],
                'north': ['east', 'west', 'central', 'south'],
                'south': ['east', 'west', 'central', 'north'],
                'northeast': ['northwest', 'southeast', 'southwest', 'central'],
                'northwest': ['northeast', 'southeast', 'southwest', 'central'],
                'southeast': ['northeast', 'northwest', 'southwest', 'central'],
                'southwest': ['northeast', 'northwest', 'southeast', 'central']
            },
            'prefixes': {
                'us': ['eu', 'ap', 'sa', 'af', 'ca'],
                'eu': ['us', 'ap', 'sa', 'af', 'ca'],
                'ap': ['us', 'eu', 'sa', 'af', 'ca'],
                'sa': ['us', 'eu', 'ap', 'af', 'ca'],
                'af': ['us', 'eu', 'ap', 'sa', 'ca'],
                'ca': ['us', 'eu', 'ap', 'sa', 'af']
            }
        }
        
        # Fixed paterns that preserve its structure
        self.patterns = {
            'single_digit': r'(?<!\d)(\d)(?!\d)',
            'double_digits': r'(?<!\d)(\d{2})(?!\d)',
            'two_chars': r'(?<![a-z])([a-z]{2})(?![a-z])',
            'cloud_region': r'([a-z]{2})-([a-z]+)-(\d+)'  
        }
        
        self.results_dir = Path('pattern_analysis_results')
        self.results_dir.mkdir(exist_ok=True)

    def identify_patterns(self, url: str) -> Dict[str, List[tuple]]:
        """Identify patterns while preserving URL structure."""
        found_patterns = defaultdict(list)
        parts = url.split('.')
        
        for i, part in enumerate(parts):
            # Look for cloud regions first
            cloud_matches = list(re.finditer(self.patterns['cloud_region'], part.lower()))
            if cloud_matches:
                for match in cloud_matches:
                    prefix, region, number = match.groups()
                    if (prefix in self.cloud_regions['prefixes'] and 
                        region in self.cloud_regions['regions']):
                        found_patterns['cloud_region'].append((
                            match.group(),
                            match.span(),
                            i,
                            (prefix, region, number)
                        ))
                        if self.verbose:
                            ColorOutput.print_info(f"Found cloud region: {match.group()} in part {i}")
                continue  # IMPORTANT NOTICE: Skip other pattern checks for this part if it's a cloud region

            # Original pattern matching logic
            for match in re.finditer(self.patterns['single_digit'], part):
                found_patterns['single_digit'].append((match.group(), match.span(), i))
            
            for match in re.finditer(self.patterns['double_digits'], part):
                found_patterns['double_digits'].append((match.group(), match.span(), i))
            
            if part.lower() in self.env_words:
                found_patterns['env_words'].append((part, (0, len(part)), i))
        
        return found_patterns

    def generate_variations(self, url: str, patterns: Dict[str, List[tuple]], max_variations=1000) -> Set[str]:
        """Generate variations while strictly preserving URL structure."""
        parts = url.split('.')
        variations = {tuple(parts)}
        
        for pattern_type, matches in patterns.items():
            new_variations = set()
            
            for current_parts in variations:
                current_parts = list(current_parts)
                
                if pattern_type == 'cloud_region':
                    for match, (start, end), part_idx, (prefix, region, number) in matches:
                        # Generate region variations
                        for new_prefix in self.cloud_regions['prefixes'].get(prefix, [prefix]):
                            for new_region in self.cloud_regions['regions'].get(region, [region]):
                                # We don't need to generate number variations here as they're 
                                # handled by the single_digit pattern
                                new_part = f"{new_prefix}-{new_region}-{number}"
                                temp_parts = current_parts.copy()
                                temp_parts[part_idx] = new_part
                                new_variations.add(tuple(temp_parts))
                
                else:
                    for match, (start, end), part_idx in matches:
                        part = current_parts[part_idx]
                        
                        if pattern_type == 'single_digit':
                            for i in range(10):
                                new_part = part[:start] + str(i) + part[end:]
                                temp_parts = current_parts.copy()
                                temp_parts[part_idx] = new_part
                                new_variations.add(tuple(temp_parts))
                        
                        elif pattern_type == 'double_digits':
                            for i in range(10, 100):
                                new_part = part[:start] + str(i) + part[end:]
                                temp_parts = current_parts.copy()
                                temp_parts[part_idx] = new_part
                                new_variations.add(tuple(temp_parts))
                        
                        elif pattern_type == 'env_words':
                            for env_word in self.env_words:
                                if len(env_word) <= len(match) + 2:
                                    temp_parts = current_parts.copy()
                                    temp_parts[part_idx] = env_word
                                    new_variations.add(tuple(temp_parts))
            
            if new_variations:
                variations.update(new_variations)
                if len(variations) > max_variations:
                    ColorOutput.print_warning(f"Reached maximum variations limit ({max_variations})")
                    variations = set(sorted(variations)[:max_variations])
                    break
        
        return {'.'.join(parts) for parts in variations}

    def analyze_and_generate(self, input_file: str, max_variations=1000):
        """Main analysis method with progress tracking."""
        if not os.path.exists(input_file):
            ColorOutput.print_error(f"Input file not found: {input_file}")
            return None, None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        pattern_log = self.results_dir / f'pattern_analysis_{timestamp}.txt'
        variations_file = self.results_dir / f'variations_{timestamp}.txt'
        
        with open(input_file, 'r') as f:
            subdomains = [line.strip() for line in f if line.strip()]

        total_patterns_found = 0
        total_variations = 0
        start_time = time.time()
        
        progress = ProgressBar(len(subdomains), prefix='Analyzing')

        # Write analysis to log file
        with open(pattern_log, 'w') as log_f:
            log_f.write(f"Pattern Analysis Report - {datetime.now()}\n")
            log_f.write("=" * 50 + "\n\n")
            
            # Write only variations to variations file
            with open(variations_file, 'w') as var_f:
                for idx, subdomain in enumerate(subdomains, 1):
                    progress.update(idx)
                    
                    log_f.write(f"\nAnalyzing: {subdomain}\n")
                    log_f.write("-" * 30 + "\n")
                    
                    patterns = self.identify_patterns(subdomain)
                    if patterns:
                        total_patterns_found += sum(len(matches) for matches in patterns.values())
                        for pattern_type, matches in patterns.items():
                            if matches:
                                if pattern_type == 'cloud_region':
                                    log_f.write(f"{pattern_type}: {', '.join(m[0] for m, _, _, _ in matches)}\n")
                                else:
                                    log_f.write(f"{pattern_type}: {', '.join(m[0] for m, _, _ in matches)}\n")
                        
                        variations = self.generate_variations(subdomain, patterns, max_variations)
                        total_variations += len(variations)
                        
                        # Write only the variations, one per line
                        for variant in sorted(variations):
                            var_f.write(f"{variant}\n")
                    else:
                        log_f.write("No patterns found\n")

            # Write summary only to log file
            elapsed_time = time.time() - start_time
            summary = f"""
Analysis Summary:
----------------
Total subdomains analyzed: {len(subdomains)}
Total patterns found: {total_patterns_found}
Total variations generated: {total_variations}
Time elapsed: {elapsed_time:.2f} seconds
            """
            log_f.write(summary)

        return pattern_log, variations_file

def main():
    parser = argparse.ArgumentParser(description='Advanced Subdomain Pattern Analyzer')
    parser.add_argument('-iL', '--input-list', required=True,
                      help='Input file containing list of subdomains')
    parser.add_argument('-v', '--verbose', action='store_true',
                      help='Enable verbose output')
    parser.add_argument('--max-variations', type=int, default=1000,
                      help='Maximum variations per subdomain (default: 1000)')

    args = parser.parse_args()

    try:
        analyzer = SubdomainPatternAnalyzer(verbose=args.verbose)
        pattern_log, variations_file = analyzer.analyze_and_generate(
            args.input_list,
            max_variations=args.max_variations
        )
        
        if pattern_log and variations_file:
            ColorOutput.print_success(f"Analysis complete!")
            ColorOutput.print_info(f"Pattern log: {pattern_log}")
            ColorOutput.print_info(f"Variations: {variations_file}")
    except KeyboardInterrupt:
        ColorOutput.print_warning("\nAnalysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        ColorOutput.print_error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()
