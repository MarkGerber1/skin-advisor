"""
📊 Coverage Matrix Analyzer
Analyzes rule coverage for all makeup/skincare combinations
"""

import json
from typing import Dict, List, Set, Tuple, Optional, Any
from itertools import product
from dataclasses import dataclass, asdict
from .models import UserProfile, Product
from .selector import SelectorV2

@dataclass
class CoverageResult:
    """Result of coverage analysis for a specific combination"""
    combination: Dict[str, Any]
    category: str
    covered: bool
    products_found: int
    coverage_score: float  # 0.0 - 1.0
    gaps: List[str]
    
class CoverageMatrixAnalyzer:
    """Analyzes coverage of selection rules across all combinations"""
    
    def __init__(self):
        self.selector = SelectorV2()
        
        # Define all possible values for matrix
        self.makeup_categories = [
            "foundation", "concealer", "corrector", "powder", "blush", 
            "bronzer", "contour", "highlighter", "eyebrow", "mascara", 
            "eyeshadow", "eyeliner", "lipstick", "lip_gloss", "lip_liner"
        ]
        
        self.skincare_categories = [
            "cleanser", "toner", "serum", "moisturizer", 
            "eye_cream", "sunscreen", "mask"
        ]
        
        self.seasons = ["spring", "summer", "autumn", "winter"]
        self.undertones = ["warm", "cool", "neutral"]
        self.contrasts = ["low", "medium", "high"]
        
        self.skin_types = ["oily", "dry", "combo", "normal"]  # Match UserProfile enum
        self.concerns_sets = [
            [],  # No concerns
            ["acne"],
            ["dehydration"], 
            ["redness"],
            ["pigmentation"],
            ["aging"],
            ["sensitivity"],
            ["acne", "dehydration"],
            ["aging", "pigmentation"],
            ["redness", "sensitivity"]
        ]
        
    def generate_test_catalog(self) -> List[Product]:
        """Generate a test catalog with representative products"""
        products = []
        product_id = 1
        
        # Foundation products for all undertones
        for undertone in self.undertones:
            for depth in ["light", "medium", "deep"]:
                products.append(Product(
                    key=f"foundation_{product_id}",
                    title=f"Foundation {undertone.title()} {depth.title()}",
                    brand="Test Brand",
                    category="foundation",
                    in_stock=True,
                    price=1500.0,
                    shade_name=f"{depth} {undertone}",
                    undertone_match=undertone,
                    id=f"foundation_{product_id}",  # Required field
                    name=f"Foundation {undertone.title()} {depth.title()}"  # Required field
                ))
                product_id += 1
        
        # Basic makeup products
        for category in ["concealer", "powder", "blush", "bronzer", "mascara"]:
            products.append(Product(
                key=f"{category}_{product_id}",
                title=f"Test {category.title()}",
                brand="Test Brand", 
                category=category,
                in_stock=True,
                price=800.0,
                id=f"{category}_{product_id}",  # Required field
                name=f"Test {category.title()}"  # Required field
            ))
            product_id += 1
        
        # Lipstick for all undertones
        for undertone in self.undertones:
            products.append(Product(
                key=f"lipstick_{undertone}_{product_id}",
                title=f"Lipstick {undertone.title()}",
                brand="Test Brand",
                category="lipstick", 
                in_stock=True,
                price=1200.0,
                undertone_match=undertone,
                id=f"lipstick_{undertone}_{product_id}",  # Required field
                name=f"Lipstick {undertone.title()}"  # Required field
            ))
            product_id += 1
        
        # Skincare products for different skin types
        skincare_actives = {
            "cleanser": [],
            "toner": ["niacinamide"],
            "serum": ["hyaluronic acid", "vitamin c"],
            "moisturizer": ["ceramide"],
            "sunscreen": [],
            "mask": ["clay"],
            "eye_cream": ["peptides"]
        }
        
        for category, actives in skincare_actives.items():
            products.append(Product(
                key=f"{category}_{product_id}",
                title=f"Test {category.title()}",
                brand="Test Brand",
                category=category,
                in_stock=True,
                price=1000.0,
                actives=actives,
                id=f"{category}_{product_id}",  # Required field
                name=f"Test {category.title()}"  # Required field
            ))
            product_id += 1
        
        return products
    
    def analyze_makeup_coverage(self, catalog: List[Product]) -> List[CoverageResult]:
        """Analyze coverage for all makeup combinations"""
        results = []
        
        # Generate all combinations for makeup
        combinations = list(product(
            self.makeup_categories,
            self.seasons, 
            self.undertones,
            self.contrasts
        ))
        
        print(f"Analyzing {len(combinations)} makeup combinations...")
        
        for category, season, undertone, contrast in combinations:
            # Create test profile
            profile = UserProfile(
                user_id=12345,  # Test user ID
                season=season,
                undertone=undertone, 
                contrast=contrast,
                skin_type="normal",  # Default for makeup analysis
                concerns=[]
            )
            
            # Test selection for this combination
            try:
                results_dict = self.selector.select_products_v2(
                    profile=profile,
                    catalog=catalog,
                    partner_code="test",
                    redirect_base=None
                )
                
                # Check if this category is covered
                makeup_results = results_dict.get("makeup", {})
                products_found = 0
                covered = False
                
                # Count products found for this category across all makeup sections
                for section_products in makeup_results.values():
                    matching_products = [p for p in section_products 
                                       if p.get("category", "").lower() == category.lower()]
                    products_found += len(matching_products)
                
                covered = products_found > 0
                coverage_score = min(products_found / 3.0, 1.0)  # Normalize to 0-1
                
                gaps = []
                if not covered:
                    gaps.append(f"No {category} products for {season}/{undertone}/{contrast}")
                elif products_found < 2:
                    gaps.append(f"Limited {category} options for {season}/{undertone}/{contrast}")
                
                results.append(CoverageResult(
                    combination={
                        "category": category,
                        "season": season,
                        "undertone": undertone,
                        "contrast": contrast
                    },
                    category=category,
                    covered=covered,
                    products_found=products_found,
                    coverage_score=coverage_score,
                    gaps=gaps
                ))
                
            except Exception as e:
                print(f"ERROR testing {category}/{season}/{undertone}/{contrast}: {e}")
                results.append(CoverageResult(
                    combination={
                        "category": category,
                        "season": season, 
                        "undertone": undertone,
                        "contrast": contrast
                    },
                    category=category,
                    covered=False,
                    products_found=0,
                    coverage_score=0.0,
                    gaps=[f"Selection failed: {str(e)}"]
                ))
        
        return results
    
    def analyze_skincare_coverage(self, catalog: List[Product]) -> List[CoverageResult]:
        """Analyze coverage for all skincare combinations"""
        results = []
        
        # Generate combinations for skincare
        combinations = list(product(
            self.skincare_categories,
            self.skin_types,
            self.concerns_sets
        ))
        
        print(f"Analyzing {len(combinations)} skincare combinations...")
        
        for category, skin_type, concerns in combinations:
            # Create test profile
            profile = UserProfile(
                user_id=12345,  # Test user ID
                season="autumn",  # Default for skincare
                undertone="neutral",  # Default for skincare
                contrast="medium",  # Default for skincare  
                skin_type=skin_type,
                concerns=concerns
            )
            
            # Test selection for this combination
            try:
                results_dict = self.selector.select_products_v2(
                    profile=profile,
                    catalog=catalog,
                    partner_code="test",
                    redirect_base=None
                )
                
                # Check if this category is covered
                skincare_results = results_dict.get("skincare", {})
                products_found = 0
                covered = False
                
                # Count products found for this category
                for routine_products in skincare_results.values():
                    matching_products = [p for p in routine_products
                                       if p.get("category", "").lower() == category.lower()]
                    products_found += len(matching_products)
                
                covered = products_found > 0
                coverage_score = min(products_found / 2.0, 1.0)  # Normalize to 0-1
                
                gaps = []
                if not covered:
                    gaps.append(f"No {category} for {skin_type} with {concerns}")
                elif products_found < 1:
                    gaps.append(f"Limited {category} options for {skin_type}")
                
                results.append(CoverageResult(
                    combination={
                        "category": category,
                        "skin_type": skin_type,
                        "concerns": concerns
                    },
                    category=category,
                    covered=covered,
                    products_found=products_found,
                    coverage_score=coverage_score,
                    gaps=gaps
                ))
                
            except Exception as e:
                print(f"ERROR testing {category}/{skin_type}/{concerns}: {e}")
                results.append(CoverageResult(
                    combination={
                        "category": category,
                        "skin_type": skin_type,
                        "concerns": concerns
                    },
                    category=category,
                    covered=False,
                    products_found=0,
                    coverage_score=0.0,
                    gaps=[f"Selection failed: {str(e)}"]
                ))
        
        return results
    
    def generate_coverage_report(self, makeup_results: List[CoverageResult], 
                                skincare_results: List[CoverageResult]) -> Dict[str, Any]:
        """Generate comprehensive coverage report"""
        
        # Calculate overall statistics
        total_combinations = len(makeup_results) + len(skincare_results)
        covered_combinations = sum(1 for r in makeup_results + skincare_results if r.covered)
        
        coverage_percentage = (covered_combinations / total_combinations) * 100
        
        # Find gaps by category
        makeup_gaps = {}
        for result in makeup_results:
            if not result.covered:
                category = result.category
                if category not in makeup_gaps:
                    makeup_gaps[category] = []
                makeup_gaps[category].append(result.combination)
        
        skincare_gaps = {}
        for result in skincare_results:
            if not result.covered:
                category = result.category
                if category not in skincare_gaps:
                    skincare_gaps[category] = []
                skincare_gaps[category].append(result.combination)
        
        # Calculate category-wise coverage
        makeup_category_coverage = {}
        for category in self.makeup_categories:
            category_results = [r for r in makeup_results if r.category == category]
            covered = sum(1 for r in category_results if r.covered)
            total = len(category_results)
            makeup_category_coverage[category] = {
                "covered": covered,
                "total": total,
                "percentage": (covered / total * 100) if total > 0 else 0
            }
        
        skincare_category_coverage = {}
        for category in self.skincare_categories:
            category_results = [r for r in skincare_results if r.category == category]
            covered = sum(1 for r in category_results if r.covered)
            total = len(category_results)
            skincare_category_coverage[category] = {
                "covered": covered,
                "total": total,
                "percentage": (covered / total * 100) if total > 0 else 0
            }
        
        return {
            "overall": {
                "total_combinations": total_combinations,
                "covered_combinations": covered_combinations,
                "coverage_percentage": coverage_percentage
            },
            "makeup": {
                "category_coverage": makeup_category_coverage,
                "gaps": makeup_gaps,
                "total_categories": len(self.makeup_categories),
                "categories_with_gaps": len(makeup_gaps)
            },
            "skincare": {
                "category_coverage": skincare_category_coverage,
                "gaps": skincare_gaps,
                "total_categories": len(self.skincare_categories),
                "categories_with_gaps": len(skincare_gaps)
            }
        }
    
    def save_detailed_results(self, makeup_results: List[CoverageResult], 
                            skincare_results: List[CoverageResult], 
                            output_path: str = "data/coverage_analysis.json"):
        """Save detailed analysis results to JSON"""
        
        detailed_data = {
            "makeup_results": [asdict(r) for r in makeup_results],
            "skincare_results": [asdict(r) for r in skincare_results],
            "analysis_metadata": {
                "makeup_categories": self.makeup_categories,
                "skincare_categories": self.skincare_categories,
                "seasons": self.seasons,
                "undertones": self.undertones,
                "contrasts": self.contrasts,
                "skin_types": self.skin_types,
                "concerns_sets": self.concerns_sets
            }
        }
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(detailed_data, f, indent=2, ensure_ascii=False)
        
        print(f"Detailed results saved to {output_path}")


def run_coverage_analysis():
    """Run complete coverage analysis"""
    print("Starting Coverage Matrix Analysis...")
    
    analyzer = CoverageMatrixAnalyzer()
    
    # Generate test catalog
    print("Generating test catalog...")
    catalog = analyzer.generate_test_catalog()
    print(f"Generated {len(catalog)} test products")
    
    # Analyze makeup coverage
    print("Analyzing makeup coverage...")
    makeup_results = analyzer.analyze_makeup_coverage(catalog)
    
    # Analyze skincare coverage  
    print("Analyzing skincare coverage...")
    skincare_results = analyzer.analyze_skincare_coverage(catalog)
    
    # Generate report
    print("Generating coverage report...")
    report = analyzer.generate_coverage_report(makeup_results, skincare_results)
    
    # Save detailed results
    analyzer.save_detailed_results(makeup_results, skincare_results)
    
    # Print summary
    print("\n" + "="*60)
    print("COVERAGE ANALYSIS SUMMARY")
    print("="*60)
    print(f"Overall Coverage: {report['overall']['coverage_percentage']:.1f}%")
    print(f"Total Combinations: {report['overall']['total_combinations']}")
    print(f"Covered: {report['overall']['covered_combinations']}")
    
    print(f"\nMAKEUP CATEGORIES:")
    for category, stats in report['makeup']['category_coverage'].items():
        print(f"  {category:12} {stats['percentage']:6.1f}% ({stats['covered']}/{stats['total']})")
    
    print(f"\nSKINCARE CATEGORIES:")
    for category, stats in report['skincare']['category_coverage'].items():
        print(f"  {category:12} {stats['percentage']:6.1f}% ({stats['covered']}/{stats['total']})")
    
    if report['makeup']['gaps']:
        print(f"\nMAKEUP GAPS ({len(report['makeup']['gaps'])} categories):")
        for category, gaps in report['makeup']['gaps'].items():
            print(f"  {category}: {len(gaps)} missing combinations")
    
    if report['skincare']['gaps']:
        print(f"\nSKINCARE GAPS ({len(report['skincare']['gaps'])} categories):")
        for category, gaps in report['skincare']['gaps'].items():
            print(f"  {category}: {len(gaps)} missing combinations")
    
    return report


if __name__ == "__main__":
    report = run_coverage_analysis()
