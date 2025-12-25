#!/usr/bin/env python3
"""
GitHub Repository Cloner
Clones student repositories for automated grading
"""

import os
import subprocess
import json
from pathlib import Path
from typing import List, Dict
from datetime import datetime


class GitHubCloner:
    """Handles cloning of student repositories from GitHub"""
    
    def __init__(self, output_dir: str = "./student_submissions"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.clone_results = []
        
    def clone_repo(self, repo_url: str, student_id: str) -> Dict:
        """
        Clone a single repository
        
        Args:
            repo_url: GitHub repository URL
            student_id: Unique identifier for the student
            
        Returns:
            Dict with clone status and information
        """
        student_dir = self.output_dir / student_id
        
        # Remove existing directory if present
        if student_dir.exists():
            import shutil
            shutil.rmtree(student_dir)
        
        result = {
            'student_id': student_id,
            'repo_url': repo_url,
            'timestamp': datetime.now().isoformat(),
            'success': False,
            'local_path': str(student_dir),
            'error': None
        }
        
        try:
            # Clone the repository
            cmd = ['git', 'clone', repo_url, str(student_dir)]
            
            process = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if process.returncode == 0:
                result['success'] = True
                print(f"✓ Successfully cloned {student_id}")
            else:
                result['error'] = process.stderr
                print(f"✗ Failed to clone {student_id}: {process.stderr}")
                
        except subprocess.TimeoutExpired:
            result['error'] = "Clone operation timed out"
            print(f"✗ Timeout cloning {student_id}")
        except Exception as e:
            result['error'] = str(e)
            print(f"✗ Error cloning {student_id}: {e}")
        
        self.clone_results.append(result)
        return result
    
    def clone_from_file(self, repos_file: str) -> List[Dict]:
        """
        Clone multiple repositories from a text file
        
        File format (one per line):
            student_id,repo_url
        or:
            student_id https://github.com/user/repo
            
        Args:
            repos_file: Path to file containing repository information
            
        Returns:
            List of clone results
        """
        repos_path = Path(repos_file)
        
        if not repos_path.exists():
            print(f"Error: File not found: {repos_file}")
            return []
        
        with open(repos_path, 'r') as f:
            lines = f.readlines()
        
        print(f"Found {len(lines)} repositories to clone")
        print("=" * 70)
        
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # Parse line - support both comma and space separated
            if ',' in line:
                student_id, repo_url = [x.strip() for x in line.split(',', 1)]
            else:
                parts = line.split()
                if len(parts) >= 2:
                    student_id, repo_url = parts[0], parts[1]
                else:
                    print(f"✗ Invalid line format: {line}")
                    continue
            
            print(f"\n[{i}/{len(lines)}] Cloning {student_id}...")
            self.clone_repo(repo_url, student_id)
        
        print("\n" + "=" * 70)
        self.print_summary()
        return self.clone_results
    
    def print_summary(self):
        """Print summary of clone operations"""
        total = len(self.clone_results)
        successful = sum(1 for r in self.clone_results if r['success'])
        failed = total - successful
        
        print(f"\nClone Summary:")
        print(f"  Total: {total}")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            print(f"\nFailed repositories:")
            for result in self.clone_results:
                if not result['success']:
                    print(f"  • {result['student_id']}: {result['error']}")
    
    def save_results(self, output_file: str = "clone_results.json"):
        """Save clone results to JSON file"""
        output_path = Path(output_file)
        
        with open(output_path, 'w') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_repos': len(self.clone_results),
                'successful': sum(1 for r in self.clone_results if r['success']),
                'results': self.clone_results
            }, f, indent=2)
        
        print(f"\nResults saved to: {output_file}")


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python github_cloner.py <repos_file>")
        print("\nRepos file format (one per line):")
        print("  student123,https://github.com/student123/cruise-control")
        print("or:")
        print("  student123 https://github.com/student123/cruise-control")
        print("\nExample:")
        print("  python github_cloner.py student_repos.txt")
        sys.exit(1)
    
    repos_file = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "./student_submissions"
    
    cloner = GitHubCloner(output_dir)
    cloner.clone_from_file(repos_file)
    cloner.save_results()


if __name__ == '__main__':
    main()
