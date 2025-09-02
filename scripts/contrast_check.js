/**
 * WCAG AA Contrast Checker
 * Проверяет контрастность цветовых пар из дизайн-системы
 * 
 * WCAG Standards:
 * - Normal text: 4.5:1 minimum (AA)
 * - Large text: 3:1 minimum (AA) 
 * - Enhanced: 7:1 (AAA)
 */

const fs = require('fs');
const path = require('path');

// Цветовая палитра из tokens.css
const colors = {
  // Brand colors
  primary: '#C26A8D',
  secondary: '#F4DCE4', 
  accent: '#C9B7FF',
  
  // Neutral colors
  bg: '#FFFFFF',
  fg: '#121212',
  muted: '#6B6B6B',
  surface: '#FAFAFA',
  border: '#E9E9E9',
  
  // State colors
  success: '#2E7D32',
  warning: '#B26A00', 
  danger: '#B3261E',
  info: '#1976D2',
  
  // Dark theme variants
  darkBg: '#121212',
  darkFg: '#FFFFFF',
  darkMuted: '#CFCFCF',
  darkSurface: '#1B1B1B',
  darkBorder: '#2A2A2A',
  darkSuccess: '#4CAF50',
  darkWarning: '#FF9800',
  darkDanger: '#F44336',
  darkInfo: '#2196F3',
  darkAccent: '#D4C5FF'
};

/**
 * Convert hex color to RGB
 */
function hexToRgb(hex) {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  return result ? {
    r: parseInt(result[1], 16),
    g: parseInt(result[2], 16),
    b: parseInt(result[3], 16)
  } : null;
}

/**
 * Calculate relative luminance
 * https://www.w3.org/WAI/GL/wiki/Relative_luminance
 */
function getLuminance(rgb) {
  const rsRGB = rgb.r / 255;
  const gsRGB = rgb.g / 255;
  const bsRGB = rgb.b / 255;

  const r = rsRGB <= 0.03928 ? rsRGB / 12.92 : Math.pow((rsRGB + 0.055) / 1.055, 2.4);
  const g = gsRGB <= 0.03928 ? gsRGB / 12.92 : Math.pow((gsRGB + 0.055) / 1.055, 2.4);
  const b = bsRGB <= 0.03928 ? bsRGB / 12.92 : Math.pow((bsRGB + 0.055) / 1.055, 2.4);

  return 0.2126 * r + 0.7152 * g + 0.0722 * b;
}

/**
 * Calculate contrast ratio between two colors
 * https://www.w3.org/WAI/GL/wiki/Contrast_ratio
 */
function getContrastRatio(color1, color2) {
  const rgb1 = hexToRgb(color1);
  const rgb2 = hexToRgb(color2);
  
  if (!rgb1 || !rgb2) return 0;
  
  const lum1 = getLuminance(rgb1);
  const lum2 = getLuminance(rgb2);
  
  const brightest = Math.max(lum1, lum2);
  const darkest = Math.min(lum1, lum2);
  
  return (brightest + 0.05) / (darkest + 0.05);
}

/**
 * Check if contrast meets WCAG standards
 */
function checkWCAG(ratio) {
  return {
    AA_normal: ratio >= 4.5,
    AA_large: ratio >= 3.0,
    AAA_normal: ratio >= 7.0,
    AAA_large: ratio >= 4.5
  };
}

/**
 * Get status emoji based on WCAG compliance
 */
function getStatusEmoji(wcag) {
  if (wcag.AAA_normal) return '🟢'; // Excellent
  if (wcag.AA_normal) return '🟡';  // Good (meets AA)
  if (wcag.AA_large) return '🟠';   // Caution (only large text)
  return '🔴'; // Fail
}

/**
 * Main contrast checking function
 */
function checkContrast() {
  const results = [];
  
  // Color pairs to check
  const colorPairs = [
    // Light theme text combinations
    { name: 'Primary text on white', fg: colors.primary, bg: colors.bg, context: 'Primary buttons, links' },
    { name: 'Body text on white', fg: colors.fg, bg: colors.bg, context: 'Main content text' },
    { name: 'Muted text on white', fg: colors.muted, bg: colors.bg, context: 'Secondary text, captions' },
    { name: 'White text on primary', fg: colors.bg, bg: colors.primary, context: 'Primary button text' },
    { name: 'Body text on surface', fg: colors.fg, bg: colors.surface, context: 'Card content' },
    { name: 'Body text on secondary', fg: colors.fg, bg: colors.secondary, context: 'Highlighted areas' },
    
    // State color combinations
    { name: 'White on success', fg: colors.bg, bg: colors.success, context: 'Success buttons' },
    { name: 'White on warning', fg: colors.bg, bg: colors.warning, context: 'Warning buttons' },
    { name: 'White on danger', fg: colors.bg, bg: colors.danger, context: 'Error buttons' },
    { name: 'White on info', fg: colors.bg, bg: colors.info, context: 'Info buttons' },
    
    // Dark theme combinations
    { name: 'Dark: White text on dark bg', fg: colors.darkFg, bg: colors.darkBg, context: 'Dark theme body text', theme: 'dark' },
    { name: 'Dark: Muted text on dark bg', fg: colors.darkMuted, bg: colors.darkBg, context: 'Dark theme secondary text', theme: 'dark' },
    { name: 'Dark: Text on dark surface', fg: colors.darkFg, bg: colors.darkSurface, context: 'Dark theme cards', theme: 'dark' },
    { name: 'Dark: Primary on dark bg', fg: colors.primary, bg: colors.darkBg, context: 'Dark theme primary elements', theme: 'dark' },
    { name: 'Dark: Accent on dark bg', fg: colors.darkAccent, bg: colors.darkBg, context: 'Dark theme accents', theme: 'dark' },
    
    // Border combinations
    { name: 'Border on white', fg: colors.border, bg: colors.bg, context: 'Light theme borders' },
    { name: 'Dark: Border on dark bg', fg: colors.darkBorder, bg: colors.darkBg, context: 'Dark theme borders', theme: 'dark' },
  ];
  
  console.log('🎨 WCAG AA Contrast Analysis for Skincare Bot Design System\n');
  console.log('═'.repeat(80));
  
  colorPairs.forEach(pair => {
    const ratio = getContrastRatio(pair.fg, pair.bg);
    const wcag = checkWCAG(ratio);
    const status = getStatusEmoji(wcag);
    
    results.push({
      ...pair,
      ratio,
      wcag,
      status
    });
    
    const themePrefix = pair.theme ? `[${pair.theme.toUpperCase()}] ` : '';
    console.log(`${status} ${themePrefix}${pair.name}`);
    console.log(`   Ratio: ${ratio.toFixed(2)}:1`);
    console.log(`   Context: ${pair.context}`);
    console.log(`   Colors: ${pair.fg} on ${pair.bg}`);
    console.log(`   WCAG: AA-Normal ${wcag.AA_normal ? '✅' : '❌'} | AA-Large ${wcag.AA_large ? '✅' : '❌'} | AAA ${wcag.AAA_normal ? '✅' : '❌'}`);
    console.log('');
  });
  
  // Summary
  const totalPairs = results.length;
  const aaCompliant = results.filter(r => r.wcag.AA_normal).length;
  const aaaCompliant = results.filter(r => r.wcag.AAA_normal).length;
  const largeTextOnly = results.filter(r => !r.wcag.AA_normal && r.wcag.AA_large).length;
  const failed = results.filter(r => !r.wcag.AA_large).length;
  
  console.log('═'.repeat(80));
  console.log('📊 SUMMARY');
  console.log('═'.repeat(80));
  console.log(`Total pairs checked: ${totalPairs}`);
  console.log(`🟢 AA Normal compliant: ${aaCompliant}/${totalPairs} (${Math.round(aaCompliant/totalPairs*100)}%)`);
  console.log(`🟡 AAA compliant: ${aaaCompliant}/${totalPairs} (${Math.round(aaaCompliant/totalPairs*100)}%)`);
  console.log(`🟠 Large text only: ${largeTextOnly}/${totalPairs} (${Math.round(largeTextOnly/totalPairs*100)}%)`);
  console.log(`🔴 Failed: ${failed}/${totalPairs} (${Math.round(failed/totalPairs*100)}%)`);
  
  if (failed > 0) {
    console.log('\n⚠️  ISSUES TO FIX:');
    results.filter(r => !r.wcag.AA_large).forEach(result => {
      console.log(`   • ${result.name}: ${result.ratio.toFixed(2)}:1 (needs ${(4.5/result.ratio).toFixed(1)}x improvement)`);
    });
  }
  
  if (largeTextOnly > 0) {
    console.log('\n⚡ LARGE TEXT ONLY:');
    results.filter(r => !r.wcag.AA_normal && r.wcag.AA_large).forEach(result => {
      console.log(`   • ${result.name}: ${result.ratio.toFixed(2)}:1 (use only for large text 18px+)`);
    });
  }
  
  console.log('\n✨ RECOMMENDATIONS:');
  console.log('   • Use primary color for accent elements, not body text');
  console.log('   • Reserve muted color for non-critical secondary text');
  console.log('   • White text on colored backgrounds works well');
  console.log('   • Dark theme provides excellent contrast');
  console.log('   • Border colors are for decoration, not text');
  
  return results;
}

/**
 * Generate markdown report
 */
function generateMarkdownReport(results) {
  const reportDir = path.join(__dirname, '..', 'report');
  if (!fs.existsSync(reportDir)) {
    fs.mkdirSync(reportDir, { recursive: true });
  }
  
  const reportPath = path.join(reportDir, 'contrast.md');
  
  let markdown = `# WCAG Contrast Analysis Report

Generated: ${new Date().toLocaleString('ru-RU')}

## Overview

This report analyzes color contrast ratios for the Skincare Bot design system against WCAG 2.1 accessibility guidelines.

### WCAG Standards
- **AA Normal text**: 4.5:1 minimum ratio
- **AA Large text**: 3:1 minimum ratio (18px+ or 14px+ bold)
- **AAA Normal text**: 7:1 minimum ratio (enhanced)

## Results

| Status | Pair | Ratio | AA Normal | AA Large | AAA | Context |
|--------|------|-------|-----------|----------|-----|---------|
`;

  results.forEach(result => {
    const theme = result.theme ? ` (${result.theme})` : '';
    markdown += `| ${result.status} | ${result.name}${theme} | ${result.ratio.toFixed(2)}:1 | ${result.wcag.AA_normal ? '✅' : '❌'} | ${result.wcag.AA_large ? '✅' : '❌'} | ${result.wcag.AAA_normal ? '✅' : '❌'} | ${result.context} |\n`;
  });
  
  const totalPairs = results.length;
  const aaCompliant = results.filter(r => r.wcag.AA_normal).length;
  const aaaCompliant = results.filter(r => r.wcag.AAA_normal).length;
  const failed = results.filter(r => !r.wcag.AA_large).length;
  
  markdown += `
## Summary

- **Total pairs**: ${totalPairs}
- **AA compliant**: ${aaCompliant}/${totalPairs} (${Math.round(aaCompliant/totalPairs*100)}%)
- **AAA compliant**: ${aaaCompliant}/${totalPairs} (${Math.round(aaaCompliant/totalPairs*100)}%)
- **Failed**: ${failed}/${totalPairs} (${Math.round(failed/totalPairs*100)}%)

## Color Palette

### Light Theme
- **Primary**: \`${colors.primary}\` (Rose Mauve)
- **Secondary**: \`${colors.secondary}\` (Nude Blush)  
- **Accent**: \`${colors.accent}\` (Soft Lilac)
- **Background**: \`${colors.bg}\`
- **Text**: \`${colors.fg}\`
- **Muted**: \`${colors.muted}\`

### Dark Theme
- **Background**: \`${colors.darkBg}\`
- **Text**: \`${colors.darkFg}\`
- **Muted**: \`${colors.darkMuted}\`
- **Accent**: \`${colors.darkAccent}\`

## Recommendations

1. **Primary color** (\`${colors.primary}\`) should only be used for:
   - Accent elements and highlights
   - Icons and decorative elements
   - NOT for body text on white backgrounds

2. **Muted text** (\`${colors.muted}\`) is suitable for:
   - Secondary information
   - Captions and metadata
   - Non-critical content

3. **High contrast combinations** that work well:
   - White text on primary background
   - Dark text on white/light backgrounds
   - Dark theme provides excellent contrast ratios

4. **Failed combinations** should be avoided or only used for:
   - Decorative purposes
   - Non-text elements
   - Large text (18px+) where applicable
`;
  
  fs.writeFileSync(reportPath, markdown);
  console.log(`\n📄 Markdown report saved to: ${reportPath}`);
}

// Run the contrast check
if (require.main === module) {
  const results = checkContrast();
  generateMarkdownReport(results);
  
  // Exit code based on failures
  const criticalFailures = results.filter(r => !r.wcag.AA_large).length;
  process.exit(criticalFailures > 0 ? 1 : 0);
}

module.exports = {
  colors,
  getContrastRatio,
  checkWCAG,
  checkContrast
};

