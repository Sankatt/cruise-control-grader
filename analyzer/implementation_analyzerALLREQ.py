#!/usr/bin/env python3
"""
Implementation Analyzer - Checks if CruiseControl.java satisfies requirements

This script analyzes the actual implementation code to verify if requirements
are correctly implemented, separate from test coverage.
"""

import re
from typing import Dict, Set, List
from pathlib import Path


class ImplementationAnalyzer:
    """Analyzes CruiseControl.java implementation for requirement satisfaction"""
    
    def __init__(self, implementation_file_path: str):
        self.impl_file_path = Path(implementation_file_path)
        self.impl_content = ""
        self.requirements_satisfied = set()
        
    def load_implementation_file(self) -> bool:
        """Load the implementation file content"""
        try:
            with open(self.impl_file_path, 'r', encoding='utf-8') as f:
                self.impl_content = f.read()
            return True
        except Exception as e:
            print(f"Error loading implementation file: {e}")
            return False
    
    def check_r1_r2_initialization(self) -> Set[str]:
        """R1, R2: Check if speedSet and speedLimit are initialized to null"""
        satisfied = set()
        
        # Look for constructor
        constructor_pattern = r'public\s+CruiseControl\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        constructor_match = re.search(constructor_pattern, self.impl_content, re.DOTALL)
        
        if constructor_match:
            constructor_body = constructor_match.group(1)
            
            # Check R1: speedSet = null
            if re.search(r'speedSet\s*=\s*null', constructor_body):
                satisfied.add('R1')
            # Also check if it's initialized as null in declaration
            elif re.search(r'private\s+Integer\s+speedSet\s*=\s*null', self.impl_content):
                satisfied.add('R1')
            # Or just declared as Integer (defaults to null)
            elif re.search(r'private\s+Integer\s+speedSet\s*;', self.impl_content) and \
                 not re.search(r'speedSet\s*=\s*\d', constructor_body):
                satisfied.add('R1')
            
            # Check R2: speedLimit = null
            if re.search(r'speedLimit\s*=\s*null', constructor_body):
                satisfied.add('R2')
            elif re.search(r'private\s+Integer\s+speedLimit\s*=\s*null', self.impl_content):
                satisfied.add('R2')
            elif re.search(r'private\s+Integer\s+speedLimit\s*;', self.impl_content) and \
                 not re.search(r'speedLimit\s*=\s*\d', constructor_body):
                satisfied.add('R2')
        
        return satisfied
    
    def check_r3_r4_setSpeedSet(self) -> Set[str]:
        """R3, R4: Check setSpeedSet accepts positive values and throws exception for ≤0"""
        satisfied = set()
        
        # Find setSpeedSet method
        method_pattern = r'public\s+void\s+setSpeedSet\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1)
            
            # R4: Check for zero/negative validation
            if re.search(r'if\s*\([^)]*speedSet\s*<=\s*0', method_body) or \
               re.search(r'if\s*\([^)]*speedSet\s*<\s*1', method_body) or \
               re.search(r'if\s*\(\s*speedSet\s*<=\s*0', method_body):
                # Check if it throws exception
                if re.search(r'throw\s+new\s+\w*IncorrectSpeedSet\w*Exception', method_body):
                    satisfied.add('R4')
            
            # R3: Check if it actually sets the value (assumes positive values work)
            if re.search(r'this\.speedSet\s*=\s*speedSet', method_body) or \
               re.search(r'speedSet\s*=\s*speedSet', method_body):
                # Only add R3 if there's no unconditional throw
                if 'throw' not in method_body or 'if' in method_body:
                    satisfied.add('R3')
        
        return satisfied
    
    def check_r5_r6_speedSet_vs_speedLimit(self) -> Set[str]:
        """R5, R6: Check speedSet cannot exceed speedLimit"""
        satisfied = set()
        
        method_pattern = r'public\s+void\s+setSpeedSet\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1)
            
            # R5: Check if there's a comparison with speedLimit
            if re.search(r'speedSet\s*>\s*.*speedLimit', method_body) or \
               re.search(r'speedLimit\s*<\s*speedSet', method_body):
                satisfied.add('R5')
                
                # R6: Check if it throws exception
                if re.search(r'throw\s+new\s+\w*SpeedSetAboveSpeedLimit\w*Exception', method_body):
                    satisfied.add('R6')
        
        return satisfied
    
    def check_r7_r8_setSpeedLimit(self) -> Set[str]:
        """R7, R8: Check setSpeedLimit accepts positive and throws for ≤0"""
        satisfied = set()
        
        method_pattern = r'public\s+void\s+setSpeedLimit\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1)
            
            # R8: Check for zero/negative validation
            if re.search(r'if\s*\([^)]*speedLimit\s*<=\s*0', method_body) or \
               re.search(r'if\s*\([^)]*speedLimit\s*<\s*1', method_body):
                if re.search(r'throw\s+new\s+\w*IncorrectSpeedLimit\w*Exception', method_body):
                    satisfied.add('R8')
            
            # R7: Check if it sets the value
            if re.search(r'this\.speedLimit\s*=\s*speedLimit', method_body):
                if 'throw' not in method_body or 'if' in method_body:
                    satisfied.add('R7')
        
        return satisfied
    
    def check_r9_cannot_set_speedLimit(self) -> Set[str]:
        """R9: Check cannot set speedLimit if speedSet exists"""
        satisfied = set()
        
        method_pattern = r'public\s+void\s+setSpeedLimit\s*\([^)]*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1)
            
            # Check if there's validation for existing speedSet
            if re.search(r'if\s*\([^)]*speedSet\s*!=\s*null', method_body) or \
               re.search(r'if\s*\(\s*speedSet\s*!=\s*null', method_body):
                if re.search(r'throw\s+new\s+\w*CannotSetSpeedLimit\w*Exception', method_body):
                    satisfied.add('R9')
        
        return satisfied
    
    def check_r10_r11_disable(self) -> Set[str]:
        """R10, R11: Check disable sets speedSet to null but not speedLimit"""
        satisfied = set()
        
        method_pattern = r'public\s+void\s+disable\s*\(\s*\)\s*\{([^}]*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1)
            
            # R10: Sets speedSet to null
            if re.search(r'speedSet\s*=\s*null', method_body):
                satisfied.add('R10')
            
            # R11: Does NOT alter speedLimit (absence of speedLimit = something)
            if not re.search(r'speedLimit\s*=', method_body):
                satisfied.add('R11')
        
        return satisfied
    
    def check_r12_r19_nextCommand(self) -> Set[str]:
        """R12-R19: Check nextCommand logic"""
        satisfied = set()
        
        method_pattern = r'public\s+Response\s+nextCommand\s*\(\s*\)\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}'
        method_match = re.search(method_pattern, self.impl_content, re.DOTALL)
        
        if method_match:
            method_body = method_match.group(1).lower()
            
            # R12: IDLE when speedSet not initialized
            if 'speedset' in method_body and 'null' in method_body and 'idle' in method_body:
                satisfied.add('R12')
            
            # R13: IDLE when disabled (this is complex, simplified check)
            # Since disable() sets speedSet to null, R13 might be same as R12
            
            # R14: REDUCE when speed > speedSet
            if 'reduce' in method_body and '>' in method_body:
                satisfied.add('R14')
            
            # R16: INCREASE when speed < speedSet
            if 'increase' in method_body and '<' in method_body:
                satisfied.add('R16')
            
            # R19: KEEP when speed == speedSet
            if 'keep' in method_body and '==' in method_body:
                satisfied.add('R19')
            
            # R17: REDUCE when > speedLimit
            if 'speedlimit' in method_body and 'reduce' in method_body:
                satisfied.add('R17')
        
        return satisfied
    
    def analyze(self) -> Dict:
        """Main analysis method"""
        if not self.load_implementation_file():
            return {
                'success': False,
                'error': 'Failed to load implementation file'
            }
        
        # Check all requirements
        self.requirements_satisfied.update(self.check_r1_r2_initialization())
        self.requirements_satisfied.update(self.check_r3_r4_setSpeedSet())
        self.requirements_satisfied.update(self.check_r5_r6_speedSet_vs_speedLimit())
        self.requirements_satisfied.update(self.check_r7_r8_setSpeedLimit())
        self.requirements_satisfied.update(self.check_r9_cannot_set_speedLimit())
        self.requirements_satisfied.update(self.check_r10_r11_disable())
        self.requirements_satisfied.update(self.check_r12_r19_nextCommand())
        
        all_requirements = set([f'R{i}' for i in range(1, 20)])
        missing = all_requirements - self.requirements_satisfied
        
        return {
            'success': True,
            'implementation_file': str(self.impl_file_path),
            'requirements_satisfied': sorted(list(self.requirements_satisfied)),
            'requirements_missing': sorted(list(missing)),
            'total_requirements': len(all_requirements),
            'requirements_found': len(self.requirements_satisfied),
            'satisfaction_percentage': round((len(self.requirements_satisfied) / len(all_requirements)) * 100, 2)
        }
    
    def generate_report(self) -> str:
        """Generate human-readable report"""
        analysis = self.analyze()
        
        if not analysis['success']:
            return f"Analysis failed: {analysis.get('error', 'Unknown error')}"
        
        report = []
        report.append("=" * 70)
        report.append("IMPLEMENTATION ANALYSIS REPORT")
        report.append("=" * 70)
        report.append(f"Implementation File: {analysis['implementation_file']}")
        report.append("")
        
        report.append(f"Requirements Satisfied: {analysis['requirements_found']}/{analysis['total_requirements']} ({analysis['satisfaction_percentage']}%)")
        report.append("")
        
        report.append("SATISFIED REQUIREMENTS:")
        if analysis['requirements_satisfied']:
            for req in analysis['requirements_satisfied']:
                report.append(f"  ✓ {req}")
        else:
            report.append("  (none)")
        report.append("")
        
        report.append("MISSING REQUIREMENTS:")
        if analysis['requirements_missing']:
            for req in analysis['requirements_missing']:
                report.append(f"  ✗ {req}")
        else:
            report.append("  (none)")
        
        report.append("=" * 70)
        
        return "\n".join(report)


def main():
    """Example usage"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python implementation_analyzer.py <path_to_CruiseControl.java>")
        print("\nExample:")
        print("  python implementation_analyzer.py CruiseControl.java")
        sys.exit(1)
    
    impl_file = sys.argv[1]
    analyzer = ImplementationAnalyzer(impl_file)
    
    print(analyzer.generate_report())


if __name__ == '__main__':
    main()
